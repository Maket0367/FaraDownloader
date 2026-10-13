from telegram import (
    Update,
    ReactionTypeEmoji,
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

# توکن از Environment Variable خونده می‌شه (برای Railway)
TOKEN = os.getenv("BOT_TOKEN")

# آیدی کانال‌های اسپانسر (با @)
CHANNEL_1 = "@V2ray_company"
CHANNEL_2 = "@RemixEmpire2026"

CHANNEL_1_LINK = "https://t.me/V2ray_company"
CHANNEL_2_LINK = "https://t.me/RemixEmpire2026"

ADMIN_ID = "@My_admin1"


# ==================== کیبوردها ====================

def get_main_keyboard():
    """کیبورد اصلی (منوی پایین صفحه - همون ۴ نقطه)"""
    keyboard = [
        [KeyboardButton("📢 کانال‌های اسپانسر"), KeyboardButton("📞 ارتباط با ما")],
        [KeyboardButton("📥 راهنمای دانلود")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_join_keyboard():
    """دکمه‌های عضویت (اینلاین)"""
    keyboard = [
        [InlineKeyboardButton("📢 آموزش و فروش کانفینگ", url=CHANNEL_1_LINK)],
        [InlineKeyboardButton("🎵 امپراطور ریمیکس", url=CHANNEL_2_LINK)],
        [InlineKeyboardButton("✅ عضویت را تایید می‌کنم", callback_data="check_join")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== چک عضویت ====================

async def is_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """چک می‌کنه کاربر عضو هر دو کانال هست یا نه"""
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
    # تلاش برای واکنش قلب به پیام /start؛ اگر تلگرام/نسخه API پشتیبانی نکند،
    # خطا گرفته می‌شود و روند عادی ربات ادامه پیدا می‌کند.
    try:
        if update.effective_chat and update.message:
            await context.bot.set_message_reaction(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
                reaction=[ReactionTypeEmoji("❤")],
            )
    except Exception as exc:
        print(f"Start reaction unavailable; continuing normally: {exc}")

    welcome = """🌟 سلام! به ربات **دانلودر اینستاگرام فرا** خوش اومدی 🤖

با من می‌تونی **ریلز، پست، عکس، ویدیو و استوری** اینستاگرام رو دانلود کنی ⚡

⚠️ برای استفاده حتماً عضو هر دو کانال اسپانسر شو:

۱. آموزش و فروش کانفینگ
۲. امپراطور ریمیکس

👇 اول عضو شو، بعد روی «عضویت را تایید می‌کنم» بزن"""

    await update.message.reply_text(
        welcome,
        reply_markup=get_join_keyboard(),
        disable_web_page_preview=True,
    )
    # کیبورد اصلی رو هم نشون بده
    await update.message.reply_text(
        "منوی ربات فعال شد 👇",
        reply_markup=get_main_keyboard(),
    )


async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """وقتی کاربر روی دکمه تایید عضویت می‌زنه"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if await is_member(user_id, context):
        success_text = """✅ عضویت شما تایید شد! ممنون 🙏

حالا لینک اینستاگرام رو بفرست تا برات دانلود کنم:

• ریلز
• پست (عکس و ویدیو)
• استوری
• آلبوم

📌 مثال:
https://www.instagram.com/reel/xxxxx"""

        await query.edit_message_text(success_text, disable_web_page_preview=True)
    else:
        not_joined = """❌ هنوز عضو هر دو کانال نشدی!

لطفاً اول عضو کانال‌های زیر شو، بعد دوباره روی دکمه تایید بزن:

۱. آموزش و فروش کانفینگ
۲. امپراطور ریمیکس"""

        await query.edit_message_text(
            not_joined,
            reply_markup=get_join_keyboard(),
            disable_web_page_preview=True,
        )


# ==================== دانلودر پیشرفته ====================

async def download_instagram(url: str, status_msg, update: Update):
    """دانلود محتوا از اینستاگرام (عکس، ویدیو، ریلز، استوری، آلبوم)"""
    ydl_opts = {
        "format": "best",
        "outtmpl": "temp_%(id)s_%(playlist_index)s.%(ext)s",
        "quiet": True,
        "noplaylist": False,  # برای آلبوم‌ها
        "extract_flat": False,
        "writethumbnail": False,
        "socket_timeout": 30,
    }

    downloaded_files = []

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # اگر چندتا فایل باشه (آلبوم)
            if "entries" in info and info["entries"]:
                for entry in info["entries"]:
                    if entry:
                        filename = ydl.prepare_filename(entry)
                        if os.path.exists(filename):
                            downloaded_files.append(filename)
                        else:
                            # پیدا کردن فایل‌های دانلود شده
                            base_id = entry.get("id", "")
                            for f in glob.glob(f"temp_{base_id}*"):
                                if f not in downloaded_files:
                                    downloaded_files.append(f)
            else:
                filename = ydl.prepare_filename(info)
                if os.path.exists(filename):
                    downloaded_files.append(filename)
                else:
                    for f in glob.glob("temp_*"):
                        if f.endswith((".mp4", ".webm", ".jpg", ".jpeg", ".png", ".webp")):
                            downloaded_files.append(f)

        if not downloaded_files:
            # آخرین تلاش: همه فایل‌های temp
            downloaded_files = [
                f for f in glob.glob("temp_*")
                if f.endswith((".mp4", ".webm", ".jpg", ".jpeg", ".png", ".webp"))
            ]

        if not downloaded_files:
            await status_msg.edit_text("❌ فایلی پیدا نشد!\nلینک رو چک کن یا کمی بعد دوباره امتحان کن.")
            return

        # مرتب‌سازی فایل‌ها
        downloaded_files = sorted(set(downloaded_files))

        caption = "✅ دانلود شد توسط @FaraYouTubeBot"

        # اگر فقط یک فایل باشه
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
            # چند فایل (آلبوم) → ارسال به صورت مدیا گروپ (حداکثر ۱۰ تا)
            media_group = []
            files_to_close = []

            for i, file_path in enumerate(downloaded_files[:10]):
                ext = os.path.splitext(file_path)[1].lower()
                f = open(file_path, "rb")
                files_to_close.append(f)

                if ext in (".jpg", ".jpeg", ".png", ".webp"):
                    media = InputMediaPhoto(media=f, caption=caption if i == 0 else None)
                else:
                    media = InputMediaVideo(media=f, caption=caption if i == 0 else None)
                media_group.append(media)

            await update.message.reply_media_group(media=media_group)

            # بستن و پاک کردن فایل‌ها
            for f in files_to_close:
                f.close()
            for file_path in downloaded_files:
                try:
                    os.remove(file_path)
                except Exception:
                    pass

        await status_msg.delete()
        await update.message.reply_text("🎉 محتوا با موفقیت برات ارسال شد!", reply_markup=get_main_keyboard())

    except Exception as e:
        # پاک کردن فایل‌های موقت در صورت خطا
        for f in glob.glob("temp_*"):
            try:
                os.remove(f)
            except Exception:
                pass

        error_msg = str(e).lower()
        if "login" in error_msg or "private" in error_msg or "cookies" in error_msg:
            await status_msg.edit_text(
                "❌ این محتوا خصوصی هست یا نیاز به لاگین داره.\n"
                "فقط لینک‌های عمومی کار می‌کنن."
            )
        else:
            await status_msg.edit_text(
                "❌ خطا در دانلود!\n\n"
                "• لینک رو چک کن\n"
                "• مطمئن شو عمومی باشه\n"
                "• چند دقیقه دیگه دوباره امتحان کن"
            )
        print(f"Download Error: {e}")


# ==================== هندلر پیام‌ها ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message.text else ""
    user_id = update.effective_user.id

    if not text:
        return

    # دکمه ارتباط با ما
    if text == "📞 ارتباط با ما":
        await update.message.reply_text(
            f"📞 برای ارتباط با پشتیبانی به این آیدی پیام بده:\n\n"
            f"👉 {ADMIN_ID}\n\n"
            f"سوالات، پیشنهادات و گزارش مشکل رو اینجا بفرست.",
            reply_markup=get_main_keyboard(),
        )
        return

    # دکمه کانال‌های اسپانسر
    if text == "📢 کانال‌های اسپانسر":
        await update.message.reply_text(
            "📢 برای استفاده از ربات باید عضو هر دو کانال باشی:\n\n"
            "۱. آموزش و فروش کانفینگ\n"
            "۲. امپراطور ریمیکس\n\n"
            "بعد از عضویت روی دکمه تایید بزن 👇",
            reply_markup=get_join_keyboard(),
        )
        return

    # دکمه راهنما
    if text == "📥 راهنمای دانلود":
        await update.message.reply_text(
            "📥 **راهنمای استفاده:**\n\n"
            "۱. عضو هر دو کانال اسپانسر شو\n"
            "۲. لینک اینستاگرام رو مستقیم بفرست\n\n"
            "✅ پشتیبانی از:\n"
            "• ریلز (Reels)\n"
            "• پست‌های عکس و ویدیو\n"
            "• استوری‌های عمومی\n"
            "• آلبوم‌ها (چند عکس/ویدیو)\n\n"
            "📌 فقط لینک‌های عمومی کار می‌کنن.",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown",
        )
        return

    # چک عضویت
    if not await is_member(user_id, context):
        await update.message.reply_text(
            "⚠️ برای استفاده از ربات باید عضو هر دو کانال اسپانسر باشی!\n\n"
            "اول عضو شو، بعد روی دکمه تایید عضویت بزن:",
            reply_markup=get_join_keyboard(),
        )
        return

    # دانلود لینک اینستاگرام
    if "instagram.com" in text.lower() or "instagr.am" in text.lower():
        status_msg = await update.message.reply_text("⏳ در حال دانلود... لطفاً صبر کن!")
        await download_instagram(text, status_msg, update)
    else:
        await update.message.reply_text(
            "📌 لطفاً فقط لینک اینستاگرام بفرست 😊\n\n"
            "از منوی پایین هم می‌تونی استفاده کنی.",
            reply_markup=get_main_keyboard(),
        )


# ==================== اجرای ربات ====================

def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN تنظیم نشده است. توکن را در بخش Variables/Secrets هاست تعریف کنید."
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join, pattern="^check_join$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("ربات دانلودر اینستاگرام فرا روشن شد...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
