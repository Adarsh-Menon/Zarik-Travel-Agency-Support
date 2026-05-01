import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
LEADS_EXCEL_PATH = os.getenv("LEADS_EXCEL_PATH", "data/leads.xlsx")
MEMORY_DIR = os.getenv("MEMORY_DIR", "data/memory")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))
