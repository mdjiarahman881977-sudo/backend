import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import telebot
from telebot.types import LabeledPrice
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)
CORS(app)

# Settings
BOT_TOKEN = "8515902521:AAFexlhDlIyNe4Iga02tCiqZ0bAsfs1m88o"
bot = telebot.TeleBot(BOT_TOKEN)

# Firebase Init (Use your json file)
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://star-1a977-default-rtdb.firebaseio.com'
})

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = str(message.from_user.id)
    args = message.text.split()
    ref_by = args[1] if len(args) > 1 else None
    
    user_ref = db.reference(f'users/{user_id}')
    if not user_ref.get():
        user_ref.set({
            'username': message.from_user.username,
            'balance': 0,
            'referrals': 0,
            'referredBy': ref_by,
            'autoTap': False,
            'dailyAds': 0
        })
        if ref_by:
            db.reference(f'users/{ref_by}/referrals').transaction(lambda c: (c or 0) + 1)

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📱 Open Star Earn", url="https://t.me/starearnbdbot/startapp"))
    markup.add(telebot.types.InlineKeyboardButton("📢 Community", url="https://t.me/snowmanadventurecommunity"))
    
    welcome_msg = "🌟 Welcome to Star Earn!\n\nKnowledge Tip: Consistency is the key to success. Start earning stars today!"
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup)

@app.route('/create-invoice', methods=['POST'])
def create_invoice():
    data = request.json
    uid = data.get('userId')
    price = data.get('price') # 50 Stars
    
    try:
        link = bot.create_invoice_link(
            title="Auto Tap Activation",
            description="Lifetime Auto Tap functionality for Star Earn",
            payload=f"autotap_{uid}",
            provider_token="", # Stars
            currency="XTR",
            prices=[LabeledPrice("Stars", int(price))]
        )
        return jsonify({"link": link})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(query):
    bot.answer_pre_checkout_query(query.id, ok=True)

@bot.successful_payment_handler(func=lambda message: True)
def payment_success(message):
    payload = message.successful_payment.invoice_payload
    uid = payload.split('_')[1]
    db.reference(f'users/{uid}').update({'autoTap': True})
    bot.send_message(uid, "✅ Payment Success! Auto Tap Activated.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
