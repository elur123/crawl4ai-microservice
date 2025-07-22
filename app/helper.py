import re

def extract_image_attribute(image: dict, desc_block: str) -> dict:
    desc_block = desc_block.replace("\n", " ").strip()
    clean_desc = clean_desc_with_repeating_word(desc_block)
    return {
        "src": image.get("src"),
        "alt": image.get("alt") or clean_desc.get("prefix"),
        "desc": clean_desc.get("desc"),
        "type": image.get("type"),
        "score": image.get("score"),
        "format": image.get("format"),
        "width": image.get("width")
    }

def split_desc_blocks(desc: str) -> list:
    return [block.strip() for block in desc.split("Read More") if block.strip()]

def get_repeating_prefix(text: str, max_chunk_words: int = 5) -> str:
    words = text.split()
    for size in range(max_chunk_words, 0, -1):  # Try chunks from 5 down to 1
        if len(words) < size * 2:
            continue
        chunk = " ".join(words[:size])
        next_chunk = " ".join(words[size:size*2])
        if chunk.lower() == next_chunk.lower():
            return chunk
    return ""

def clean_desc_with_repeating_word(desc: str) -> dict:
    prefix = get_repeating_prefix(desc)
    print(prefix)
    if prefix:
       # Escape special characters for regex
        pattern = re.compile(rf'^({re.escape(prefix)}\s*)+', re.IGNORECASE)
        desc = pattern.sub('', desc)
    return {
        "prefix": prefix,
        "desc": desc.strip()
    }

