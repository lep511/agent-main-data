import re

def split_into_words(text: str) -> list[str]:
    # Split by whitespace and punctuation, keeping punctuation as separate tokens
    return re.findall(r'\S+|\S', text)