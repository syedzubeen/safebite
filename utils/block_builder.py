"""
Block Kit message builder for SafeBite responses.
Converts structured food safety data into rich Slack Block Kit messages.
"""

CONDITION_LABELS = {
    "celiac": "Celiac Disease",
}

VERDICT_COLORS = {
    "safe": "#2EB67D",
    "caution": "#ECB22E",
    "unsafe": "#E01E5A",
}

VERDICT_EMOJI = {
    "safe": "✅",
    "caution": "⚠️",
    "unsafe": "❌",
}

VERDICT_LABELS = {
    "safe": "Safe",
    "caution": "Use Caution",
    "unsafe": "Unsafe",
}


def _parse_verdict(verdict_str: str) -> str:
    v = verdict_str.lower()
    if "unsafe" in v or "❌" in v:
        return "unsafe"
    if "caution" in v or "⚠️" in v:
        return "caution"
    return "safe"


def food_query_blocks(query: str, verdict: str, analysis: str, alternatives: str, workspace_note: str = "") -> tuple[list, list]:
    """
    Returns (blocks, attachments) for a food safety query response.
    Uses colored left-border attachment for the verdict banner.
    """
    verdict_key = _parse_verdict(verdict)
    color = VERDICT_COLORS[verdict_key]
    emoji = VERDICT_EMOJI[verdict_key]
    label = VERDICT_LABELS[verdict_key]

    # Header blocks (outside attachment — no color)
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Food Safety Check* — _{query}_",
            },
        },
    ]

    # Colored verdict attachment
    attachment_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{emoji} *{label}*",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*ANALYSIS:*\n{analysis}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*SAFE ALTERNATIVES:*\n{alternatives}",
            },
        },
    ]

    if workspace_note:
        attachment_blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"📌 {workspace_note}"}],
        })

    attachment_blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": "SafeBite · Results based on typical ingredients. Always confirm with the restaurant."}],
    })

    attachments = [{"color": color, "blocks": attachment_blocks}]
    return blocks, attachments


def guardian_alert_blocks(context: str, verdict: str, watch_out: str, suggestion: str) -> tuple[list, list]:
    """Returns (blocks, attachments) for a Silent Guardian alert."""
    verdict_key = _parse_verdict(verdict)
    color = VERDICT_COLORS[verdict_key]
    emoji = VERDICT_EMOJI[verdict_key]
    label = VERDICT_LABELS[verdict_key]

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*SafeBite Alert* — food mentioned in your channel\n_{context}_",
            },
        },
    ]

    attachment_blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"{emoji} *{label}*"},
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*WATCH OUT FOR:*\n{watch_out}"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*SUGGESTION:*\n{suggestion}"},
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": "SafeBite · Only you can see this alert."}],
        },
    ]

    attachments = [{"color": color, "blocks": attachment_blocks}]
    return blocks, attachments


def restaurant_scan_blocks(restaurant: str, safe: list, modify: list, avoid: list, tips: str, conditions: str) -> tuple[list, list]:
    """Returns (blocks, attachments) for a restaurant scan."""
    has_safe = len(safe) >= 2
    color = VERDICT_COLORS["safe"] if has_safe else VERDICT_COLORS["caution"] if safe else VERDICT_COLORS["unsafe"]
    verdict_text = "Safe options available" if has_safe else "Limited options" if safe else "Nothing safe found"
    verdict_emoji = "✅" if has_safe else "⚠️" if safe else "❌"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"🍽️ {restaurant}", "emoji": True},
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"Your conditions: {conditions}"}],
        },
    ]

    attachment_blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"{verdict_emoji} *{verdict_text}*"},
        },
        {"type": "divider"},
    ]

    if safe:
        safe_text = "\n".join(f"🟢 {dish}" for dish in safe)
        attachment_blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*LIKELY SAFE:*\n{safe_text}"},
        })

    if avoid:
        avoid_text = "\n".join(f"🔴 {dish}" for dish in avoid[:5])
        if len(avoid) > 5:
            avoid_text += f"\n_...and {len(avoid) - 5} more items to avoid_"
        attachment_blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*AVOID:*\n{avoid_text}"},
        })

    if tips:
        attachment_blocks.append({"type": "divider"})
        attachment_blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"💡 *TIP:* {tips}"},
        })

    attachment_blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": "SafeBite · Based on typical ingredients. Always confirm with the restaurant."}],
    })

    attachments = [{"color": color, "blocks": attachment_blocks}]
    return blocks, attachments
