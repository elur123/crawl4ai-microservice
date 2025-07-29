import re
import ast
from lxml import html

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

def extract_repeated_sections(raw_html):
    tree = html.fromstring(raw_html)
    repeated_blocks = []

    for parent in tree.xpath("//*[count(*) > 2]"):
        children = parent.getchildren()

        tag_names = [child.tag for child in children]
        if len(set(tag_names)) == 1 and len(children) >= 3:
            blocks = []
            for child in children:
                imgs = child.xpath(".//img")
                if imgs:
                    img_src = imgs[0].get("data-src") if imgs[0].get("data-src") else imgs[0].get("src")  # take first image
                    text = child.text_content().strip()

                    # Try to find the first heading inside the block
                    heading = child.xpath(
                        ".//*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6 or contains(@class, 'title')]"
                    )
                    title = heading[0].text_content().strip() if heading else ""

                    if "\n" not in title:
                        blocks.append({
                            "img_src": img_src,
                            "title": title,
                            "description": text,
                            "html": html.tostring(child, encoding="unicode"),
                        })

            if len(blocks) >= 2:
                repeated_blocks.append(blocks)

    # Flatten and deduplicate by title
    flat_services = []
    seen_titles = set()

    for block_group in repeated_blocks:
        for item in block_group:
            title_key = item["title"].strip().lower()
            if title_key and title_key not in seen_titles:
                seen_titles.add(title_key)
                flat_services.append(item)

    return flat_services

def extract_basic_info(raw_html):
    tree = html.fromstring(raw_html)
    text = tree.text_content()

    contact_info = extract_contact_info(raw_html)

    email = contact_info.get("email")
    phone = contact_info.get("phone")
    address = contact_info.get("address")
    logo = tree.xpath('//img[contains(@src, "logo")]/@src')
    title = tree.xpath('//title/text()')
    
    return {
        "name": title[0].strip() if title else "",
        "email": email[0] if email else "",
        "phone": ''.join(phone[0]) if phone else "",
        "address": address[0] if address else "",
        "logo": logo[0] if logo else "",
    }

def extract_contact_info(raw_html):
    tree = html.fromstring(raw_html)

    # Extract text from <footer> and nearby elements
    footer = tree.xpath('//footer')
    footer_text = ""
    if footer:
        footer_text = footer[0].text_content()
    else:
        # Fallback: last few <div>s or body bottom (heuristic)
        last_divs = tree.xpath('//div[position() > last()-3]')
        footer_text = " ".join(div.text_content() for div in last_divs)

    # Normalize text
    text = re.sub(r'\s+', ' ', footer_text)

    # Extract email
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)

    # Extract phone (simplified)
    phones = re.findall(r'(\+?\d[\d\s\-\(\)]{7,}\d)', text)

    # Extract address (very fuzzy heuristic)
    address_matches = re.findall(
        r'\d{1,5}\s+\w+(?:\s+\w+)*,?\s+\w+(?:\s+\w+)*,?\s+[A-Z]{2,3}\s+\d{4,6}',
        text
    )

    return {
        "email": list(set(emails)),
        "phone": list(set(phones)),
        "address": list(set(address_matches))
    }

def extact_fonts_colors_from_console(console_messages):
    def dedup(seq):
        seen = set()
        return [x for x in seq if not (x in seen or seen.add(x))]

    fonts = []
    colors = []
    info_filtered = [item for item in console_messages if item.get("type") == "info"]
    
    for item in info_filtered:
        text = item["text"]

        match = re.search(r'\[([^\]]+)\]', text)
        if not match:
            continue
        
        # Split values by comma and clean up
        values = [v.strip().strip('"') for v in match.group(1).split(',')]

        if text.startswith("fonts"):
            fonts.extend(values)
        elif text.startswith("colors"):
            colors.extend(values)

    return {
        "fonts": dedup(fonts),
        "colors": dedup(colors)
    }

def js_fonts_colors_extractor():
    return """function extractFont() {
        const fonts = new Set();

        document.querySelectorAll('*').forEach(el => {
            const font = window.getComputedStyle(el).getPropertyValue('font-family');
            if (font) fonts.add(font.trim());
        });

        console.info("fonts", [...fonts]);
        return fonts;
    } 

    function extractColors(minCount = 20) {
        const rgbToHex = (rgb) => {
            const match = rgb.match(/\d+/g);
            if (!match || match.length < 3) return null;

            return (
                '#' +
                match.slice(0, 3)
                    .map(x => parseInt(x).toString(16).padStart(2, '0'))
                    .join('')
                    .toUpperCase()
            );
        };

        const elements = document.querySelectorAll('*');
        const colorCount = {};

        elements.forEach(el => {
            const style = window.getComputedStyle(el);
            ['color', 'backgroundColor', 'borderColor'].forEach(prop => {
                const rgb = style[prop];
                if (rgb && rgb.startsWith('rgb')) {
                    const hex = rgbToHex(rgb);
                    if (hex) {
                        colorCount[hex] = (colorCount[hex] || 0) + 1;
                    }
                }
            });
        });

        const colors =  Object.entries(colorCount)
            .filter(([, count]) => count > minCount)
            .sort((a, b) => b[1] - a[1])
            .map(([hex, count]) => hex);

        console.info("colors", colors);
        return colors;
    }
    
    extractFont();
    extractColors();
    """