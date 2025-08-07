import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

# ENV variables
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

thumb_path = os.path.join(os.getcwd(), "thumb.jpg")
current_task = {}

def clean_cache():
    for f in os.listdir():
        if f.endswith((".mp4", ".mkv", ".avi", ".mov", ".webm")):
            os.remove(f)
    if os.path.exists("video_input"):
        os.remove("video_input")

@app.on_message(filters.command("start") & filters.user(OWNER_ID))
async def start_cmd(client, message):
    await message.reply("✅ Bot ishga tushdi. Convert qilishga tayyor.")

@app.on_message(filters.command("help") & filters.user(OWNER_ID))
async def help_cmd(client, message):
    await message.reply(
        "/convert – Video yuboring\n"
        "/set_thumb – Poster yuboring\n"
        "/show_thumb – Poster ko‘rish\n"
        "/del_thumb – Poster o‘chirish\n"
        "/stop – Convertni to‘xtatish"
    )

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
        await message.reply_photo(photo=thumb_path, caption="📸 Saqlangan poster.")
    else:
        await message.reply("❌ Poster topilmadi.")

@app.on_message(filters.command("del_thumb") & filters.user(OWNER_ID))
async def delete_thumb(client, message):
    if os.path.exists(thumb_path):
        os.remove(thumb_path)
        await message.reply("🗑 Poster o‘chirildi.")
    else:
        await message.reply("❌ Hech qanday poster mavjud emas.")

@app.on_message(filters.command("convert") & filters.user(OWNER_ID))
async def convert_command(client, message):
    await message.reply("📥 Iltimos convert qilish uchun video yuboring...")

@app.on_message(filters.video & filters.user(OWNER_ID))
async def handle_video(client, message: Message):
    if current_task.get("busy", False):
        await message.reply("⏳ Iltimos, hozirgi convert tugaguncha kuting.")
        return

    current_task["busy"] = True
    msg = await message.reply("⬇️ Video yuklanmoqda...")

    input_path = "video_input"
    output_path = "xdkino.mp4"

    try:
        await message.download(file_name=input_path)
        await msg.edit("♻️ Convert qilinmoqda...")

        cmd = [
            "ffmpeg", "-i", input_path,
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        await process.communicate()

        if not os.path.exists(output_path):
            await msg.edit("❌ Convert muvaffaqiyatsiz yakunlandi.")
            current_task["busy"] = False
            clean_cache()
            return

        await msg.edit("📤 Video yuborilmoqda...")

        await client.send_video(
            chat_id=message.chat.id,
            video=output_path,
            caption="@xdkino",
            thumb=thumb_path if os.path.exists(thumb_path) else None,
            supports_streaming=True
        )
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ Xatolik: {str(e)}")
    finally:
        current_task["busy"] = False
        clean_cache()

@app.on_message(filters.command("stop") & filters.user(OWNER_ID))
async def stop_cmd(client, message):
    if current_task.get("busy", False):
        current_task["busy"] = False
        clean_cache()
        await message.reply("🛑 Convert to‘xtatildi va fayllar tozalandi.")
    else:
        await message.reply("ℹ️ Hozir hech qanday convert ketmayapti.")

app.run()
