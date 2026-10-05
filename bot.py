from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InputMediaPhoto,
    InputMediaVideo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
import yt_dlp
import os
import glob
import asyncio

# ==================== تنظیمات جدید ====================
TOKEN = "8876599083:AAENDsfE2rfsEKMvigwQ5qlziHfkhk0BEmI"
BOT_USERNAME = "@FaraDownloader_Bot"

# آیدی کانال‌های اسپانسر
CHANNEL_1 = "@V2ray_company"
CHANNEL_2 = "@RemixEmpire2026"

CHANNEL_1_LINK = "https://t.me/V2ray_company"
CHANNEL_2_LINK = "https://t.me/RemixEmpire2026"

ADMIN_ID = "@My_admin1"


# ==================== کیبوردها ====================
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("📢 کانال‌های اسپانسر"), KeyboardButton("📞 ارتباط با ما")],
        [KeyboardButton("📥 راهنمای دانلود")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_join_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 آموزش و فروش کانفینگ", url=CHANNEL_1_LINK)],
        [InlineKeyboardButton("🎵 امپراطور ریمیکس", url=CHANNEL_2_LINK)],
        [InlineKeyboardButton("✅ عضویت را تایید می‌کنم", callback_data="check_join")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def is_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    for channel in [CHANNEL_1, CHANNEL_2]:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except Exception:
            return False
    return True


# ==================== دستورات ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = """🌟 سلام! به ربات **دانلودر اینستاگرام فرا** خوش اومدی 🤖

با من می‌تونی **ریلز، پست، عکس، ویدیو و استوری** اینستاگرام رو دانلود کنی ⚡

⚠️ برای استفاده حتماً عضو هر دو کانال اسپانسر شو:
۱. آموزش و فروش کانفینگ
۲. امپراطور ریمیکس

👇 اول عضو شو، بعد روی «عضویت را تایید می‌کنم» بزن"""

    await update.message.reply_text(welcome, reply_markup=get_join_keyboard(), disable_web_page_preview=True)
    await update.message.reply_text("منوی ربات فعال شد 👇", reply_markup=get_main_keyboard())


async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if await is_member(user_id, context):
        await query.edit_message_text("""✅ عضویت شما تایید شد! ممنون 🙏

حالا لینک اینستاگرام رو بفرست:""", disable_web_page_preview=True)
    else:
        await query.edit_message_text("""❌ هنوز عضو هر دو کانال نشدی!

لطفاً اول عضو شو:""", reply_markup=get_join_keyboard())


async def download_instagram(url, status_msg, update):
    ydl_opts = {
        "format": "best",
        "outtmpl": "temp_%(id)s_%(playlist_index)s.%(ext)s",
        "quiet": True,
        "noplaylist": False,
        "extract_flat": False,
        "writethumbnail": False,
        "socket_timeout": 30,
    }

    downloaded_files = []

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            if "entries" in info and info["entries"]:
                for entry in info["entries"]:
                    if entry:
                        filename = ydl.prepare_filename(entry)
                        if os.path.exists(filename):
                            downloaded_files.append(filename)
            else:
                filename = ydl.prepare_filename(info)
                if os.path.exists(filename):
                    downloaded_files.append(filename)

        if not downloaded_files:
            downloaded_files = [f for f in glob.glob("temp_*") if f.endswith((".mp4", ".webm", ".jpg", ".jpeg", ".png", ".webp"))]

        if not downloaded_files:
            await status_msg.edit_text("❌ فایلی پیدا نشد!")
            return

        downloaded_files = sorted(set(downloaded_files))
        caption = "✅ دانلود شد توسط @FaraDownloaderBot"

        if len(downloaded_files) == 1:
            file_path = downloaded_files[0]
            ext = os.path.splitext(file_path)[1].lower()
            with open(file_path, "rb") as f:
                if ext in (".jpg", ".jpeg", ".png", ".webp"):
                    await update.message.reply_photo(photo=f, caption=caption)
                else:
                    await update.message.reply_video(video=f, caption=caption)
            os.remove(file_path)
        else:
            media_group = []
            for i, file_path in enumerate(downloaded_files[:10]):
                ext = os.path.splitext(file_path)[1].lower()
                with open(file_path, "rb") as f:
                    if ext in (".jpg", ".jpeg", ".png", ".webp"):
                        media = InputMediaPhoto(media=f, caption=caption if i == 0 else None)
                    else:
                        media = InputMediaVideo(media=f, caption=caption if i == 0 else None)
                    media_group.append(media)
            await update.message.reply_media_group(media=media_group)

        await status_msg.delete()
        await update.message.reply_text("🎉 محتوا با موفقیت برات ارسال شد!", reply_markup=get_main_keyboard())

    except Exception as e:
        await status_msg.edit_text("❌ خطا در دانلود! لینک رو چک کن.")
        print(e)


# ==================== هندلر پیام‌ها ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message.text else ""
    user_id = update.effective_user.id

    if not text:
        return

    if text == "📞 ارتباط با ما":
        await update.message.reply_text(f"📞 پشتیبانی: {ADMIN_ID}", reply_markup=get_main_keyboard())
        return

    if text == "📢 کانال‌های اسپانسر":
        await update.message.reply_text("۱. آموزش و فروش کانفینگ\n۲. امپراطور ریمیکس", reply_markup=get_join_keyboard())
        return

    if text == "📥 راهنمای دانلود":
        await update.message.reply_text(
            "📥 **راهنمای استفاده:**\n\n"
            "۱. عضو هر دو کانال اسپانسر شو\n"
            "۲. لینک اینستاگرام رو بفرست\n\n"
            "✅ ریلز، پست، استوری، آلبوم\n"
            "📌 فقط لینک‌های عمومی کار می‌کنن.",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown",
        )
        return

    if not await is_member(user_id, context):
        await update.message.reply_text("⚠️ عضو هر دو کانال شو!", reply_markup=get_join_keyboard())
        return

    if "instagram.com" in text.lower() or "instagr.am" in text.lower():
        status_msg = await update.message.reply_text("⏳ در حال دانلود... لطفاً صبر کن!")
        await download_instagram(text, status_msg, update)
    else:
        await update.message.reply_text("📌 فقط لینک اینستاگرام بفرست!", reply_markup=get_main_keyboard())


# ==================== اجرای ربات ====================
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("ربات روشن شد!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
