import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ---- LLM / RAG ----
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = "llama-3.1-8b-instant"

    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    CHROMA_COLLECTION = "sop_knowledge_base"

    # ---- Integrations ----
    TODOIST_API_KEY = os.getenv("TODOIST_API_KEY")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    # ---- App ----
    LOG_FILE = "logs/app.log"

    @classmethod
    def validate(cls):
        missing = []

        if not cls.GROQ_API_KEY:
            missing.append("GROQ_API_KEY")

        if not cls.TODOIST_API_KEY:
            missing.append("TODOIST_API_KEY")

        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")

        if missing:
            raise ValueError(
                "Missing environment variables: " + ", ".join(missing)
            )