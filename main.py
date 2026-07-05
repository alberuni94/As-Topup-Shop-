import telebot  # Capitalized 'Import' fixed to lowercase
from telebot import types
import sqlite3
import random
from datetime import datetime, date, timedelta

# =========================
# INITIAL SETTINGS
# =========================
TOKEN = "8553931591:AAFV05QUXPEWRhlLISOUvQljPz6e-qQJHlg"  # ⚠️ এখানে আপনার বটের টোকেন দিন
ADMIN_ID = 7146777474     # আপনার টেলিগ্রাম আইডি

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ডাটাবেজ কানেকশন ফাংশন
def get_db_connection():
    conn = sqlite3.connect("ultimate_v7_shop.db", check_same_thread=False)
    return conn

# =========================
# DATABASE SETUP
# =========================
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ইউজার টেবিল
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        balance REAL DEFAULT 0.0,
        total_spent REAL DEFAULT 0.0,
        last_bonus TEXT DEFAULT '',
        referred_by INTEGER DEFAULT 0,
        ref_count INTEGER DEFAULT 0
    )""")
    
    # ডিপোজিট টেবিল
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deposits (
        req_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        txid TEXT,
        status TEXT DEFAULT 'PENDING',
        date TEXT
    )""")
    
    # অর্ডার টেবিল
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY,
        user_id INTEGER,
        item_name TEXT,
        uid TEXT,
        price REAL,
        status TEXT DEFAULT 'PENDING',
        date TEXT
    )""")
    
    # ডাইনামিক মেইন বাটন/ক্যাটাগরি টেবিল
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        cat_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cat_name TEXT UNIQUE
    )""")
    
    # ক্যাটাগরি ভিত্তিক প্যাকেজ টেবিল
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS packages (
        pkg_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT, 
        name TEXT,
        price REAL DEFAULT 0.0
    )""")
    
    # মিউজিক টেবিল
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS music_tracks (
        track_id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT,
        title TEXT
    )""")
    
    # বটের গ্লোবাল সেটিংস টেবিল (চ্যানেল এবং ডিসকাউন্ট কলামসহ আপডেট)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bot_settings (
        bot_status TEXT DEFAULT 'ON',
        bkash_number TEXT DEFAULT '01825939645',
        admin_username TEXT DEFAULT 'AsAlberuni',
        ref_bonus REAL DEFAULT 5.0,
        target_channel TEXT DEFAULT '@YourChannelUsername', -- ⚠️ আপনার চ্যানেল ইউজারনেম এখানে দিন
        must_join_status TEXT DEFAULT 'OFF',
        discount_percentage REAL DEFAULT 0.0,
        discount_expiry TEXT DEFAULT ''
    )""")
    
    # ডিফল্ট সেটিংস ইনসার্ট
    cursor.execute("SELECT count(*) FROM bot_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""INSERT INTO bot_settings 
        (bot_status, bkash_number, admin_username, ref_bonus, target_channel, must_join_status, discount_percentage, discount_expiry) 
        VALUES ('ON', '01825939645', 'AsAlberuni', 5.0, '@YourChannelUsername', 'OFF', 0.0, '')""")
        
    # ডিফল্ট ডাইনামিক ক্যাটাগরি ইনসার্ট
    cursor.execute("SELECT count(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO categories (cat_name) VALUES ('diamond')")
        cursor.execute("INSERT INTO categories (cat_name) VALUES ('membership')")
        cursor.execute("INSERT INTO categories (cat_name) VALUES ('glory')")
        
        default_pkgs = [
            # DIAMOND PACKAGES
            ("diamond", "🔹 25 Diamond", 20.0),
            ("diamond", "🔹 50 Diamond", 35.0),
            ("diamond", "🔹 100 Diamond", 70.0),
            ("diamond", "🔹 115 Diamond", 79.0),
            ("diamond", "🔹 240 Diamond", 158.0),
            ("diamond", "🔹 355 Diamond", 237.0),
            ("diamond", "🔹 505 Diamond", 335.0),
            ("diamond", "🔹 610 Diamond", 400.0),
            ("diamond", "🔹 850 Diamond", 558.0),
            ("diamond", "🔹 1090 Diamond", 715.0),
            ("diamond", "🔹 1240 Diamond", 800.0),
            ("diamond", "🔹 1505 Diamond", 980.0),
            ("diamond", "🔹 1850 Diamond", 1200.0),
            ("diamond", "🔹 2090 Diamond", 1360.0),
            ("diamond", "🔹 2530 Diamond", 1610.0),
            ("diamond", "🔹 3770 Diamond", 2380.0),
            ("diamond", "🔹 5060 Diamond", 3200.0),
            ("diamond", "🔹 10120 Diamond", 6400.0),
            
            # MEMBERSHIP PACKAGES
            ("membership", "🔹 Weekly 1x", 158.0),
            ("membership", "🔹 Weekly 2x", 315.0),
            ("membership", "🔹 Weekly 3x", 475.0),
            ("membership", "🔹 Weekly Lite 1x", 40.0),
            ("membership", "🔹 Weekly Lite 2x", 80.0),
            ("membership", "🔹 Weekly Lite 3x", 120.0),
            ("membership", "🔹 Monthly 1x", 790.0),
            ("membership", "🔹 Monthly 2x", 1575.0),
            ("membership", "🔹 Monthly 3x", 2360.0),
            
            # GLORY BOT PACKAGES
            ("glory", "🤖 4ta Glory Bot", 200.0),
            ("glory", "🤖 8ta Glory Bot", 400.0),
            ("glory", "🤖 12ta Glory Bot", 600.0),
            ("glory", "🤖 16ta Glory Bot", 800.0),
            ("glory", "🤖 20ta Glory Bot", 1000.0)
        ]
        cursor.executemany("INSERT INTO packages (category, name, price) VALUES (?, ?, ?)", default_pkgs)
        
    conn.commit()
    conn.close()

init_db()

