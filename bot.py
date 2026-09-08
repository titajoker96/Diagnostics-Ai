import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from duckduckgo_search import DDGS

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8612719931:AAG5aqhKDq9P-Zy5dnOHVxLdNICPtMi0C2U")

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

def ask_ai(user_text: str) -> str:
    """استعلام مباشر مجاني وسريع ومفتوح عبر محرك الذكاء الاصطناعي"""
    full_prompt = f"{SYSTEM_PROMPT}\n\nسؤال الفني: {user_text}"
    with DDGS() as ddgs:
        # استخدام موديل GPT-4o-mini المفتوح مجاناً
        response = ddgs.chat(keywords=full_prompt, model="gpt-4o-mini")
        return response

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً بك في مساعد تشخيص أعطال Kalmar & Cummins - by Mostafa M 🛠️\n\n"
        "أرسل رقم الكود (مثلاً: 6006 أو 7681) أو اكتب المشكلة مباشرة وسأعطيك أرقام الفيش والأطراف وخطوات القياس."
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        loop = asyncio.get_event_loop()
        reply_text = await loop.run_in_executor(None, ask_ai, user_query)
        await update.message.reply_text(reply_text)
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء معالجة الطلب: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("البوت يعمل الآن ومستعد للاستخدام بدون أي مفاتيح...")
    app.run_polling()
    
