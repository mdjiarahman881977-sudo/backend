from flask import Flask, request, jsonify
from telegram import Bot, LabeledPrice
import telebot # pyTelegramBotAPI
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)
BOT_TOKEN = "8515902521:AAFexlhDlIyNe4Iga02tCiqZ0bAsfs1m88o"
bot = telebot.TeleBot(BOT_TOKEN)

# Firebase Init
cred = credentials.Certificate("firebase-adminsdk-json-path.json") # Download from Firebase Console
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://star-1a977-default-rtdb.firebaseio.com'
})

WELCOME_TEXT = """
🌟 Welcome to Star Earn! 🌟
Did you know? Learning one new thing every day improves brain health.
Explore our app to earn Stars and rewards!
"""

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    ref_by = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    # Save User to Firebase
    user_ref = db.reference(f'users/{user_id}')
    if not user_ref.get():
        user_ref.set({
            'username': message.from_user.username,
            'balance': 0,
            'referrals': 0,
            'referredBy': ref_by,
            'autoTapActive': False,
            'dailyAdsCount': 0
        })
        if ref_by:
            # Increment referral count for inviter
            db.reference(f'users/{ref_by}/referrals').transaction(lambda curr: (curr or 0) + 1)

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Open App", url="https://t.me/starearnbdbot/startapp"))
    markup.add(telebot.types.InlineKeyboardButton("Join Community", url="https://t.me/snowmanadventurecommunity"))
    
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=markup)

# API Endpoint for Star Invoice
@app.route('/create-invoice')
def create_invoice():
    user_id = request.args.get('userId')
    price = int(request.args.get('price'))
    
    invoice = bot.create_invoice_link(
        title="Auto Tap Bot",
        description="Activate lifetime auto-tapping!",
        payload=f"autotap_{user_id}",
        provider_token="", # Empty for Telegram Stars
        currency="XTR",
        prices=[LabeledPrice("Stars", price)]
    )
    return jsonify({"invoiceLink": invoice})

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.successful_payment_handler(func=lambda message: True)
def got_payment(message):
    user_id = message.from_user.id
    db.reference(f'users/{user_id}').update({'autoTapActive': True})
    bot.send_message(user_id, "✅ Auto Tap Activated!")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
