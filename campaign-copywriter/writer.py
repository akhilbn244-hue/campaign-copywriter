"""
writer.py  -  WRITES ONE EMAIL PER SEGMENT
==========================================

This file connects the pieces:
    prompts.py (what to say)  ->  llm.py (ask the AI)  ->  check the answer

The important lesson here: NEVER trust the AI's answer blindly.
We asked for JSON, but the AI can still:
- wrap it in ```json ... ``` markdown fences,
- forget a field,
- or return something that isn't JSON at all.
So we clean it, check it, and if it's broken we ask ONE more time.
"""

import json

from llm import ask_ai
from prompts import build_system_prompt, build_user_prompt

# Every email must have these fields, or our app can't display it.
REQUIRED_FIELDS = ["subject", "preview_text", "body", "cta"]


class BadAIAnswer(Exception):
    """The AI replied, but not in the shape we asked for."""


def parse_email_json(raw_text):
    """
    Turn the AI's reply (text) into a Python dictionary we can use.
    Raises BadAIAnswer if the reply can't be read or is missing fields.
    """
    text = raw_text.strip()

    # Step 1: remove markdown fences if the AI added them.
    if text.startswith("```"):
        text = text.strip("`")              # drop the backticks
        if text.lower().startswith("json"):
            text = text[4:]                 # drop the word "json"
        text = text.strip()

    # Step 2: if there's extra chatter around the JSON, keep only the {...} part.
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise BadAIAnswer("The reply contained no JSON at all.")
    text = text[start:end + 1]

    # Step 3: try to read it as JSON.
    try:
        email = json.loads(text)
    except json.JSONDecodeError as problem:
        raise BadAIAnswer(f"The JSON was broken: {problem}")

    # Step 4: check every required field is there and not empty.
    missing = [f for f in REQUIRED_FIELDS if not str(email.get(f, "")).strip()]
    if missing:
        raise BadAIAnswer("The reply was missing: " + ", ".join(missing))

    return email


def write_email_for_segment(segment, segment_stats, product, offer,
                            brand_name, tone, temperature=0.7):
    """
    Write one email for one segment.
    Returns (email_dictionary, usage_dictionary).
    Tries twice: if the first answer is broken, it asks again.
    """
    system_prompt = build_system_prompt(brand_name, tone)
    user_prompt = build_user_prompt(segment, segment_stats, product, offer)

    total_in, total_out = 0, 0
    last_problem = None

    for attempt in (1, 2):
        result = ask_ai(system_prompt, user_prompt, temperature=temperature, want_json=True)
        total_in += result["input_tokens"]
        total_out += result["output_tokens"]
        try:
            email = parse_email_json(result["text"])
            email["segment"] = segment
            usage = {"input_tokens": total_in, "output_tokens": total_out,
                     "attempts": attempt, "model": result["model"]}
            return email, usage
        except BadAIAnswer as problem:
            last_problem = problem
            # Second try: tell the AI exactly what went wrong.
            user_prompt += f"\n\nYour last reply could not be used ({problem}). Reply with valid JSON only."

    raise BadAIAnswer(f"Gave up on the {segment} email after 2 tries. {last_problem}")
