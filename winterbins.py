# winterbins.py — copia texto, fotos sueltas y álbumes (fotos + videos)
import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("winterbins")

load_dotenv()
TOKEN = os.getenv("TOKEN")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))      # ej. -1001234567890
TOPIC_ID = int(os.getenv("TOPIC_ID"))                # ej. 1234 (topic id)

ALBUMS_KEY = "albums_by_group"

# --------- Guardar partes de álbum ---------
async def collect_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.media_group_id:
        return

    albums = context.chat_data.setdefault(ALBUMS_KEY, {})
    media_list = albums.setdefault(msg.media_group_id, [])

    first = len(media_list) == 0
    caption = msg.caption if first else None
    caption_entities = msg.caption_entities if first else None

    if msg.photo:
        media_list.append(
            InputMediaPhoto(
                media=msg.photo[-1].file_id,
                caption=caption,
                caption_entities=caption_entities,
            )
        )
    elif msg.video:
        media_list.append(
            InputMediaVideo(
                media=msg.video.file_id,
                caption=caption,
                caption_entities=caption_entities,
            )
        )

    log.debug(f"Album {msg.media_group_id} size={len(media_list)}")

# --------- /tested ---------
async def tested_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message:
        await update.message.reply_text("responde con /tested al bin que quieras aprobar y compartir.")
        return

    original = update.message.reply_to_message

    # --- Caso: Álbum ---
    if original.media_group_id:
        await asyncio.sleep(0.5)  # esperar un poco para juntar todas las partes

        albums = context.chat_data.get(ALBUMS_KEY, {})
        media_group = albums.get(original.media_group_id, [])

        if media_group:
            await context.bot.send_media_group(
                chat_id=GROUP_CHAT_ID,
                message_thread_id=TOPIC_ID,
                media=media_group,
            )
            await update.message.reply_text("bin enviado a winter priv. ¡muchas gracias por tu trabajo!")
        else:
            await update.message.reply_text("no pude capturar el álbum completo.")
        return

    # --- Caso: Foto suelta ---
    if original.photo:
        await context.bot.send_photo(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=TOPIC_ID,
            photo=original.photo[-1].file_id,
            caption=original.caption,
            caption_entities=original.caption_entities,
        )
        return

    # --- Caso: Video suelto ---
    if original.video:
        await context.bot.send_video(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=TOPIC_ID,
            video=original.video.file_id,
            caption=original.caption,
            caption_entities=original.caption_entities,
        )
        return

    # --- Caso: Texto ---
    if original.text:
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=TOPIC_ID,
            text=original.text,
            entities=original.entities,
        )
        return

    await update.message.reply_text("solo manejo texto, fotos, videos y álbumes.")

# --------- Main ---------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("tested", tested_command))
    app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, collect_album))

    log.info("🤖 bot listo.")
    app.run_polling()

if __name__ == "__main__":
    main()
