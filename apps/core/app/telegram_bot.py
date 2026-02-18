import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.settings import settings


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


START_MESSAGE = "Helix - бот для сохранения и возврата напряжений"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    if update.message is not None:
        await update.message.reply_text(START_MESSAGE)


def run() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. Please add it to the environment."
        )

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_handler(CommandHandler("start", start))
    logger.info("Telegram bot started and waiting for commands")
    application.run_polling()


if __name__ == "__main__":
    run()
