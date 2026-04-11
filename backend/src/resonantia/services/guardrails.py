"""Guardrails for Resonantia Lab — restrict LLM usage to lab informatics."""

ALLOWED_TOPICS = [
    "plate mapping", "plate map", "well plate", "microwell", "96-well", "384-well",
    "worklist", "liquid handler", "echo", "hamilton", "opentrons", "tecan",
    "dose-response", "dose response", "IC50", "EC50", "4PL", "curve fitting",
    "plate normalization", "z-score", "z-prime", "percent of control",
    "qPCR", "delta-delta Ct", "gene expression",
    "microscopy", "fluorescence", "DAPI", "GFP", "mCherry", "FOV", "field of view",
    "sample", "reagent", "antibody", "cell line", "compound", "buffer", "media",
    "inventory", "barcode", "lot number", "expiry", "storage",
    "experiment", "protocol", "assay", "screen", "screening",
    "data analysis", "data processing", "normalization",
    "lab", "laboratory", "instrument", "plate reader",
    "drug discovery", "hit", "lead", "target",
    "cherry pick", "serial dilution", "replicate", "randomize",
]

BLOCKED_PATTERNS = [
    "write me a poem", "tell me a joke", "write a story",
    "what is the meaning of life", "who is the president",
    "help me with my homework", "write an essay",
    "translate", "summarize this article",
    "code a website", "build an app", "write python",
    "investment advice", "stock market",
    "medical advice", "diagnose",
    "legal advice", "lawsuit",
]

GUARDRAIL_SYSTEM_PROMPT = """You are Resonantia Lab Assistant, a specialized AI for laboratory informatics.

IMPORTANT CONSTRAINTS:
- You ONLY help with lab informatics tasks: plate mapping, dose-response analysis, plate normalization, qPCR analysis, microscopy image browsing, sample/reagent tracking, experiment protocols, and related lab workflows.
- If a user asks about anything unrelated to laboratory science or lab informatics, politely decline and redirect them to lab-related tasks.
- You NEVER provide medical advice, legal advice, investment advice, or help with non-scientific tasks.
- You NEVER generate creative writing, code unrelated to lab analysis, or general knowledge answers.
- When declining, suggest relevant lab tasks you CAN help with.

YOUR CAPABILITIES:
- Design plate maps (96-well, 384-well) with cherry-pick, serial dilution, replicate, and randomize modes
- Generate worklists for Echo, Hamilton, and Opentrons liquid handlers
- Fit 4-parameter logistic dose-response curves and compute IC50/EC50
- Normalize plate data using Z-score, percent-of-control, or robust-Z methods
- Calculate Z-prime factor for assay quality assessment
- Perform delta-delta Ct analysis for qPCR data
- Browse microscopy images by plate, well, channel, and field of view
- Track samples and reagents with barcode, lot number, location, and expiry
- Design experimental protocols
- Search and analyze scientific literature related to lab methods
"""


def check_guardrails(user_message: str) -> tuple[bool, str]:
    """Check if a user message is within allowed lab informatics scope.

    Returns (is_allowed, reason).
    """
    message_lower = user_message.lower().strip()

    # Empty messages are fine (will get a generic response)
    if not message_lower:
        return True, ""

    # Check for explicitly blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if pattern in message_lower:
            return False, f"This request appears to be about '{pattern}', which is outside Resonantia Lab's scope. I can help you with plate mapping, dose-response analysis, sample tracking, microscopy, and other lab informatics tasks."

    # Short messages (under 10 chars) — allow through (likely greetings)
    if len(message_lower) < 10:
        return True, ""

    # Check if message relates to any allowed topic
    has_lab_context = any(topic in message_lower for topic in ALLOWED_TOPICS)

    # If no lab context detected, check if it's a general greeting or question
    greetings = ["hello", "hi", "hey", "help", "what can you do", "how does this work", "thanks", "thank you"]
    is_greeting = any(g in message_lower for g in greetings)

    if has_lab_context or is_greeting:
        return True, ""

    # Ambiguous — allow but flag for review (the LLM system prompt will handle edge cases)
    return True, "flagged_for_review"
