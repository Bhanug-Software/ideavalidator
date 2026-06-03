from dotenv import load_dotenv
import os
from anthropic import Anthropic
from langgraph.checkpoint.memory import MemorySaver
import uuid

os.environ.setdefault("LANGSMITH_TRACING", "true")
load_dotenv()

# Validate required API keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
GMAIL_OAUTH_CREDENTIALS = os.getenv("GMAIL_OAUTH_CREDENTIALS", "app/credentials/oauth_credentials.json")

if not ANTHROPIC_API_KEY:
    raise ValueError("❌ Error: ANTHROPIC_API_KEY not found in .env file")

client = Anthropic(api_key=ANTHROPIC_API_KEY, timeout=120.0)
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096