# =========================
# DYNAMIC GETTERS & SETTERS
# =========================
def get_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT bot_status, bkash_number, admin_username, ref_bonus, target_channel, must_join_status, discount_percentage, discount_expiry FROM bot_settings")
    row = cursor.fetchone()
    conn.close()
    return {
        "status": row[0], "bkash": row[1], "username": row[2], "ref_bonus": row[3],
        "channel": row[4], "must_join": row[5], "discount_pct": row[6], "discount_exp": row[7]
    }

def get_all_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT cat_name FROM categories")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_packages_by_cat(category):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pkg_id, name, price FROM packages WHERE category = ?", (category,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_user(user_id, name="User"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance, total_spent, last_bonus, referred_by, ref_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, name, balance, total_spent, last_bonus) VALUES (?, ?, 0.0, 0.0, '')", (user_id, name))
        conn.commit()
        row = (0.0, 0.0, '', 0, 0)
    conn.close()
    return {"balance": row[0], "total_spent": row[1], "last_bonus": row[2], "referred_by": row[3], "ref_count": row[4]}

# ==================================
# 📢 MUST JOIN CHECKER FUNCTION
# ==================================
def check_must_join(user_id):
    settings = get_settings()
    if settings['must_join'] == "ON" and user_id != ADMIN_ID:
        try:
            member = bot.get_chat_member(settings['channel'], user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

def send_must_join_message(chat_id):
    settings = get_settings()
    channel_url = f"https://t.me/{settings['channel'].replace('@', '')}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Join Our Channel", url=channel_url))
    markup.add(types.InlineKeyboardButton("🔄 Checked / Verified", callback_data="check_verified_join"))
    bot.send_message(chat_id, "⚠️ <b>আপনাকে অবশ্যই আমাদের অফিশিয়াল চ্যানেলে জয়েন থাকতে হবে!</b>\n\nনিচের বাটনে ক্লিক করে জয়েন করুন, তারপর ভেরিফাইড বাটনে চাপ দিন।", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_verified_join")
def check_verified_callback(call):
    user_id = call.from_user.id
    if check_must_join(user_id):
        bot.answer_callback_query(call.id, "✅ ভেরিফিকেশন সফল!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        text = f"🔥 <b>Welcome to AS TOPUP SHOP!</b> 🔥\n\nএখানে আপনি ওয়ালেটে ব্যালেন্স এড করে যেকোনো সময় ডায়মন্ড ও মেম্বারশিপ টপ-আপ করতে পারবেন।"
        bot.send_message(call.message.chat.id, text, reply_markup=main_menu(user_id))
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো চ্যানেলে জয়েন করেননি!", show_alert=True)

# ==================================
# ⏳ ACTIVE DISCOUNT PRICE CALCULATOR
# ==================================
def get_discounted_price(original_price):
    settings = get_settings()
    if settings['discount_pct'] > 0 and settings['discount_exp']:
        try:
            expiry = datetime.strptime(settings['discount_exp'], "%Y-%m-%d %H:%M:%S")
            if datetime.now() < expiry:
                discount_amount = original_price * (settings['discount_pct'] / 100.0)
                return max(0.0, original_price - discount_amount)
        except:
            pass
    return original_price

# =========================
# MAIN REPLIES KEYBOARD
# =========================
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 Buy Packages", "💳 Add Money")
    markup.row("🛒 Buy Glory Bot", "👤 My Profile")
    markup.row("🎁 Daily Bonus", "🤝 Invite & Earn")
    markup.row("📊 Order History", "🎵 Play Music")
    markup.row("📞 Support")
    if user_id == ADMIN_ID:
        markup.row("⚙️ Admin Panel")
    return markup

# =========================
# START COMMAND
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    settings = get_settings()
    
    if settings['status'] == "OFF" and user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "⚠️ <b>বট বর্তমানে মেইনটেইন্যান্স (Maintenance) মোডে আছে।</b>")
        return

    # মাস্ট জয়েন চেক
    if not check_must_join(user_id):
        send_must_join_message(message.chat.id)
        return

    args = message.text.split()
    referrer = 0
    if len(args) > 1:
        try:
            referrer = int(args[1])
            if referrer == user_id: referrer = 0
        except ValueError:
            referrer = 0

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute("INSERT INTO users (user_id, name, referred_by) VALUES (?, ?, ?)", (user_id, name, referrer))
        if referrer != 0:
            cursor.execute("UPDATE users SET balance = balance + ?, ref_count = ref_count + 1 WHERE user_id = ?", (settings['ref_bonus'], referrer))
            try:
                bot.send_message(referrer, f"🤝 <b>আপনার লিংকে নতুন ইউজার জয়েন করেছে!</b>\nবোনাস পেয়েছেন: <b>{settings['ref_bonus']} TK</b>")
            except: pass
        conn.commit()
    conn.close()

    text = f"🔥 <b>Welcome to AS TOPUP SHOP!</b> 🔥\n\nএখানে আপনি ওয়ালেটে ব্যালেন্স এড করে যেকোনো সময় ডায়মন্ড ও মেম্বারশিপ টপ-আপ করতে পারবেন।"
    bot.send_message(message.chat.id, text, reply_markup=main_menu(user_id))

# =========================
# 🎵 USER MUSIC SYSTEM
# =========================
@bot.message_handler(func=lambda m: m.text == "🎵 Play Music")
def play_music_user(message):
    if not check_must_join(message.from_user.id):
        send_must_join_message(message.chat.id)
        return
    send_track(message.chat.id, None)

def send_track(chat_id, message_id=None, current_track_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if current_track_id:
        cursor.execute("SELECT track_id, file_id, title FROM music_tracks WHERE track_id != ? ORDER BY RANDOM() LIMIT 1", (current_track_id,))
    else:
        cursor.execute("SELECT track_id, file_id, title FROM music_tracks ORDER BY RANDOM() LIMIT 1")
        
    track = cursor.fetchone()
    conn.close()
    
    if not track:
        msg_text = "🎵 <b>মিউজিক প্লেয়ার</b>\n\n❌ এখনো কোনো গান আপলোড করা হয়নি! এডমিন প্যানেল থেকে গান যোগ করুন।"
        if message_id:
            bot.edit_message_text(msg_text, chat_id, message_id)
        else:
            bot.send_message(chat_id, msg_text)
        return

    track_id, file_id, title = track[0], track[1], track[2]
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Next Music (গান পরিবর্তন)", callback_data=f"nextmus_{track_id}"))
    
    if message_id:
        try: bot.delete_message(chat_id, message_id)
        except: pass
        
    bot.send_audio(chat_id, file_id, caption=f"🎧 <b>Now Playing:</b> {title}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('nextmus_'))
def next_music_callback(call):
    bot.answer_callback_query(call.id, "🔄 গান পরিবর্তন করা হচ্ছে...")
    current_id = int(call.data.split('_')[1])
    send_track(call.message.chat.id, call.message.message_id, current_id)

# =========================
# 📋 BUY PACKAGES
# =========================
@bot.message_handler(func=lambda m: m.text == "📋 Buy Packages")
def buy_packages_menu(message):
    if not check_must_join(message.from_user.id):
        send_must_join_message(message.chat.id)
        return
    send_category_menu(message.chat.id, message.message_id, edit=False)

def send_category_menu(chat_id, message_id, edit=False):
    markup = types.InlineKeyboardMarkup(row_width=2)
    categories = get_all_categories()
    
    buttons = []
    for cat in categories:
        if cat != "glory":
            display_name = "💎 Diamond Top-Up" if cat == "diamond" else "🔹 Membership" if cat == "membership" else cat
            buttons.append(types.InlineKeyboardButton(display_name, callback_data=f"vcat_{cat}"))
            
    markup.add(*buttons)
    
    # ডিসকাউন্ট নোটিশ শো করার লজিক
    settings = get_settings()
    text = "📁 <b>অনুগ্রহ করে ক্যাটাগরি সিলেক্ট করুন:</b>"
    if settings['discount_pct'] > 0:
        text = f"⚡ <b>সীমিত সময়ের ফ্ল্যাশ ডিসকাউন্ট অফার চলমান!</b>\n🔥 প্রতিটি প্যাকেজে পাচ্ছেন <b>{settings['discount_pct']}%</b> ডিসকাউন্ট।\n\n" + text
        
    if edit:
        try: bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        except: pass
    else:
        bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_cats")
def back_to_categories(call):
    bot.answer_callback_query(call.id)
    send_category_menu(call.message.chat.id, call.message.message_id, edit=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith('vcat_'))
def show_category_packages(call):
    category = call.data.replace("vcat_", "")
    pkgs = get_packages_by_cat(category)
    
    if not pkgs:
        bot.answer_callback_query(call.id, "❌ এই ক্যাটাগরিতে কোনো প্যাকেজ নেই।", show_alert=True)
        return
        
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    buttons = []
    for p in pkgs:
        original_price = p[2]
        final_price = get_discounted_price(original_price)
        
        if final_price < original_price:
            btn_text = f"{p[1]} — <s>{int(original_price)}</s> {int(final_price)} TK 🔥"
        else:
            btn_text = f"{p[1]} — {int(original_price)} TK"
            
        buttons.append(types.InlineKeyboardButton(btn_text, callback_data=f"user_buy_{p[0]}"))
    
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("🔙 Back to Categories", callback_data="back_to_cats"))
    
    display_title = "💎 Diamond Top-Up" if category == "diamond" else "🔹 Membership" if category == "membership" else category
    title = f"📦 <b>{display_title} এর প্যাকেজসমূহ:</b>"
    try: bot.edit_message_text(title, call.message.chat.id, call.message.message_id, reply_markup=markup)
    except: pass

# =========================
# 🛒 BUY GLORY BOT
# =========================
@bot.message_handler(func=lambda m: m.text == "🛒 Buy Glory Bot")
def glory_bot_button(message):
    if not check_must_join(message.from_user.id):
        send_must_join_message(message.chat.id)
        return
        
    pkgs = get_packages_by_cat("glory")
    
    text = f"🤖 <b>GLORY BOT PRICE LIST</b> 🤖\n---\n"
    markup = types.InlineKeyboardMarkup(row_width=1)
    buttons = []
    
    if pkgs:
        for p in pkgs:
            original_price = p[2]
            final_price = get_discounted_price(original_price)
            if final_price < original_price:
                text += f"{p[1]} = <s>{int(original_price)}</s> <b>{int(final_price)} TK</b> 🔥\n"
            else:
                text += f"{p[1]} = <b>{int(original_price)} TK</b>\n"
            buttons.append(types.InlineKeyboardButton(f"{p[1]} — {int(final_price)} TK", callback_data=f"user_buy_{p[0]}"))
    else:
        text += "❌ কোনো প্যাকেজ সেট করা নেই।"
        
    text += "\n⚠️ <b>নিচের বাটনে ক্লিক করে অর্ডার করতে পারেন অথবা এডমিনের সাথে যোগাযোগ করুন।</b>"
    
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("💬 Telegram Admin", url=f"tg://user?id={ADMIN_ID}"),
               types.InlineKeyboardButton("🟢 WhatsApp Message", url="https://wa.me/8801825939645"))
    markup.add(types.InlineKeyboardButton("🔙 Close Menu", callback_data="close_glory"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "close_glory")
def close_glory_menu(call):
    bot.answer_callback_query(call.id)
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

# =========================
# ORDER PROCESS (BUYING)
# =========================
@bot.callback_query_handler(func=lambda call: call.data.startswith('user_buy_'))
def order_step1(call):
    pkg_id = int(call.data.split('_')[2])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, category FROM packages WHERE pkg_id = ?", (pkg_id,))
    pkg = cursor.fetchone()
    conn.close()
    
    if not pkg: 
        bot.answer_callback_query(call.id, "❌ প্যাকেজটি খুঁজে পাওয়া যায়নি!", show_alert=True)
        return
        
    pkg_name, original_price, category = pkg[0], pkg[1], pkg[2]
    pkg_price = get_discounted_price(original_price)
    
    user = get_user(call.message.chat.id)
    if user['balance'] < pkg_price:
        bot.answer_callback_query(call.id, f"❌ পর্যাপ্ত ব্যালেন্স নেই! মূল্য: {pkg_price} TK। দয়া করে Add Money করুন।", show_alert=True)
        return
        
    bot.answer_callback_query(call.id)
    
    if category == "glory":
        input_msg = "✍️ আপনার ফ্রি ফায়ার <b>Guild UID / Details</b> দিন:"
        uid_type = "Guild UID"
    else:
        input_msg = "✍️ আপনার ফ্রি ফায়ার <b>Player ID (UID)</b> দিন:"
        uid_type = "Player ID"
        
    msg = bot.send_message(call.message.chat.id, f"🛒 আইটেম: <b>{pkg_name}</b>\nমূল্য: {pkg_price} TK\n\n{input_msg}")
    bot.register_next_step_handler(msg, order_step2, pkg_name, pkg_price, uid_type)

def order_step2(message, pkg_name, pkg_price, uid_type):
    uid = message.text.strip()
    user_id = message.chat.id
    user = get_user(user_id)
    
    if user['balance'] < pkg_price:
        bot.send_message(user_id, "❌ পর্যাপ্ত ব্যালেন্স নেই।")
        return
        
    order_id = random.randint(100000, 999999)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance - ?, total_spent = total_spent + ? WHERE user_id = ?", (pkg_price, pkg_price, user_id))
    full_item_name = f"{pkg_name} ({uid_type})"
    cursor.execute("INSERT INTO orders (order_id, user_id, item_name, uid, price, date) VALUES (?, ?, ?, ?, ?, ?)", (order_id, user_id, full_item_name, uid, pkg_price, now))
    conn.commit()
    conn.close()
    
    bot.send_message(user_id, f"✅ <b>অর্ডার সফল হয়েছে!</b>\nOrder ID: #{order_id}")
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("✅ Deliver", callback_data=f"od_dl_{user_id}_{order_id}"), types.InlineKeyboardButton("❌ Refund", callback_data=f"od_rf_{user_id}_{order_id}_{pkg_price}"))
    bot.send_message(ADMIN_ID, f"🛍️ <b>NEW ORDER (# {order_id})</b>\nUser: <code>{user_id}</code>\nItem: {pkg_name}\n{uid_type}: <code>{uid}</code>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('od_'))
def handle_order_callback(call):
    if call.from_user.id != ADMIN_ID: return
    data = call.data.split('_')
    action, user_id, order_id = data[1], int(data[2]), int(data[3])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    if action == "dl":
        cursor.execute("UPDATE orders SET status = 'COMPLETED' WHERE order_id = ?", (order_id,))
        bot.send_message(user_id, f"🎉 <b>Order Completed!</b>\nআপনার #{order_id} অর্ডারটি ডেলিভার করা হয়েছে।")
        try: bot.edit_message_text(f"✅ Order #{order_id} Delivered.", call.message.chat.id, call.message.message_id)
        except: pass
    else:
        price = float(data[4])
        cursor.execute("UPDATE orders SET status = 'REFUNDED' WHERE order_id = ?", (order_id,))
        cursor.execute("UPDATE users SET balance = balance + ?, total_spent = total_spent - ? WHERE user_id = ?", (price, price, user_id))
        bot.send_message(user_id, f"❌ <b>Order Cancelled!</b>\nআপনার #{order_id} অর্ডারটি রিফান্ড করা হয়েছে।")
        try: bot.edit_message_text(f"❌ Order #{order_id} Cancelled.", call.message.chat.id, call.message.message_id)
        except: pass
    conn.commit()
    conn.close()

# =========================
# ADD MONEY & DEPOSIT SYSTEM
# =========================
@bot.message_handler(func=lambda m: m.text == "💳 Add Money")
def add_money(message):
    if not check_must_join(message.from_user.id):
        send_must_join_message(message.chat.id)
        return
        
    settings = get_settings()
    text = f"💳 <b>ADD MONEY (bKash)</b>\n\n📱 <b>bKash Personal Number:</b> <code>{settings['bkash']}</code>\n🔹 Method: <b>Send Money</b>\n\n⚠️ টাকা পাঠানোর পর নিচের বাটনে ক্লিক করে তথ্য সাবমিট করুন।"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💰 Submit Payment Details", callback_data="sub_dep"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "sub_dep")
def sub_dep(call):
    msg = bot.send_message(call.message.chat.id, "💵 <b>কত টাকা পাঠিয়েছেন তা সংখ্যায় লিখুন:</b>")
    bot.register_next_step_handler(msg, dep_amount)

def dep_amount(message):
    try:
        amount = float(message.text)
        if amount <= 0: raise ValueError
    except:
        bot.send_message(message.chat.id, "❌ ভুল ইনপুট।")
        return
    msg = bot.send_message(message.chat.id, "✍️ আপনার বিকাশের <b>TrxID (Transaction ID)</b> দিন:")
    bot.register_next_step_handler(msg, dep_final, amount)

def dep_final(message, amount):
    txid = message.text.strip()
    user_id = message.chat.id
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO deposits (user_id, amount, txid, date) VALUES (?, ?, ?, ?)", (user_id, amount, txid, now))
    req_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    bot.send_message(user_id, "✅ পেমেন্ট রিকোয়েস্ট জমা হয়েছে।")
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("✅ Accept", callback_data=f"dep_ap_{req_id}"), types.InlineKeyboardButton("❌ Reject", callback_data=f"dep_rj_{req_id}"))
    bot.send_message(ADMIN_ID, f"💰 <b>NEW DEPOSIT (# {req_id})</b>\nUser: <code>{user_id}</code>\nAmount: {amount} TK\nTxID: <code>{txid}</code>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dep_'))
def handle_deposit_callback(call):
    if call.from_user.id != ADMIN_ID: return
    data = call.data.split('_')
    action, req_id = data[1], int(data[2])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, amount, txid, status FROM deposits WHERE req_id = ?", (req_id,))
    dep = cursor.fetchone()
    
    if not dep:
        bot.answer_callback_query(call.id, "❌ এই ডিপোজিট রিকোয়েস্টটি পাওয়া যায়নি।", show_alert=True)
        conn.close()
        return
        
    user_id, amount, txid, current_status = dep[0], dep[1], dep[2], dep[3]
    if current_status != "PENDING":
        bot.answer_callback_query(call.id, f"⚠️ এই রিকোয়েস্টটি ইতিমধ্যেই {current_status} করা হয়েছে।", show_alert=True)
        conn.close()
        return

    if action == "ap":
        cursor.execute("UPDATE deposits SET status = 'APPROVED' WHERE req_id = ?", (req_id,))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        
        # 🤝 ৩ নম্বর সিস্টেম: রেফারেল ২০০ টাকা বা তার বেশি অ্যাড মানি বোনাস চেক
        cursor.execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,))
        ref_row = cursor.fetchone()
        if ref_row and ref_row[0] != 0 and amount >= 200.0:
            referrer_id = ref_row[0]
            cursor.execute("UPDATE users SET balance = balance + 15.0 WHERE user_id = ?", (referrer_id,))
            try:
                bot.send_message(referrer_id, f"🎁 <b>রেফারেল অ্যাড মানি বোনাস!</b>\nআপনার আমন্ত্রিত ইউজার <b>{amount} TK</b> অ্যাড মানি করায় আপনি পেয়েছেন অতিরিক্ত <b>15 TK</b> বোনাস!")
            except: pass
            
        conn.commit()
        bot.send_message(user_id, f"✅ <b>ডিপোজিট সফল হয়েছে!</b>\nআপনাকে <b>{amount} TK</b> যোগ করা হয়েছে।")
        try: bot.edit_message_text(f"✅ Deposit #{req_id} Approved!", call.message.chat.id, call.message.message_id)
        except: pass
    else:
        cursor.execute("UPDATE deposits SET status = 'REJECTED' WHERE req_id = ?", (req_id,))
        conn.commit()
        bot.send_message(user_id, f"❌ <b>ডিপোজিট বাতিল করা হয়েছে!</b>")
        try: bot.edit_message_text(f"❌ Deposit #{req_id} Rejected.", call.message.chat.id, call.message.message_id)
        except: pass
    conn.close()

