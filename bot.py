import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Initialize API Keys from environment variables (Critical for Railway deployment)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI Client
ai_client = OpenAI(api_key=OPENAI_API_KEY)

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("✍️ Blog Post Idea/Outline", callback_index="blog")],
        [InlineKeyboardButton("📢 Ad Copy (FB/Google)", callback_data="ad")],
        [InlineKeyboardButton("📧 Email Newsletter", callback_data="email")],
        [InlineKeyboardButton("📱 Social Media Post", callback_data="social")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Welcome to Jaspers21Bot! Your AI marketing assistant.\n"
        "What kind of content would you like to create today?", 
        reply_markup=reply_markup
    )

# Handle Menu Selection
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Save the selected mode to user data
    context.user_data['mode'] = query.data
    
    await query.edit_message_text(text=f"Great! Please reply with a short prompt or topic for your **{query.data.upper()}**.")

# Handle User Prompt & Generate Text
async def generate_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_mode = context.user_data.get('mode')
    user_prompt = update.message.text

    if not user_mode:
        await update.message.reply_text("Please select a content type first using /start.")
        return

    await update.message.reply_chat_action(action="typing")

    # System prompts to guide the AI persona based on selection
    system_prompts = {
        "blog": "You are an expert copywriter. Write a compelling blog post outline and introduction based on the user's topic.",
        "ad": "You are a direct-response marketer. Write high-converting ad copy (headline, primary text, CTA) for Facebook and Google Ads.",
        "email": "You are an email marketing specialist. Write an engaging email newsletter with an attention-grabbing subject line.",
        "social": "You are a social media manager. Write an engaging post with relevant hashtags and emojis suitable for Instagram and LinkedIn."
    }

    try:
        # Request generation from OpenAI
        response = ai_client.chat.completions.create(
            model="gpt-4o-mini", # Cost-effective and fast
            messages=[
                {"role": "system", "content": system_prompts.get(user_mode, "You are a helpful assistant.")},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        ai_reply = response.choices[0].message.content
        await update.message.reply_text(ai_reply, parse_mode="Markdown")
        
        # Clear mode so they can select again
        context.user_data['mode'] = None
        
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ Sorry, I ran into an error generating your content. Please try again later.")

def main():
    # Build the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_content))

    # Start the Bot (Railway will use polling unless you configure webhooks)
    application.run_polling()

if __name__ == '__main__':
    main()
