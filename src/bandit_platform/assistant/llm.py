from __future__ import annotations

import os

import dotenv
from langchain_anthropic import ChatAnthropic

DEFAULT_MODEL = "claude-sonnet-5"


def get_chat_model(model: str = DEFAULT_MODEL) -> ChatAnthropic:
    dotenv.load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Add it to your local .env file (see .env.example)."
        )
    return ChatAnthropic(model=model, temperature=0)