# ========================================
# ⚙️ ADVANCED & DYNAMIC ADMIN PANEL
# ========================================
@bot.message_handler(func=lambda m: m.text == "⚙️ Admin Panel" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    settings = get_settings()
    text = f"⚙️ <b>ADVANCED ADMIN PANEL</b>\n\nBot Status: <b>{settings['status']}</b>\nbKash: <code>{settings['bkash']}</code>\n"
    text += f"📢 Must Join: <b>{settings['must_join']}</b> ({settings['channel']})\n"
    
    # ডিসকাউন্ট টাইম স্ট্যাটাস ক্যালকুলেশন
    if settings['discount_pct'] > 0 and settings['discount_exp']:
        try:
            exp = datetime.strptime(settings['discount_exp'], "%Y-%m-%d %H:%M:%S")
            if datetime.now() < exp:
                remaining = exp - datetime.now()
                text += f"⚡ Discount Active: <b>{settings['discount_pct']}%</b> ({int(remaining.total_seconds() / 60)} min left)"
            else:
                text += f"⚡ Discount Status: <b>Expired/OFF</b>"
        except: text += f"⚡ Discount Status: <b>OFF</b>"
    else:
        text += f"⚡ Discount Status: <b>OFF</b>"
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("➕ Add New Main Button (Category)", callback_data="adm_add_main_btn"),
        types.InlineKeyboardButton("❌ Remove Main Button (Category)", callback_data="adm_rem_main_btn"),
        types.InlineKeyboardButton("➕ Add Package inside Button", callback_data="adm_add_pkg_inside"),
        types.InlineKeyboardButton("✏️ Edit Package Price (দাম বসান)", callback_data="adm_edit_pkg_price"),
        types.InlineKeyboardButton("⚙️ Control Flash Discount (ডিসকাউন্ট সেট)", callback_data="adm_set_discount"),
        types.InlineKeyboardButton("⚙️ Setup Must Join Channel", callback_data="adm_setup_join"),
        types.InlineKeyboardButton("🎵 Manage Music (মিউজিক সেটআপ)", callback_data="adm_manage_music"),
        types.InlineKeyboardButton("👥 All Users Info", callback_data="adm_all_users_info"),
        types.InlineKeyboardButton("🔄 Toggle Bot Status", callback_data="adm_toggle"),
        types.InlineKeyboardButton("📱 Change bKash Number", callback_data="adm_change_bkash")
    )
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_'))
def admin_callbacks(call):
    if call.from_user.id != ADMIN_ID: return
    action = call.data
    
    if action == "adm_add_main_btn":
        msg = bot.send_message(ADMIN_ID, "✍️ <b>নতুন মেইন বাটন (Category) এর নাম লিখুন:</b>\n(যেমন: <code>PUBG UC</code>)")
        bot.register_next_step_handler(msg, save_new_category)
        
    elif action == "adm_rem_main_btn":
        categories = get_all_categories()
        if not categories:
            bot.send_message(ADMIN_ID, "❌ কোনো বাটন/ক্যাটাগরি অবশিষ্ট নেই!")
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        for cat in categories:
            markup.add(types.InlineKeyboardButton(f"🗑️ Delete {cat}", callback_data=f"delcat_{cat}"))
        bot.send_message(ADMIN_ID, "⚠️ <b>কোন মেইন বাটনটি চিরতরে রিমুভ করতে চান সিলেক্ট করুন:</b>\n(নোট: ডিলিট করলে এর ভেতরের সব প্যাকেজও ডিলিট হয়ে যাবে)", reply_markup=markup)
        
    elif action == "adm_add_pkg_inside":
        categories = get_all_categories()
        if not categories:
            bot.send_message(ADMIN_ID, "❌ কোনো ক্যাটাগরি নেই! আগে মেইন বাটন তৈরি করুন।")
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        for cat in categories:
            markup.add(types.InlineKeyboardButton(cat, callback_data=f"selcat_{cat}"))
        bot.send_message(ADMIN_ID, "📁 <b>কোন বাটনের ভেতর প্যাকেজ যোগ করবেন সিলেক্ট করুন:</b>", reply_markup=markup)
        
    elif action == "adm_edit_pkg_price":
        categories = get_all_categories()
        markup = types.InlineKeyboardMarkup(row_width=2)
        for cat in categories:
            display_name = "💎 Diamond Top-Up" if cat == "diamond" else "🔹 Membership" if cat == "membership" else "🤖 Glory Bot" if cat == "glory" else cat
            markup.add(types.InlineKeyboardButton(display_name, callback_data=f"editpricecat_{cat}"))
        bot.send_message(ADMIN_ID, "✏️ <b>কোন ক্যাটাগরির প্যাকেজের দাম পরিবর্তন বা সেট করতে চান?</b>", reply_markup=markup)

    elif action == "adm_set_discount":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎯 Start New Discount (1-5%)", callback_data="dsc_setup_pct"),
                   types.InlineKeyboardButton("❌ Stop Current Discount", callback_data="dsc_stop_now"))
        bot.send_message(ADMIN_ID, "⚡ <b>ফ্ল্যাশ ডিসকাউন্ট কন্ট্রোল সিস্টেম:</b>", reply_markup=markup)

    elif action == "adm_setup_join":
        settings = get_settings()
        markup = types.InlineKeyboardMarkup()
        status_text = "🔴 Turn OFF" if settings['must_join'] == "ON" else "🟢 Turn ON"
        markup.add(types.InlineKeyboardButton(status_text, callback_data="mj_toggle_status"),
                   types.InlineKeyboardButton("✏️ Change Channel Username", callback_data="mj_change_channel"))
        bot.send_message(ADMIN_ID, f"📢 <b>Must Join Channel Settings</b>\n\nStatus: {settings['must_join']}\nChannel: {settings['channel']}", reply_markup=markup)

    elif action == "adm_manage_music":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Add New MP3 Music", callback_data="mus_upload_step"),
                   types.InlineKeyboardButton("🗑️ Clear All Music List", callback_data="mus_clear_all"))
        bot.send_message(ADMIN_ID, "🎵 <b>মিউজিক কন্ট্রোল প্যানেল:</b>", reply_markup=markup)

    elif action == "adm_all_users_info":
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name, balance, total_spent FROM users")
        users = cursor.fetchall()
        conn.close()
        
        if not users:
            bot.send_message(ADMIN_ID, "👤 ডাটাবেজে কোনো ইউজার নেই।")
            return
            
        text = "👥 <b>ALL REGISTERED USERS INFO</b>\n----------------------------------\n"
        for u in users:
            text += f"🆔 <b>ID:</b> <code>{u[0]}</code>\n👤 <b>Name:</b> {u[1]}\n💰 <b>Balance:</b> {u[2]} TK\n🛒 <b>Spent:</b> {u[3]} TK\n----------------------------------\n"
            if len(text) > 3800:
                bot.send_message(ADMIN_ID, text)
                text = ""
        if text: bot.send_message(ADMIN_ID, text)

    elif action == "adm_toggle":
        current = get_settings()['status']
        new_status = "OFF" if current == "ON" else "ON"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE bot_settings SET bot_status = ?", (new_status,))
        conn.commit()
        conn.close()
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        admin_panel(call.message)
        
    elif action == "adm_change_bkash":
        msg = bot.send_message(ADMIN_ID, "✍️ নতুন বিকাশ নম্বরটি লিখুন:")
        bot.register_next_step_handler(msg, save_bkash)

