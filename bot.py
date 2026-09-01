import logging
import os
import random
from collections import defaultdict

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
BOT_NAME = os.getenv("BOT_NAME", "يوهان")

if not TOKEN:
    raise RuntimeError(
        "لم يتم العثور على TELEGRAM_BOT_TOKEN. ضع التوكن في ملف .env أو متغيرات Render."
    )

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("yohan")

# ردود عامة متنوعة حتى لا يكرر البوت الجملة نفسها دائمًا.
GENERAL_REPLIES = [
    "صحا خويا، يوهان هنا حاضر وبالضحكة حاضر!",
    "آهلا بالناس الزينة، واش حوالكم؟",
    "ربي يدوم لمّة الخير والمحبة بيناتكم.",
    "هاك ضحكة مجانية من عند يوهان 😄",
    "كلامك على راسي، نورت المجموعة.",
    "يا سلام، المجموعة اليوم فيها الطاقة الزينة!",
    "ما تقلقش، يوهان راهو يسمع فيكم كامل.",
    "ربي يسهّل أموركم ويفرّح قلوبكم.",
    "واش هذا النشاط؟ خليتوني نبتسم وحدي!",
    "مرحبا بيك، الدار دارك والضحكة ضحكتك.",
]

KEYWORD_REPLIES = {
    # التحية والترحيب
    "سلام": "وعليكم السلام ورحمة الله تعالى وبركاته، مرحبا بيك يا خويا!",
    "السلام عليكم": "وعليكم السلام ورحمة الله تعالى وبركاته، نورت المجموعة!",
    "سلام عليكم": "وعليكم السلام ورحمة الله تعالى وبركاته، نورتنا!",
    "اهلا": "آهلا وسهلا، نورت يا زين!",
    "أهلا": "آهلا وسهلا، الدار دارك!",
    "مرحبا": "مرحبا بيك، نورت القعدة!",
    "صباح الخير": "صباح النور والسرور، ربي يجعل نهارك زين!",
    "مساء الخير": "مساء النور والهناء، ربي يفرّجها عليكم!",
    "ليلة سعيدة": "ليلة سعيدة خويا، ربي يهنيك!",
    "تصبح على خير": "وانت من أهلو، أحلام سعيدة يا زين.",
    # عبارات جزائرية يومية
    "صحا": "صحا صحا وليدي، هاك حبة حلوة 🍬",
    "يعطيك الصحة": "الله يسلمك ويحفظك، الصحة ليك ولعائلتك!",
    "يعطيك العافية": "الله يعافيك خويا، راك من الناس الملاح!",
    "واش راك": "راني فور ومتهني، وانتا واش حوالك؟",
    "واش حوالك": "الحمد لله لاباس، مادامكم حاضرين القعدة زينة!",
    "لاباس": "لاباس الحمد لله، ربي يدومها نعمة علينا كامل.",
    "راك مليح": "مليح بزاف، كي نشوفكم نولي فور!",
    "وين راك": "راني هنا، يوهان ما يغيبش على لمّة الخير!",
    "وينكم": "حاضرين يا جماعة، غير زيدو الهدرة الزينة!",
    "واش داير": "ندير في الجو ونحرس على الضحكة، وانتا؟",
    "واش درت": "درت قهوة افتراضية وقعدت نستنى فيكم!",
    "كيف حالك": "الحمد لله بخير، مادامكم بخير أنا بخير.",
    "الحمد لله": "دوم الحمد لله، ربي يزيدكم من فضلو.",
    "ان شاء الله": "إن شاء الله، ربي يجيب الخير ويفتحها عليكم.",
    "ربي يجيب الخير": "آمين يا رب، الخير قدّام والفرج قريب.",
    "ربي يحفظك": "آمين ويحفظك انت ثاني ويحفظ كامل الأحباب.",
    "ربي يسهلك": "آمين، ربي يسهّلها علينا وعليكم.",
    "ربي يفرج": "آمين يا رب، بعد العسر يجي اليسر.",
    "مبروك": "مبروك عليك، فرحتنا فرحتك!",
    "بالشفا": "الله يشافيك ويعافيك وترجع فور كي العادة.",
    "صح فطوركم": "صح فطوركم، تقبل الله صيامكم وصالح أعمالكم.",
    "رمضان كريم": "رمضان كريم، ربي يعيده علينا بالخير والبركة.",
    # الشكر والاعتذار
    "شكرا": "العفو خويا، ما كان حتى مزية بيناتنا.",
    "مرسي": "بلا مزية، هذا واجبنا يا خو!",
    "بارك الله فيك": "وفيك بارك الله، ربي يحفظك ويعطيك ما تتمنى.",
    "سمحلي": "مسامح خويا، القلوب صافية والضحكة باقية.",
    "معليش": "ماعليش، تصرا للناس كامل. المهم القلوب صافية.",
    # القهوة والأكل والجو
    "قهوة": "القهوة واجبة، شكون يزيدلنا قهوة مضبوطة؟",
    "كاش قهوة": "كاينة قهوة افتراضية سخونة، تفضل يا خويا!",
    "جوعان": "هاك كسرة وشوية حريرة، بالصحة والراحة!",
    "بالصحة": "الله يسلمك، بالصحة عليك وعلى أحبابك.",
    "شهية طيبة": "الله يهنيك، خليلي غير لقمة صغيرة!",
    "برد": "دير كاس أتاي وتغطى مليح، ما نحبوش يوهان يبرد!",
    "سخانة": "اشرب الماء بزاف وخفف الحركة، يوهان طبيب القعدة اليوم!",
    # المزاح والضحك
    "هههه": "ضحكتك وصلت حتى ليوهان، زيدنا منها!",
    "خخخ": "الضحكة الجزائرية بدات، شدوا رواحكم!",
    "نكتة": "واحد سأل يوهان: علاش ترد على كلشي؟ قالو: الخدمة خدمة والضحكة واجبة!",
    "نحبك": "نحبكم كامل يا جماعة الخير، بلا تفرقة!",
    "وحشتوني": "حتى نتوما وحشتوني، القعدة بلا بيكم ما تسواش.",
    "راك تهبل": "نهبل غير بالضحك والجو الزين، ما تخافش!",
    "مجنون": "مجنون بالضحكة برك، والعقل راهو في عطلة!",
    "اسكت": "حاضر نسكت ثانيتين... خلاص كملت الثانيتين!",
    "كذاب": "يوهان ما يكذبش، غير يزيد شوية بهارات للقعدة!",
    "نحب": "الحب والنية الصافية هما الزين كامل.",
    # الوداع والدعاء
    "تصبح": "تصبح على خير، وخلي البسمة دايمًا معاك.",
    "باي": "باي خويا، ربي يحفظك وترجع بالسلامة!",
    "سلام": "وعليكم السلام ورحمة الله تعالى وبركاته، ربي يحفظكم كامل.",
    "نشوفك": "نشوفوك على خير، ما تطولش الغيبة علينا.",
    "دعواتكم": "ربي يفتحها عليك ويحققلك ما تتمنى.",
}

