from dotenv import load_dotenv
import os
from anthropic import Anthropic

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

client = Anthropic(api_key = ANTHROPIC_API_KEY)
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024