# ==================================
# ⚡ DISCOUNT LOGICS (ADMIN OPERATIONS)
# ==================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('dsc_'))
def discount_callbacks(call):
    if call.from_user.id != ADMIN_ID: return
    if call.data == "dsc_setup_pct":
        msg = bot.send_message(ADMIN_ID, "✍️ <b>কত পারসেন্ট ডিসকাউন্ট দিতে চান লিখুন (সর্বোচ্চ ৫%):</b>\n(শুধুমাত্র ১ থেকে ৫ এর মধ্যে সংখ্যা লিখুন)")
        bot.register_next_step_handler(msg, dsc_setup_time)
    elif call.data == "dsc_stop_now":
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE bot_settings SET discount_percentage = 0.0, discount_expiry = ''")
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "❌ ডিসকাউন্ট সম্পূর্ণ বন্ধ করা হয়েছে।", show_alert=True)

def dsc_setup_time(message):
    try:
        pct = float(message.text.strip())
        if pct < 1.0 or pct > 5.0:
            bot.send_message(ADMIN_ID, "❌ দুঃখিত! আপনি ৫% এর বেশি ডিসকাউন্ট দিতে পারবেন না। আবার চেষ্টা করুন।")
            return
    except:
        bot.send_message(ADMIN_ID, "❌ ভুল ইনপুট। শুধুমাত্র সংখ্যা লিখুন।")
        return
        
    msg = bot.send_message(ADMIN_ID, "✍️ <b>কত মিনিটের জন্য ডিসকাউন্ট সেশনটি সচল রাখতে চান? (১ থেকে ৯০ মিনিট):</b>")
    bot.register_next_step_handler(msg, dsc_final_save, pct)

