"""
llm.py  -  THE ONLY FILE THAT TALKS TO THE AI
=============================================

Every other file asks this file for help when it needs the AI.
Why keep it in one place?  If you ever switch from Gemini to Claude or GPT,
you only change THIS file. Nothing else in the project needs to know
which AI company is behind the answers.

What happens here, in plain English:
1. Read your secret API key from the .env file.
2. Send the AI two things: a SYSTEM PROMPT (permanent rules, like a job
   description) and a USER MESSAGE (today's specific task).
3. Get the answer back, plus how many TOKENS it used (tokens = small
   pieces of words; the AI is measured and billed in tokens).
"""

import os
import time                             # lets us pause before trying again

from dotenv import load_dotenv         # reads the .env file
from google import genai                # Google's official Gemini toolbox
from google.genai import types          # settings objects for Gemini

# Load the .env file so os.getenv() can see GEMINI_API_KEY.
load_dotenv()

# Google renames models every few months. We try these in order, so the app
# keeps working even if one name stops existing. You can force a specific
# model by adding a line  GEMINI_MODEL=model-name  to your .env file.
MODELS_TO_TRY = [
    os.getenv("GEMINI_MODEL"),       # your choice, if you set one
    "gemini-flash-latest",           # Google's "always the newest Flash" name
    "gemini-2.5-flash",              # well-known older name, as a backup
    "gemini-flash-lite-latest",      # smaller, faster model, last resort
]


class AIError(Exception):
    """A friendly error we show on screen instead of a scary crash."""


def get_api_key():
    """Return the API key, or raise a clear message if it's missing."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "paste-your-key-here":
        raise AIError(
            "No API key found. Open the .env file in this folder, paste your "
            "Gemini key after GEMINI_API_KEY=, save it, and restart the app."
        )
    return key


def ask_ai(system_prompt, user_message, temperature=0.7, want_json=False):
    """
    Send one request to Gemini and return a dictionary like:
        {"text": "...the answer...", "input_tokens": 512,
         "output_tokens": 230, "model": "gemini-flash-latest"}

    temperature: 0 = predictable and repeatable, 1 = more creative and varied.
    want_json:   True tells Gemini to reply ONLY with JSON (data our code can read).
    """
    client = genai.Client(api_key=get_api_key())

    settings = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=temperature,
        response_mime_type="application/json" if want_json else "text/plain",
    )

    last_problem = None
    for model in [m for m in MODELS_TO_TRY if m]:
        # Up to 3 tries on each model, waiting a bit longer each time (2s, then 4s).
        # This is called "retry with backoff" - every real AI app does it.
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model, contents=user_message, config=settings
                )
                usage = response.usage_metadata
                return {
                    "text": response.text or "",
                    "input_tokens": getattr(usage, "prompt_token_count", 0) or 0,
                    "output_tokens": getattr(usage, "candidates_token_count", 0) or 0,
                    "model": model,
                }
            except Exception as problem:
                last_problem = problem
                kind = what_went_wrong(str(problem))

                if kind == "busy" and attempt < 2:
                    time.sleep(2 * (attempt + 1))   # wait, then try the same model again
                    continue
                if kind in ("busy", "missing"):
                    break                           # give up on this model, try the next one
                if kind == "limit":
                    raise AIError(
                        "Gemini's free tier limit was reached. Wait one minute and "
                        "try again (or tomorrow, if you hit the daily limit)."
                    )
                if kind == "bad_key":
                    raise AIError(
                        "Gemini rejected your API key. Check it's pasted correctly in .env "
                        "with no spaces or quotes, then restart the app."
                    )
                raise AIError(f"Gemini returned an error: {problem}")

    raise AIError(
        "Gemini is busy or none of the model names worked. Wait a minute and click "
        "Generate again. If it keeps happening, check aistudio.google.com for a current "
        f"model name and add it to .env as GEMINI_MODEL=that-name. (Last error: {last_problem})"
    )


def what_went_wrong(message):
    """
    Read Google's error message and sort it into one of a few simple kinds,
    so ask_ai() can decide what to do: wait, switch model, or stop and explain.
    """
    if any(sign in message for sign in ("503", "UNAVAILABLE", "500", "INTERNAL", "overloaded")):
        return "busy"       # Google's servers are overloaded right now
    if "404" in message or "not found" in message.lower():
        return "missing"    # this model name doesn't exist (any more)
    if "429" in message or "RESOURCE_EXHAUSTED" in message:
        return "limit"      # too many requests for the free tier
    if "API key" in message or "API_KEY" in message:
        return "bad_key"    # key typed wrong or deleted
    return "other"
