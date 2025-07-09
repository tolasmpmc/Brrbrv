import telebot
from telebot import types
import mysql.connector
import random
import string

# === CONFIG ===
BOT_TOKEN = '7087152172:AAHCLied9YpQZuKWcD9Sfe4IwCKoh0_s6PA'
CHANNEL_ID = '-1002506809326'  # replace with your channel username (with @)

db = mysql.connector.connect(
    host="sql307.ezyro.com",
    user="ezyro_39421933",
    password="Tola009@@",
    database="ezyro_39421933_tgbot"
)
cursor = db.cursor(dictionary=True)
bot = telebot.TeleBot(BOT_TOKEN)

# === SESSIONS ===
admin_sessions = {}
user_states = {}

def generate_order_id():
    return "tola" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Deposit", "Buy")
    markup.add("Profile")
    return markup

# === /start ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name

    cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (telegram_id, name) VALUES (%s, %s)", (user_id, name))
        db.commit()

    bot.send_message(user_id, f"Welcome, {name}!", reply_markup=get_main_menu())

# === Deposit ===
@bot.message_handler(func=lambda m: m.text == "Deposit")
def deposit(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Back")
    bot.send_message(message.chat.id, "Hello!\nTo add balance, contact admin: @itslurytime", reply_markup=markup)

# === Back ===
@bot.message_handler(func=lambda m: m.text == "Back")
def go_back(message):
    bot.send_message(message.chat.id, "Main menu:", reply_markup=get_main_menu())

# === Profile ===
@bot.message_handler(func=lambda m: m.text == "Profile")
def profile(message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (user_id,))
    user = cursor.fetchone()

    msg = f"""👤 Name: {user['name']}
🆔 ID: {user_id}
💰 Balance: ${user['balance']}
🛒 Total Orders: {user['orders']}
💵 Total Spent: ${user['spent']}"""

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Back")
    bot.send_message(user_id, msg, reply_markup=markup)

# === Buy Step 1 ===
@bot.message_handler(func=lambda m: m.text == "Buy")
def buy_game(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Free Fire", "MLBB")
    markup.add("Back")
    user_states[message.chat.id] = {"step": "select_game"}
    bot.send_message(message.chat.id, "Select Game:", reply_markup=markup)

# === General Message Handler ===
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    chat_id = message.chat.id
    text = message.text
    state = user_states.get(chat_id)

    # === /admin Login ===
    if text == "/admin":
        user_states[chat_id] = {"step": "admin_user"}
        bot.send_message(chat_id, "Please send admin username:")
        return

    if state:
        step = state.get("step")

        # === Admin Login ===
        if step == "admin_user":
            user_states[chat_id]["username"] = text
            user_states[chat_id]["step"] = "admin_pass"
            bot.send_message(chat_id, "Please send password:")
            return

        elif step == "admin_pass":
            username = user_states[chat_id]["username"]
            password = text
            cursor.execute("SELECT * FROM admin WHERE username = %s AND password = %s", (username, password))
            admin = cursor.fetchone()
            if admin:
                admin_sessions[chat_id] = True
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.row("Add Balance", "Add Key")
                markup.add("Send Message")
                bot.send_message(chat_id, "Welcome, admin.", reply_markup=markup)
                user_states[chat_id] = {"step": "admin_menu"}
            else:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add("Back")
                bot.send_message(chat_id, "Incorrect admin account.", reply_markup=markup)
                user_states.pop(chat_id)
            return

        # === Admin Menu Buttons ===
        elif step == "admin_menu":
            if text == "Add Balance":
                user_states[chat_id] = {"step": "add_balance_user"}
                bot.send_message(chat_id, "Enter user ID:")
            elif text == "Add Key":
                user_states[chat_id] = {"step": "add_key_keys"}
                bot.send_message(chat_id, "Send key(s), comma-separated if multiple:")
            elif text == "Send Message":
                bot.send_message(chat_id, "Use /ann your message here")
            return

        # === Add Balance ===
        elif step == "add_balance_user":
            if not text.isdigit():
                bot.send_message(chat_id, "❌ Invalid ID.")
                return
            user_states[chat_id] = {"step": "add_balance_amount", "target_user": int(text)}
            bot.send_message(chat_id, "Enter amount:")
            return

        elif step == "add_balance_amount":
            try:
                amount = float(text)
                target_user = user_states[chat_id]["target_user"]
                cursor.execute("UPDATE users SET balance = balance + %s WHERE telegram_id = %s", (amount, target_user))
                db.commit()
                bot.send_message(chat_id, "✅ Deposit Successfully")
            except:
                bot.send_message(chat_id, "❌ Failed.")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("Add Balance", "Add Key")
            markup.add("Send Message")
            user_states[chat_id] = {"step": "admin_menu"}
            bot.send_message(chat_id, "Back to admin menu:", reply_markup=markup)
            return

        # === Add Key ===
        elif step == "add_key_keys":
            keys = [k.strip() for k in text.split(",") if k.strip()]
            if not keys:
                bot.send_message(chat_id, "❌ No keys detected.")
                return
            user_states[chat_id] = {"step": "add_key_game", "keys": keys}
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("Free Fire", "MLBB")
            bot.send_message(chat_id, "Select Game:", reply_markup=markup)
            return

        elif step == "add_key_game":
            if text not in ["Free Fire", "MLBB"]:
                bot.send_message(chat_id, "❌ Invalid game.")
                return
            user_states[chat_id]["game"] = text
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("1 Day", "1 Week", "1 Month")
            bot.send_message(chat_id, "Select Duration:", reply_markup=markup)
            user_states[chat_id]["step"] = "add_key_duration"
            return

        elif step == "add_key_duration":
            if text not in ["1 Day", "1 Week", "1 Month"]:
                bot.send_message(chat_id, "❌ Invalid duration.")
                return
            keys = user_states[chat_id]["keys"]
            game = user_states[chat_id]["game"]
            duration = text
            for k in keys:
                cursor.execute("INSERT INTO keys (key, game, duration) VALUES (%s, %s, %s)", (k, game, duration))
            db.commit()
            bot.send_message(chat_id, "✅ Key stock add successfully")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("Add Balance", "Add Key")
            markup.add("Send Message")
            user_states[chat_id] = {"step": "admin_menu"}
            bot.send_message(chat_id, "Back to admin menu:", reply_markup=markup)
            return

        # === Buy Step 2: Duration ===
        elif step == "select_game":
            if text not in ["Free Fire", "MLBB"]:
                return
            user_states[chat_id]["game"] = text
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("1 Day", "1 Week", "1 Month")
            markup.add("Back")
            user_states[chat_id]["step"] = "select_duration"
            bot.send_message(chat_id, "Select Duration:", reply_markup=markup)
            return

        elif step == "select_duration":
            if text not in ["1 Day", "1 Week", "1 Month"]:
                return
            game = user_states[chat_id]["game"]
            duration = text
            price = {"1 Day": 2, "1 Week": 5, "1 Month": 10}[duration]
            order_id = generate_order_id()
            user_states[chat_id] = {
                "step": "confirm",
                "game": game,
                "duration": duration,
                "price": price,
                "order_id": order_id
            }
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("Buy", "Cancel")
            bot.send_message(chat_id, f"""Game: {game}
Duration: {duration}
Price: ${price}
Order ID: {order_id}""", reply_markup=markup)
            return

        elif step == "confirm":
            if text == "Cancel":
                bot.send_message(chat_id, "Order cancelled.", reply_markup=get_main_menu())
                user_states.pop(chat_id)
                return
            if text == "Buy":
                data = user_states[chat_id]
                cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (chat_id,))
                user = cursor.fetchone()
                if user["balance"] < data["price"]:
                    bot.send_message(chat_id, "❌ Not enough balance.", reply_markup=get_main_menu())
                    user_states.pop(chat_id)
                    return
                # Check stock
                cursor.execute("SELECT * FROM keys WHERE game = %s AND duration = %s AND status = 'unused' LIMIT 1", (data["game"], data["duration"]))
                key = cursor.fetchone()
                if not key:
                    bot.send_message(chat_id, "❌ Key out of stock.", reply_markup=get_main_menu())
                    user_states.pop(chat_id)
                    return
                # Update
                cursor.execute("UPDATE users SET balance = balance - %s, orders = orders + 1, spent = spent + %s WHERE telegram_id = %s",
                               (data["price"], data["price"], chat_id))
                cursor.execute("UPDATE keys SET status = 'used', buyer_id = %s, order_id = %s WHERE id = %s",
                               (chat_id, data["order_id"], key["id"]))
                db.commit()
                msg = f"""✅ Your key has been successfully purchased

Your Key: {key['key']}
Duration: {data['duration']}
Game: {data['game']}
Order ID: {data['order_id']}

———————
Tola Store"""
                bot.send_message(chat_id, msg, reply_markup=get_main_menu())
                bot.send_message(CHANNEL_ID, msg)
                user_states.pop(chat_id)
                return

# === Broadcast ===
@bot.message_handler(commands=['ann'])
def broadcast(message):
    if message.chat.id not in admin_sessions:
        return
    msg = message.text.replace('/ann', '').strip()
    if not msg:
        bot.send_message(message.chat.id, "Use: /ann your message")
        return
    cursor.execute("SELECT telegram_id FROM users")
    for user in cursor.fetchall():
        try:
            bot.send_message(user["telegram_id"], msg)
        except:
            continue
    bot.send_message(message.chat.id, "✅ Message sent to all users.")

# === Start Bot ===
print("Bot is running...")
bot.infinity_polling()