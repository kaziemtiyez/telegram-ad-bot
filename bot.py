import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import requests
import threading
import http.server
import socketserver

BOT_TOKEN = os.getenv("BOT_TOKEN")
# Safely parsing the Block ID environment variable strictly as a clean string
raw_block_id = os.getenv("ADSGRAM_BLOCK_ID", "36654")
ADSGRAM_BLOCK_ID = str(raw_block_id).strip()

bot = telebot.TeleBot(BOT_TOKEN)
user_balances = {}

# --- Background Static HTML Web Server for Render ---
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path.startswith('/?'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('index.html', 'rb') as file:
                self.wfile.write(file.read())
        else:
            try:
                return http.server.SimpleHTTPRequestHandler.do_GET(self)
            except:
                self.send_response(404)
                self.end_headers()

def run_server():
    port = int(os.environ.get("PORT", 10000))
    with socketserver.TCPServer(("", port), MyHandler) as httpd:
        httpd.serve_forever()

# Start the web server thread to ensure 24/7 uptime regardless of mobile state
threading.Thread(target=run_server, daemon=True).start()
# ----------------------------------------------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0
        
    welcome_text = (
        "👋 Welcome to the Premium Crypto & Rewards Platform!\n\n"
        "Utilize the options below to track live market data and secure reward points."
    )
    
    # Passing clean string parameter to the verified WebApp URL
    ad_webapp_url = f"https://telegram-ad-bot-emm3.onrender.com/?blockId={ADSGRAM_BLOCK_ID}&uid={user_id}"
    
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
    ad_webapp_url = f"https://telegram-ad-bot-emm3.onrender.com/?blockId={ADSGRAM_BLOCK_ID}&uid={user_id}"
    
    if call.data == "check_balance":
        balance = user_balances.get(user_id, 0)
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, f"💵 Your Current Balance: {balance} Points.")
        
    elif call.data == "show_prices":
        bot.answer_callback_query(call.id)
        ad_markup = InlineKeyboardMarkup()
        ad_markup.row(InlineKeyboardButton("🎬 Watch Ad (15s)", web_app=WebAppInfo(url=ad_webapp_url)))
        ad_markup.row(InlineKeyboardButton("✅ Done? View Prices Now", callback_data="fetch_real_price"))
        bot.send_message(chat_id, "⚠️ Content Locked: Please complete the 15-second video ad below to access live market analytics:", reply_markup=ad_markup)

    elif call.data == "fetch_real_price":
        bot.answer_callback_query(call.id)
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,the-open-network&vs_currencies=usd"
            response = requests.get(url).json()
            btc_price = response['bitcoin']['usd']
            ton_price = response['the-open-network']['usd']
            
            user_balances[user_id] = user_balances.get(user_id, 0) + 5
            
            price_message = (
                "🎯 Verification Successful! +5 Points credited to your profile.\n\n"
                "📊 **Live Market Analytics (USD):**\n"
                "🪙 Bitcoin (BTC): ${:,}\n"
                "💎 Toncoin (TON): ${:.2f}"
            ).format(btc_price, ton_price)
            
            bot.send_message(chat_id, price_message, parse_mode="Markdown")
        except:
            bot.send_message(chat_id, "❌ Network Error: Unable to fetch real-time data rates. Please try again.")

    elif call.data == "withdraw":
        bot.answer_callback_query(call.id)
        balance = user_balances.get(user_id, 0)
        if balance < 500:
            bot.send_message(chat_id, f"❌ Transaction Declined: Minimum payout requirement is 500 points. Your balance: {balance}.")
        else:
            bot.send_message(chat_id, "✅ Request Approved: Please submit your Binance Pay ID directly to the Administrator.")

if __name__ == "__main__":
    print("Bot infrastructure successfully initiated...")
    bot.infinity_polling()