def dsc_final_save(message, pct):
    try:
        duration = int(message.text.strip())
        if duration < 1 or duration > 90:
            bot.send_message(ADMIN_ID, "❌ সময়সীমা অবশ্যই ১ থেকে ৯০ মিনিটের মধ্যে হতে হবে।")
            return
    except:
        bot.send_message(ADMIN_ID, "❌ ভুল ইনপুট।")
        return
        
    exp_time = (datetime.now() + timedelta(minutes=duration)).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bot_settings SET discount_percentage = ?, discount_expiry = ?", (pct, exp_time))
    conn.commit()
    conn.close()
    
    bot.send_message(ADMIN_ID, f"✅ <b>সফলভাবে ডিসকাউন্ট সেট হয়েছে!</b>\n🔥 ডিসকাউন্ট: {pct}%\n⏱️ সময়কাল: {duration} মিনিট\n⌛ শেষ হবে: {exp_time}")

# ==================================
# 📢 MUST JOIN LOGICS (ADMIN OPERATIONS)
# ==================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('mj_'))
def must_join_callbacks(call):
    if call.from_user.id != ADMIN_ID: return
    if call.data == "mj_toggle_status":
        current = get_settings()['must_join']
        new_status = "OFF" if current == "ON" else "ON"
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE bot_settings SET must_join_status = ?", (new_status,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, f"Must Join Status: {new_status}")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        admin_panel(call.message)
    elif call.data == "mj_change_channel":
        msg = bot.send_message(ADMIN_ID, "✍️ <b>আপনার টেলিগ্রাম চ্যানেলের Username দিন:</b>\n(অবশ্যই <code>@</code> সহ দিবেন, যেমন: @MyChannel)")
        bot.register_next_step_handler(msg, save_channel_username)

