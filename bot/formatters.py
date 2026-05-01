import re


def format_for_telegram(text: str) -> str:
    """Ensure itinerary text is Telegram MarkdownV2 safe-ish.
    We use HTML parse mode instead for reliability."""
    # Convert markdown bold to HTML bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Convert markdown italic
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', text)
    return text


def chunk_message(text: str, max_length: int = 4000) -> list[str]:
    """Split long messages into Telegram-safe chunks."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break
        # Find a good split point (newline near the limit)
        split_at = text.rfind("\n", 0, max_length)
        if split_at == -1:
            split_at = max_length
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks
