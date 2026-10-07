"""
prompts.py  -  THE INSTRUCTIONS WE GIVE THE AI
==============================================

A "prompt" is the text we send to the AI. Good prompts = good results.
We keep them in their own file so you can improve the wording without
touching any of the logic.

Two kinds of prompt:
- SYSTEM PROMPT: permanent rules. Like a job description for a new copywriter.
- USER PROMPT:   the specific task right now ("write an email for VIPs about
                 this product with this offer").
"""

# {brand_name} and {tone} are blanks we fill in later with .format()
SYSTEM_PROMPT = """You are a senior email copywriter for the brand "{brand_name}".

Brand rules:
- Tone: {tone}.
- Write for the specific customer group you are given. Mention what matters to them.
- Never invent facts, prices or discounts that are not in the brief.
- Subject line: under 60 characters. Preview text: under 90 characters.
- Body: 80 to 140 words, short paragraphs, no more than one emoji.
- End with one clear call-to-action.

Reply ONLY with JSON in exactly this shape, and nothing else:
{{
  "subject": "...",
  "preview_text": "...",
  "body": "...",
  "cta": "...",
  "why_this_works": "one sentence explaining how this email fits this group"
}}"""
# Note: {{ and }} are written double so .format() leaves them as real { and } in the text.


# How we describe each segment to the AI. Clear descriptions = better targeting.
SEGMENT_DESCRIPTIONS = {
    "VIP": "Loyal, high-spending customers. Make them feel valued and first in line. "
           "Exclusivity and recognition matter more than the discount.",
    "Regular": "Customers who buy now and then. Remind them why they liked us and "
               "give them a reason to come back now.",
    "New": "First-time buyers. Welcome them warmly, build trust, and make the next "
           "purchase feel easy and low-risk.",
}


def build_system_prompt(brand_name, tone):
    """Fill the brand name and tone into the system prompt."""
    return SYSTEM_PROMPT.format(brand_name=brand_name, tone=tone)


def build_user_prompt(segment, segment_stats, product, offer):
    """
    Build today's task for ONE segment.
    segment_stats is one row from summarise_segments() - numbers about the group.
    """
    description = SEGMENT_DESCRIPTIONS.get(segment, "A group of our customers.")
    return f"""Write a marketing email for this customer group.

CUSTOMER GROUP: {segment}
Who they are: {description}
Group facts: {int(segment_stats['customers'])} customers, average spend {int(segment_stats['avg_spend'])} AED,
average age {int(segment_stats['avg_age'])}, average {int(segment_stats['avg_orders'])} orders, most live in {segment_stats['top_city']}.

PRODUCT: {product}
OFFER: {offer}
"""
