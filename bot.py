import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

# Fetching tokens from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADSGRAM_BLOCK_ID = os.getenv("ADSGRAM_BLOCK_ID")

bot = telebot.TeleBot(BOT_TOKEN)

# Dictionary to store user balances temporarily
user_balances = {}

# Handle /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0 # New user starts with 0 points
        
    welcome_text = (
        "👋 Welcome to our Crypto & Rewards Bot!\n\n"
        "Here you can check live Bitcoin (BTC) and Toncoin (TON) prices for free.\n"
        "Click the buttons below to check your balance, view prices, or earn reward points."
    )
    
    # Inline buttons layout
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("💰 My Balance", callback_data="check_balance"))
    markup.row(InlineKeyboardButton("📉 Check Crypto Prices", callback_data="show_prices"))
    markup.row(InlineKeyboardButton("💵 Withdraw Money", callback_data="withdraw"))
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# Handle button clicks
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
        
        ad_markup = InlineKeyboardMarkup()
        # Creating Adsgram direct ad redirect link
        ad_url = f"https://sad.adsgram.ai/redirect?bg={ADSGRAM_BLOCK_ID}&user={user_id}"
        
        ad_markup.row(InlineKeyboardButton("🎬 Watch Ad (15s)", url=ad_url))
        ad_markup.row(InlineKeyboardButton("✅ Done? View Prices Now", callback_data="fetch_real_price"))
        
        bot.send_message(chat_id, "⚠️ Please watch the 15-second video ad below to unlock live prices:", reply_markup=ad_markup)

    elif call.data == "fetch_real_price":
        bot.answer_callback_query(call.id)
        
        try:
            # Fetching live prices from CoinGecko Free API
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,the-open-network&vs_currencies=usd"
            response = requests.get(url).json()
            
            btc_price = response['bitcoin']['usd']
            ton_price = response['the-open-network']['usd']
            
            # Reward user with 5 points for watching the ad
            user_balances[user_id] = user_balances.get(user_id, 0) + 5
            
            price_message = (
                "🎯 Thank you for watching! +5 Points added to your account.\n\n"
                "📊 **Live Crypto Prices (USD):**\n"
                "🪙 Bitcoin (BTC): ${:,}\n"
                "💎 Toncoin (TON): ${:.2f}\n\n"
                "Type /start to check again or boost your balance!"
            ).format(btc_price, ton_price)
            
            bot.send_message(chat_id, price_message, parse_mode="Markdown")
            
        except Exception as e:
            bot.send_message(chat_id, "❌ Error updating prices. Please try again in a few moments.")

    elif call.data == "withdraw":
        bot.answer_callback_query(call.id)
        balance = user_balances.get(user_id, 0)
        
        if balance < 500: # Minimum withdraw limit
            bot.send_message(chat_id, f"❌ Insufficient balance! Minimum payout requires 500 points. You currently have {balance} points.")
        else:
            bot.send_message(chat_id, "✅ To claim your earnings, please send your Binance Pay ID to our Support Admin.")

# Run the bot
if __name__ == "__main__":
    print("Bot is successfully running...")
    bot.infinity_polling()