# حفظ بسيط لعدد الرسائل في كل مجموعة أثناء تشغيل البوت.
message_counts = defaultdict(int)


def choose_reply(text: str) -> str:
    normalized = " ".join(text.lower().strip().split())
    for keyword, reply in KEYWORD_REPLIES.items():
        if keyword in normalized:
            return reply
    return random.choice(GENERAL_REPLIES)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"آهلا! أنا {BOT_NAME}، بوت جزائري مرح. نرد على كل رسالة نصية في المجموعة ونزيدها شوية ضحك."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "أنا نرد على كل رسالة نصية في المجموعة.\n"
        "الأوامر المتاحة:\n"
        "/start — التعريف بالبوت\n"
        "/help — عرض المساعدة\n"
        "/stats — عدد الرسائل التي شفتها المجموعة أثناء التشغيل"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    count = message_counts.get(chat.id, 0)
    await update.message.reply_text(f"يوهان شاف حتى الآن {count} رسالة في هذه المجموعة.")


async def reply_to_every_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat

    if not message or not message.text:
        return
    if chat and chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP, ChatType.PRIVATE}:
        return
    # لا نعالج رسائل البوتات لمنع حلقات الرد.
    if message.from_user and message.from_user.is_bot:
        return

    message_counts[chat.id] += 1
    await message.reply_text(choose_reply(message.text))


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled exception while processing update", exc_info=context.error)


def main() -> None:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_to_every_text))
    app.add_error_handler(error_handler)
    logger.info("يوهان يعمل الآن.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