def save_channel_username(message):
    username = message.text.strip()
    if not username.startswith("@"):
        bot.send_message(ADMIN_ID, "❌ ভুল ফরম্যাট! ইউজারনেম অবশ্যই @ দিয়ে শুরু হতে হবে।")
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bot_settings SET target_channel = ?", (username,))
    conn.commit()
    conn.close()
    bot.send_message(ADMIN_ID, f"✅ সফলভাবে মাস্ট জয়েন চ্যানেল আপডেট হয়েছে: <b>{username}</b>\n⚠️ মনে রাখবেন, বটকে অবশ্যই উক্ত চ্যানেলে <b>Admin</b> বানাতে হবে!")

# =========================
# 🎵 MUSIC ADMIN OPERATIONS
# =========================
@bot.callback_query_handler(func=lambda call: call.data == "mus_upload_step")
def music_upload_trigger(call):
    msg = bot.send_message(ADMIN_ID, "✍️ <b>বটের কাছে যেকোনো অডিও/MP3 ফাইল ফরওয়ার্ড বা সেন্ড করুন:</b>")
    bot.register_next_step_handler(msg, save_audio_file_db)

def save_audio_file_db(message):
    if not message.audio:
        bot.send_message(ADMIN_ID, "❌ ভুল ইনপুট! দয়া করে একটি সঠিক .mp3 বা অডিও ফাইল সেন্ড করুন।")
        return
    
    file_id = message.audio.file_id
    title = message.audio.title if message.audio.title else f"Track-{random.randint(100,999)}"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO music_tracks (file_id, title) VALUES (?, ?)", (file_id, title))
    conn.commit()
    conn.close()
    
    bot.send_message(ADMIN_ID, f"✅ <b>'{title}'</b> গানটি সফলভাবে বটের আনলিমিটেড মিউজিক লিস্টে যোগ হয়েছে!")

