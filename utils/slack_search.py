"""
Slack Real-Time Search API integration.
Uses assistant.search.context to search workspace messages for food-related context.
"""


def search_workspace_food_context(client, query: str, action_token: str = None) -> str:
    """
    Search the Slack workspace for past discussions about a food or restaurant.
    Returns a summarised string of relevant findings, or empty string if none.
    """
    try:
        payload = {
            "query": query,
            "channel_types": ["public_channel", "private_channel", "mpim", "im"],
            "content_types": ["messages"],
            "limit": 5,
        }
        if action_token:
            payload["action_token"] = action_token

        response = client.api_call("assistant.search.context", json=payload)

        if not response["ok"]:
            return ""

        messages = response.get("results", {}).get("messages", [])
        if not messages:
            return ""

        snippets = []
        for msg in messages:
            author = msg.get("author_name", "Someone")
            content = msg.get("content", "").strip()
            channel = msg.get("channel_name", "")
            if content:
                location = f"#{channel}" if channel else "Slack"
                snippets.append(f'- {author} in {location}: "{content[:200]}"')

        if not snippets:
            return ""

        return "Relevant past Slack discussions:\n" + "\n".join(snippets)

    except Exception as e:
        print(f"[RTS] error: {e}")
        return ""
