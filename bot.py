import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

thumb_path = "thumb.jpg"
working_task = {}

def clean_cache():
    for f in os.listdir():
        if f.endswith((".mp4", ".mkv", ".avi", ".mov", ".webm")):
            os.remove(f)

@app.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start(client, message):
    await message.reply("✅ Bot ishga tushdi.")

@app.on_message(filters.command("help") & filters.user(OWNER_ID))
async def help_command(client, message):
    await message.reply("/convert - Video yuboring\n/set_thumb - Poster yuborish\n/show_thumb - Poster ko’rish\n/del_thumb - Poster o’chirish\n/stop - Convertni to’xtatish")

@app.on_message(filters.command("set_thumb") & filters.user(OWNER_ID))
async def set_thumb(client, message):
    await message.reply("📸 Iltimos rasm yuboring...")

@app.on_message(filters.photo & filters.user(OWNER_ID))
async def save_thumb(client, message: Message):
    await message.download(file_name=thumb_path)
    await message.reply("✅ Poster saqlandi.")

@app.on_message(filters.command("show_thumb") & filters.user(OWNER_ID))
async def show_thumb(client, message):
    if os.path.exists(thumb_path):
        await message.reply_photo(thumb_path, caption="📸 Saqlangan poster.")
    else:
        await message.reply("❌ Poster topilmadi.")

@app.on_message(filters.command("del_thumb") & filters.user(OWNER_ID))
async def delete_thumb(client, message):
    if os.path.exists(thumb_path):
        os.remove(thumb_path)
        await message.reply("🗑 Poster o‘chirildi.")
    else:
        await message.reply("❌ Poster mavjud emas.")

@app.on_message(filters.command("convert") & filters.user(OWNER_ID))
async def convert_command(client, message):
    await message.reply("📤 Iltimos video yuboring...")

@app.on_message(filters.video & filters.user(OWNER_ID))
async def handle_video(client, message: Message):
    video = message.video or message.document
    if not video:
        await message.reply("❌ Video topilmadi.")
        return

    file_name = video.file_name or "video_input.mp4"
    out_file = "xdkino.mp4"
    working_task[message.from_user.id] = True

    msg = await message.reply("⬇️ Yuklanmoqda...")
    await message.download(file_name=file_name)

    await msg.edit("♻️ Convert qilinmoqda...")

    cmd = [
        "ffmpeg", "-i", file_name,
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        out_file
    ]

    if os.path.exists(thumb_path):
        cmd += ["-vf", "scale=1280:-2"]

    process = await asyncio.create_subprocess_exec(*cmd)
    await process.wait()

    if not working_task.get(message.from_user.id, False):
        await msg.edit("🛑 Convert to‘xtatildi.")
        clean_cache()
        return

    await msg.edit("✅ Tayyor! Video yuborilmoqda...")

    try:
        await client.send_video(
            chat_id=message.chat.id,
            video=out_file,
            caption="@xdkino",
            thumb=thumb_path if os.path.exists(thumb_path) else None,
            supports_streaming=True
        )
    except Exception as e:
        await msg.edit(f"❌ Yuborishda xatolik: {str(e)}")
    finally:
        clean_cache()

@app.on_message(filters.command("stop") & filters.user(OWNER_ID))
async def stop_command(client, message):
    working_task[message.from_user.id] = False
    await message.reply("🛑 To‘xtatildi va fayllar o‘chirildi.")
    clean_cache()

app.run()
