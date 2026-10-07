# AI Campaign Copywriter

Generates segment-personalised marketing emails from a customer CSV using the Gemini API, with structured JSON output and token tracking.

<!-- Add a screenshot here: drag a PNG into this file on GitHub, or save it as screenshot.png in the repo -->
![App screenshot](screenshot.png)

## How it works

1. Upload a customer CSV (name, email, age, city, total spend, orders, last purchase).
2. **pandas** sorts customers into segments with simple rules: New (1 order), VIP (1,000+ AED spent), Regular.
3. Each segment is summarised (size, average spend, age, top city) so the AI knows who it is writing for, without sending personal data.
4. A **system prompt** sets the brand rules; a **user prompt** gives the segment and the offer.
5. **Gemini** replies in JSON (subject, preview text, body, call-to-action). The code checks the JSON and retries once if it is broken.
6. Results appear on screen and can be downloaded as JSON or CSV.

## Tech used

Python · Gemini API (`google-genai`) · Streamlit · pandas · python-dotenv

## Project structure

| File | Job |
| --- | --- |
| `app.py` | The web page: upload, settings, Generate button, results |
| `segmenter.py` | Reads the CSV and assigns each customer a segment |
| `prompts.py` | The system prompt and per-segment instructions |
| `writer.py` | Calls the AI per segment and validates the JSON reply |
| `llm.py` | The only file that talks to the AI provider (easy to swap to Claude or GPT) |

## How to run it (Windows)

1. Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).
2. Double-click `setup.bat`. When Notepad opens, paste your key after `GEMINI_API_KEY=`, save, close.
3. Double-click `run.bat`. The app opens in your browser.

## What I learned

- _Write 3 bullets in your own words after the walkthrough._

## What I'd build next

- An "At risk" segment for customers who haven't bought in 6 months
- A/B variants: two subject lines per segment
- Send drafts straight to an email platform such as Mailchimp
