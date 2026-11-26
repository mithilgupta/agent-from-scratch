"""Talking to the model: setup and one call."""

import os

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

_client = None


def get_client() -> OpenAI:
    """Connect on first use, so importing this module needs no .env."""
    global _client
    if _client is None:
        load_dotenv(find_dotenv(usecwd=True))
        _client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.environ["LLM_BASE_URL"])
    return _client


def call_llm(conversation: list) -> str:
    """Send the whole conversation and return the reply as text."""
    response = get_client().chat.completions.create(model=os.environ["LLM_MODEL"], messages=conversation)
    return response.choices[0].message.content
