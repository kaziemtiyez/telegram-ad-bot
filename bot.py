import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import requests
import threading
import http.server
import socketserver

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADSGRAM_BLOCK_ID = os.getenv("ADSGRAM_BLOCK_ID")

bot = telebot.TeleBot(BOT_TOKEN)
user_balances = {}

# --- Server for Hosting the index.html and Fake Port ---
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path.startswith('/?'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('index.html', 'rb') as file:
                self.wfile.write(file.read())
        else:
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

def run_server():
    port = int(os.environ.get("PORT", 10000))
    with socketserver.TCPServer(("", port), MyHandler) as httpd:
        print(f"Server running on port {port}")
        httpd.serve_forever()

threading.Thread(target=run_server, daemon=True).start()
# ----------------------------------------------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0
        
    welcome_text = (
        "👋 Welcome to our Crypto & Rewards Bot!\n\n"
        "Click the buttons below to check your balance or earn reward points."
    )
    
    # 🔗 রেন্ডারের নিজস্ব লিংক ব্যবহার করে ওয়েবভিউ ওপেন করা (টাইম আউট সমস্যা দূর করার জন্য)
    # আপনার রেন্ডার ডোমেইন: telegram-ad-bot-emm3.onrender.com
    ad_webapp_url = f"https://telegram-ad-bot-emm3.onrender.com/?blockId={ADSGRAM_BLOCK_ID}&tg_user_id={user_id}"
    
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📉 Check Crypto Prices", callback_data="show_prices"),
        InlineKeyboardButton("🎬 Watch Ad & Earn", web_app=WebAppInfo(url=ad_webapp_url))
    )
    markup.row(
        InlineKeyboardButton("💰 My Balance", callback_data="check_balance"),
        InlineKeyboardButton("💵 Withdraw Money", callback_data="withdraw")
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if call.data == "check_balance":
        balance = user_balances.get(user_id, 0)
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"💵 Your Current Balance: {balance} Points.")
        
    elif call.data == "show_prices":
        bot.answer_callback_query(call.id)
        ad_webapp_url = f"https://telegram-ad-bot-emm3.onrender.com/?blockId={ADSGRAM_BLOCK_ID}&tg_user_id={user_id}"
        
        ad_markup = InlineKeyboardMarkup()
        ad_markup.row(InlineKeyboardButton("🎬 Watch Ad (15s)", web_app=WebAppInfo(url=ad_webapp_url)))
        ad_markup.row(InlineKeyboardButton("✅ Done? View Prices Now", callback_data="fetch_real_price"))
        
        bot.send_message(chat_id, "⚠️ Please watch the 15-second video ad below to unlock live prices:", reply_markup=ad_markup)

    elif call.data == "fetch_real_price":
        bot.answer_callback_query(call.id)
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,the-open-network&vs_currencies=usd"
            response = requests.get(url).json()
            btc_price = response['bitcoin']['usd']
            ton_price = response['the-open-network']['usd']
            
            user_balances[user_id] = user_balances.get(user_id, 0) + 5
            
            price_message = (
                "🎯 Thank you for watching! +5 Points added.\n\n"
                "📊 **Live Crypto Prices (USD):**\n"
                "🪙 Bitcoin (BTC): ${:,}\n"
                "💎 Toncoin (TON): ${:.2f}"
            ).format(btc_price, ton_price)
            
            bot.send_message(chat_id, price_message, parse_mode="Markdown")
        except Exception as e:
            bot.send_message(chat_id, "❌ Error updating prices. Try again later.")

    elif call.data == "withdraw":
        bot.answer_callback_query(call.id)
        balance = user_balances.get(user_id, 0)
        if balance < 500:
            bot.send_message(chat_id, f"❌ Insufficient balance! Minimum payout 500 points. You have {balance}.")
        else:
            bot.send_message(chat_id, "✅ Send your Binance Pay ID to Admin.")

if __name__ == "__main__":
    print("Bot is successfully running...")
    bot.infinity_polling()