@bot.callback_query_handler(func=lambda call: call.data == "mus_clear_all")
def clear_all_music(call):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM music_tracks")
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "🗑️ সব গান সফলভাবে ডাটাবেজ থেকে মুছে ফেলা হয়েছে।", show_alert=True)

# =========================
# OTHER ADMIN LOGICS
# =========================
@bot.callback_query_handler(func=lambda call: call.data.startswith('delcat_'))
def delete_category_completely(call):
    if call.from_user.id != ADMIN_ID: return
    cat_name = call.data.replace("delcat_", "")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE cat_name = ?", (cat_name,))
    cursor.execute("DELETE FROM packages WHERE category = ?", (cat_name,))
    conn.commit()
    conn.close()
    
    bot.answer_callback_query(call.id, f"✅ '{cat_name}' বাটনটি সফলভাবে রিমুভ করা হয়েছে!", show_alert=True)
    try: bot.delete_message(call.message.chat.id, call.message.message_id)
    except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith('editpricecat_'))
def process_edit_price_list(call):
    cat_name = call.data.replace("editpricecat_", "")
    pkgs = get_packages_by_cat(cat_name)
    
    if not pkgs:
        bot.send_message(ADMIN_ID, f"❌ '{cat_name}' ক্যাটাগরিতে কোনো প্যাকেজ নেই।")
        return
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    for p in pkgs:
        markup.add(types.InlineKeyboardButton(f"{p[1]} ({int(p[2])} TK)", callback_data=f"pro_edit_{p[0]}"))
    bot.send_message(ADMIN_ID, f"✏️ <b>{cat_name}</b> এর কোন প্যাকেজটির দাম পরিবর্তন করবেন?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('pro_edit_'))
def process_edit_price_step(call):
    pkg_id = int(call.data.split('_')[2])
    msg = bot.send_message(ADMIN_ID, "✍️ <b>নতুন প্রাইস (Price) কত টাকা হবে সংখ্যায় লিখুন:</b>")
    bot.register_next_step_handler(msg, save_edited_price, pkg_id)

def save_edited_price(message, pkg_id):
    try:
        new_price = float(message.text.strip())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE packages SET price = ? WHERE pkg_id = ?", (new_price, pkg_id))
        conn.commit()
        conn.close()
        bot.send_message(ADMIN_ID, "✅ <b>প্যাকেজের মূল্য সফলভাবে আপডেট করা হয়েছে!</b>")
    except ValueError:
        bot.send_message(ADMIN_ID, "❌ ভুল ইনপুট! প্রাইস শুধুমাত্র সংখ্যায় লিখুন।")

def save_new_category(message):
    cat_name = message.text.strip()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO categories (cat_name) VALUES (?)", (cat_name,))
        conn.commit()
        conn.close()
        bot.send_message(ADMIN_ID, f"✅ <b>'{cat_name}'</b> বাটনটি সফলভাবে শপ মেনুতে যোগ হয়েছে!")
    except sqlite3.IntegrityError:
        bot.send_message(ADMIN_ID, "❌ এই নামের বাটনটি ইতিমধ্যেই আছে।")

@bot.callback_query_handler(func=lambda call: call.data.startswith('selcat_'))
def select_category_for_pkg(call):
    cat_name = call.data.replace("selcat_", "")
    msg = bot.send_message(ADMIN_ID, f"✍️ <b>'{cat_name}' এর ভেতরে প্যাকেজের নাম লিখুন:</b>")
    bot.register_next_step_handler(msg, save_pkg_name_step, cat_name)

def save_pkg_name_step(message, cat_name):
    pkg_name = message.text.strip()
    msg = bot.send_message(ADMIN_ID, f"✍️ <b>'{pkg_name}' এর মূল্য (Price) কত টাকা হবে লিখুন:</b>")
    bot.register_next_step_handler(msg, save_pkg_final_step, cat_name, pkg_name)

def save_pkg_final_step(message, cat_name, pkg_name):
    try:
        price = float(message.text.strip())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO packages (category, name, price) VALUES (?, ?, ?)", (cat_name, pkg_name, price))
        conn.commit()
        conn.close()
        bot.send_message(ADMIN_ID, f"✅ প্যাকেজ সফলভাবে সেট হয়েছে!\n📁 বাটন: {cat_name}\n📦 প্যাকেজ: {pkg_name}\n💰 মূল্য: {price} TK")
    except ValueError:
        bot.send_message(ADMIN_ID, "❌ ভুল ইনপুট! প্রাইস শুধুমাত্র সংখ্যায় হতে হবে।")

def save_bkash(message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bot_settings SET bkash_number = ?", (message.text,))
    conn.commit()
    conn.close()
    bot.send_message(ADMIN_ID, "✅ বিকাশ নাম্বার পরিবর্তন সফল!")

# =========================
# OTHER SYSTEM HANDLERS
# =========================
@bot.message_handler(func=lambda m: m.text == "👤 My Profile")
def profile(message):
    if not check_must_join(message.from_user.id):
        send_must_join_message(message.chat.id)
        return
        
    user = get_user(message.from_user.id, message.from_user.first_name)
    text = f"👤 <b>YOUR ACCOUNT PROFILE</b>\n---\n🆔 <b>User ID:</b> <code>{message.from_user.id}</code>\n💰 <b>Current Balance:</b> {user['balance']} TK\n🛒 <b>Total Spent:</b> {user['total_spent']} TK"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "🎁 Daily Bonus")
def daily_bonus_button(message):
    if not check_must_join(message.from_user.id):
        send_must_join_message(message.chat.id)
        return
        
    user_id = message.chat.id
    today_str = date.today().strftime("%Y-%m-%d")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_bonus FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    
    if row and row[0] == today_str:
        bot.send_message(user_id, "❌ <b>আপনি আজ অলরেডি বোনাস নিয়ে নিয়েছেন!</b>")
        conn.close()
    else:
        cursor.execute("UPDATE users SET balance = balance + ?, last_bonus = ? WHERE user_id = ?", (2.0, today_str, user_id))
        conn.commit()
        conn.close()
        bot.send_message(user_id, f"🎁 <b>অভিনন্দন!</b> ২ টাকা বোনাস যোগ হয়েছে।")

@bot.message_handler(func=lambda m: m.text == "🤝 Invite & Earn")
def invite_earn(message):
    if not check_must_join(message.from_user.id):
        send_must_join_message(message.chat.id)
        return
        
    user_id = message.chat.id
    user_data = get_user(user_id)
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    bot.send_message(user_id, f"🤝 <b>রেফার লিঙ্ক:</b>\n<code>{ref_link}</code>\n\n👥 মোট রেফার: {user_data['ref_count']} জন\n🎯 আপনার রেফারেল লিংকের কেউ জয়েন করে ২০০ টাকা বা তার বেশি Add Money করলে আপনি সাথে সাথে পাবেন <b>১৫ টাকা</b> বোনাস!")

@bot.message_handler(func=lambda m: m.text == "📊 Order History")
def order_history_button(message):
    if not check_must_join(message.from_user.id):
        send_must_join_message(message.chat.id)
        return
        
    user_id = message.chat.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT order_id, item_name, price, status FROM orders WHERE user_id = ? ORDER BY date DESC LIMIT 5", (user_id,))
    orders = cursor.fetchall()
    conn.close()
    
    if not orders:
        bot.send_message(user_id, "📊 কোনো অর্ডার ইতিহাস নেই।")
        return
    text = "📊 <b>আপনার শেষ ৫টি অর্ডার:</b>\n\n"
    for o in orders:
        text += f"🆔 #{o[0]} | 📦 {o[1]} | 💰 {o[2]} TK | ⚡ {o[3]}\n"
    bot.send_message(user_id, text)

@bot.message_handler(func=lambda m: m.text == "📞 Support")
def support_button(message):
    if not check_must_join(message.from_user.id):
        send_must_join_message(message.chat.id)
        return
        
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Contact Admin", url=f"tg://user?id={ADMIN_ID}"))
    bot.send_message(message.chat.id, "📞 <b>আমাদের সাপোর্ট টিম:</b>\nনিচের বাটনে ক্লিক করে এডমিনের সাথে যোগাযোগ করুন।", reply_markup=markup)

# =========================
# BOT POLLING
# =========================
if __name__ == "__main__":
    print("Bot is running perfectly with advanced updates...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=5)
        except Exception as e:
            print(f"Error encountered: {e}. Restarting polling...")
