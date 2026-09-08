import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8612719931:AAG5aqhKDq9P-Zy5dnOHVxLdNICPtMi0C2U")

# قاعدة بيانات تشخيص أعطال Kalmar DRG 420-450 و Cummins QSM11
FAULTS_DB = {
    "6006": {
        "title": "عطل كود SPN 6006 - بلف هيدروليك الفرد/الضم (Telescope Extension/Retraction)",
        "control": "KAU D7911 (Node 7) أو KPU D7902 (Node 11)",
        "pins": "فيشة البلف الهيدروليكي Y6006 / طرف الإشارة Connectors X102 Pins 3 & 4",
        "measurements": "مقاومة الملف (Solenoid Coil): من 24 إلى 30 أوم. الجهد التشغيلي: 24V DC عند إعطاء أمر الحركة عبر الجويستيك.",
        "steps": (
            "1. ادخل على شاشة الكابينة في Diagnostic Menu وافحص حالة الإشارة من الجويستيك.\n"
            "2. افحص فيوز التغذية الخاص بالـ KAU في لوحة الفيوزات الرئيسية.\n"
            "3. قس بالآفوميتر مقاومة الملف على فيشة البلف (يجب ألا تكون شورت 0 أوم أو قاطعة Open Loop).\n"
            "4. افحص الضفيرة عند ركبة البوم (Boom Pivot) للتأكد من عدم وجود قطع أو تأريض للأسلاك."
        )
    },
    "7681": {
        "title": "عطل كود SPN 7681 - حساس قفل التويست لوك (Twistlocks Locked Sensor)",
        "control": "KAU D7911 (Node 7) - Spread Controller",
        "pins": "حساسات التقارب (Inductive Sensors) على أطراف الإسباردر B7681 / فيشة النود طرف إشارة Pin 12 و Pin 14",
        "measurements": "تغذية الحساس: 24V DC. إشارة الرجوع: 24V عند ملامسة الحاوية، و 0V في حالة الفتح.",
        "steps": (
            "1. تأكد من نظافة وجه الحساس الميكانيكي وخلوه من الشحم والرايش.\n"
            "2. افحص المسافة الهوائية (Air Gap) بين رأس الحساس وقرص القفل (من 2 إلى 4 مم).\n"
            "3. راقب لمبة البيان (LED) الموجودة على ظهر الحساس أثناء حركة التويست لوك.\n"
            "4. قس سلك الإشارة المتجه لنود الإسباردر KAU عند محاولة القفل."
        )
    },
    "6001": {
        "title": "عطل كود SPN 6001 - بلف رفع البوم الرئيسي (Main Boom Lift Valve)",
        "control": "KFU D7971 (Node 2) - Frame Front Controller",
        "pins": "بلف الرفع النسبي Y6001 / فيشة الكنترول KFU طرف إشارة PWM",
        "measurements": "المقاومة: 18 إلى 22 أوم. إشارة التحكم: PWM متغيرة من 0V حتى 24V حسب مشوار الجويستيك.",
        "steps": (
            "1. راجع شاشة الأعطال للتأكد من عدم وجود Stop Condition بسبب الحمل الزائد (Overload).\n"
            "2. افحص بلف الأمان الرئيسي وتأكد من وصول ضغط البايلوت (Pilot Pressure ~ 35 Bar).\n"
            "3. قس خروج إشارة الـ PWM من فيشة الـ KFU المتجهة للبلف."
        )
    },
    "qsm11": {
        "title": "أعطال محرك Cummins QSM11 - نظام الحقن وحساسات المحرك",
        "control": "Cummins ECM CM570 / CM870",
        "pins": "فيشة الحساسات 50-Pin Connector / حساس الكرنك والكاملات Engine Speed & Position",
        "measurements": "حساس الكرنك: مقاومة 1000 إلى 2000 أوم. ضغط الزيت والمانيفولد: تغذية 5V Reference ثابتة وسلك إشارة 0.5V إلى 4.5V.",
        "steps": (
            "1. افحص كود الفلاش من لمبة الـ Warning/Stop في لوحة العدادات.\n"
            "2. تأكد من ثبات جهد التغذية 24V القادم من بطاريات المعدة لمفتاح الكونتاكت و ECM.\n"
            "3. نظف حساس ضغط الهواء والحرارة (Tmap) على مانيفولد السحب.\n"
            "4. افحص فيشة الرشاشات المتصلة بجسم المحرك وتأكد من سلامة العزل ضد الزيت والحرارة."
        )
    }
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً بك يا فنان في مساعد تشخيص أعطال Kalmar & Cummins 🛠️\n\n"
        "أرسل رقم الكود فوراً (مثلاً: 6006 أو 7681 أو 6001 أو اكتب qsm11) "
        "وسأعطيك مباشرة: النود، أرقام الفيش، قيم القياس بالآفوميتر، وخطوات الفحص في الميدان."
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    
    # البحث عن الكود داخل الرسالة
    matched = None
    for code, data in FAULTS_DB.items():
        if code in text:
            matched = data
            break
            
    if matched:
        reply = (
            f"📋 **{matched['title']}**\n\n"
            f"🔹 **الكنترول والنود المسؤول:** {matched['control']}\n"
            f"🔹 **الفيش والأطراف (Pins):** {matched['pins']}\n"
            f"🔹 **قيم القياس بالآفوميتر:** {matched['measurements']}\n\n"
            f"🔧 **خطوات الفحص الميداني:**\n{matched['steps']}"
        )
    else:
        reply = (
            f"تم استلام طلبك بخصوص: '{text}'.\n\n"
            "لتشخيص دقيق وسريع، أرسل رقم الكود مباشرة مثل:\n"
            "• **6006** (بلف الفرد والضم)\n"
            "• **7681** (حساسات التويست لوك)\n"
            "• **6001** (بلف رفع البوم)\n"
            "• **qsm11** (حساسات ورشاشات محرك كومنز)\n\n"
            "وسأعطيك أرقام الفيش وخطوات الفحص فوراً."
        )
        
    await update.message.reply_text(reply)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("البوت يعمل محلياً بنجاح 100% بدون أي سيرفرات خارجية...")
    app.run_polling()
    
