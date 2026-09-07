import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from openai import OpenAI

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8612719931:AAG5aqhKDq9P-Zy5dnOHVxLdNICPtMi0C2U")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")

# تهيئة عميل OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

SYSTEM_PROMPT = """
أنت مهندس ومساعد فني لتشخيص أعطال معدات Kalmar Reachstacker DRG 420-450 ومحركات Cummins QSM11.
عندما يسألك الفني أو يرسل كود عطل (مثل SPN 6006 أو 7681 أو عطل في حركة معينة):
1. عرّف العطل واسم المكون والتأثير التشغيلي فوراً.
2. حدد الكنترول المسؤول ورقم النود (KCU D7901 Node 1, KFU D7971 Node 2, KAU D7911 Node 7, KPU D7902 Node 11).
3. حدد مسار الأسلاك والفيش وأرقام الأطراف (Connectors & Pins) بدقة.
4. اذكر قيم القياس بالآفوميتر (مقاومة أوم، جهد 24V أو 5V أو إشارة PWM).
5. رتب خطوات الفحص من الأسهل (شاشة التشخيص والفيوزات) إلى الأصعب (الضفيرة والبلوف).
اجعل الرد موجزاً، عملياً، وبنقاط واضحة تناسب القراءة على الموبايل في الميدان.
"""

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً بك في مساعد تشخيص أعطال Kalmar & Cummins - by Mostafa M 🛠️\n\n"
        "أرسل رقم الكود (مثلاً: 6006 أو 7681) أو اكتب المشكلة مباشرة "
        "(مثلاً: بلف الفرد مش شغال أو التويست لوك لا يقفل) وسأعطيك أرقام الفيش والأطراف وخطوات القياس."
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query}
            ],
            temperature=0.2,
        )
        response_text = response.choices[0].message.content
        await update.message.reply_text(response_text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء معالجة الطلب: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("البوت يعمل الآن بنجاح على OpenRouter...")
    app.run_polling()
    
