import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.infra.db.session import SessionLocal
from app.infra.repos.tensions_repo import TensionsRepo
from app.settings import settings


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


START_MESSAGE = (
    "Helix - бот для сохранения и возврата напряжений\n\n"
    "Команды:\n"
    "/add - добавить напряжение\n"
    "/list - показать активные напряжения\n"
    "/cancel - отменить текущий диалог"
)

TITLE, CHARGE, VECTOR = range(3)

ALLOWED_VECTORS = {
    "unknown",
    "action",
    "message",
    "meeting",
    "focus_block",
    "decision",
    "research",
    "delegate",
    "drop",
}
MAX_MESSAGE_LEN = 3800


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    if update.message is not None:
        await update.message.reply_text(START_MESSAGE)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("new_tension", None)
    if update.message is not None:
        await update.message.reply_text("Ок, отменено.")
    return ConversationHandler.END


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    del context
    if update.message is not None:
        await update.message.reply_text("Введите заголовок напряжения (1..500 символов):")
    return TITLE


async def add_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return TITLE

    title = update.message.text.strip()
    if not title or len(title) > 500:
        await update.message.reply_text("Некорректный заголовок. Введите текст длиной 1..500.")
        return TITLE

    context.user_data["new_tension"] = {"title": title}
    await update.message.reply_text(
        "Укажите charge (0..5) или отправьте 'skip' для значения по умолчанию (3)."
    )
    return CHARGE


async def add_charge(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return CHARGE

    raw = update.message.text.strip().lower()
    charge = 3
    if raw not in {"skip", "пропуск"}:
        try:
            charge = int(raw)
        except ValueError:
            await update.message.reply_text("Charge должен быть числом от 0 до 5 или 'skip'.")
            return CHARGE
        if charge < 0 or charge > 5:
            await update.message.reply_text("Charge должен быть в диапазоне 0..5.")
            return CHARGE

    context.user_data.setdefault("new_tension", {})["charge"] = charge
    await update.message.reply_text(
        "Укажите vector "
        "(unknown/action/message/meeting/focus_block/decision/research/delegate/drop) "
        "или отправьте 'skip' для unknown."
    )
    return VECTOR


async def add_vector(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        return VECTOR

    raw = update.message.text.strip().lower()
    vector = "unknown"
    if raw not in {"skip", "пропуск"}:
        if raw not in ALLOWED_VECTORS:
            await update.message.reply_text("Некорректный vector. Введите одно из допустимых значений.")
            return VECTOR
        vector = raw

    data = context.user_data.get("new_tension") or {}
    title = data.get("title")
    charge = data.get("charge", 3)
    if not title:
        await update.message.reply_text("Не удалось прочитать заголовок. Начните заново через /add.")
        return ConversationHandler.END

    async with SessionLocal() as session:
        repo = TensionsRepo(session)
        t = await repo.create_tension(
            title=title,
            note=None,
            charge=charge,
            vector=vector,
            status="held",
            actor="user",
        )

    context.user_data.pop("new_tension", None)
    await update.message.reply_text(
        f"Сохранено: #{t.id} | {t.title}\nstatus={t.status}, charge={t.charge}, vector={t.vector}"
    )
    return ConversationHandler.END


def _format_tensions_chunks(lines: list[str]) -> list[str]:
    chunks: list[str] = []
    current = ""
    for line in lines:
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > MAX_MESSAGE_LEN:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


async def list_tensions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    if update.message is None:
        return

    async with SessionLocal() as session:
        repo = TensionsRepo(session)
        tensions = await repo.list_active(limit=50)

    if not tensions:
        await update.message.reply_text("Активных напряжений нет.")
        return

    lines = ["Активные напряжения:"]
    for t in tensions:
        lines.append(f"#{t.id} | {t.title} | status={t.status} | charge={t.charge} | vector={t.vector}")

    for chunk in _format_tensions_chunks(lines):
        await update.message.reply_text(chunk)


def run() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. Please add it to the environment."
        )

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_tensions))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("add", add_start)],
            states={
                TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_title)],
                CHARGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_charge)],
                VECTOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_vector)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
    )
    logger.info("Telegram bot started and waiting for commands")
    application.run_polling()


if __name__ == "__main__":
    run()
