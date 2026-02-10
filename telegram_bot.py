import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from core.config import Config
from core.task_processor import TaskProcessor
from core.todoist_client import TodoistClient
from core.rag_engine import RAGEngine

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------- GLOBAL COMPONENTS ----------------
rag_engine = RAGEngine()
processor = TaskProcessor(rag_engine)
todoist_client = TodoistClient()

rag_loaded = False


# ---------------- UTIL ----------------
async def load_sop_if_needed():
    global rag_loaded
    if not rag_loaded:
        rag_engine.load_sop("data/sop_expenses.txt")
        rag_loaded = True


# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        " AI Task Assistant\n\n"
        "Commands:\n"
        "/task - Create a Todoist task\n"
        "/ask - Ask SOP question"
    )


async def task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "task"
    await update.message.reply_text(
        " Send your task request.\n\n"
        "Example:\n"
        "Buy MacBook for new developer, urgent"
    )


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "ask"
    await update.message.reply_text(
        " Send your SOP question.\n\n"
        "Example:\n"
        "Which card should I use for laptop purchases?"
    )


# ---------------- MESSAGE ROUTER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await load_sop_if_needed()

    text = update.message.text
    mode = context.user_data.get("mode")

    if mode == "task":
        await process_task(update, text)

    elif mode == "ask":
        await answer_question(update, text)

    else:
        await update.message.reply_text(
            "Please choose an action first:\n"
            "/task – Create task\n"
            "/ask – Ask SOP question"
        )


# ---------------- TASK FLOW ----------------
async def process_task(update: Update, request: str):
    await update.message.reply_text(" Parsing request...")

    parsed = processor.parse_request(request)
    logging.info(f"Parsed task: {parsed}")

    await update.message.reply_text(
        " Parsed Task\n"
        f"Title: {parsed['title']}\n"
        f"Category: {parsed['category']}\n"
        f"Priority: {parsed.get('priority')}\n"
        f"Deadline: {parsed.get('deadline_hint')}"
    )

    await update.message.reply_text(" Searching SOP...")
    sop_chunks = processor.rag_engine.query(
        f"{parsed['category']} {parsed['title']}",
        n_results=3
    )

    if sop_chunks:
        sop_preview = "\n\n".join(
            f"- {chunk[:150]}..." for chunk in sop_chunks
        )
        await update.message.reply_text(
            " Relevant SOP\n" + sop_preview
        )
    else:
        await update.message.reply_text(" No relevant SOP found.")

    await update.message.reply_text(" Generating enriched description...")
    enriched_desc = processor.enrich_with_sop(parsed)

    await update.message.reply_text(
        " Enriched Description\n"
        + enriched_desc
    )

    await update.message.reply_text(" Creating Todoist task...")

    try:
        task = todoist_client.create_task(parsed, enriched_desc)

        await update.message.reply_text(
            "Task Created Successfully!\n\n"
            f"Title: {task['content']}\n"
            f"Priority: P{task['priority']}\n"
            f"Todoist URL:\n{task['url']}"
        )

    except Exception as e:
        logging.exception("Todoist task creation failed")
        await update.message.reply_text(
            " Failed to create task.\n"
            f"Reason: {str(e)}"
        )


# ---------------- Q&A FLOW ----------------
async def answer_question(update: Update, question: str):
    await update.message.reply_text(" Searching SOP...")
    answer = processor.answer_question(question)

    await update.message.reply_text(
        " Answer\n"
        + answer
    )


# ---------------- ERROR HANDLER ----------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.exception("Unhandled Telegram error", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "An unexpected error occurred. Please try again."
        )


# ---------------- BOOTSTRAP ----------------
def run_bot():
    Config.validate()

    app = ApplicationBuilder() \
        .token(Config.TELEGRAM_BOT_TOKEN) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("task", task_command))
    app.add_handler(CommandHandler("ask", ask_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_error_handler(error_handler)

    logging.info("Telegram bot started")
    app.run_polling()

if __name__ == "__main__":
    run_bot()