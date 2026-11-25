"""
test_agent.py - Anticipatory Agent for Rezolve Labs Challenge 1
"""
import re
from search import FILTER_FIELDS, load_catalogue, search

# 1. Vocabularies
CATEGORIES = {
    "running shoes": ["running shoes", "runners", "running shoe", "running sneakers"],
    "sneakers": ["sneakers", "sneaker", "casual shoes", "casual sneakers"],
    "sandals": ["sandals", "sandal", "slides", "slide", "floaters", "floater", "chappal", "chappals", "slippers"],
    "backpacks": ["backpacks", "backpack", "bag pack", "bagpack", "rucksack", "bag"],
    "caps": ["caps", "cap", "baseball cap", "hat"],
    "dresses": ["dresses", "dress", "one piece", "gown"],
    "headphones": ["headphones", "headphone", "earphones", "headset"],
    "hoodies": ["hoodies", "hoodie", "hooded sweatshirt", "sweatshirt"],
    "jackets": ["jackets", "jacket", "coat", "bomber"],
    "jeans": ["jeans", "jean", "denims", "denim"],
    "kurtas": ["kurtas", "kurta", "kurti"],
    "shirts": ["shirts", "shirt", "formal shirt", "button down"],
    "t-shirts": ["t-shirts", "t-shirt", "t shirt", "tshirt", "tee", "tees"],
    "track pants": ["track pants", "trackpants", "track pant", "joggers", "jogger", "sweatpants"],
    "wallets": ["wallets", "wallet"],
    "watches": ["watches", "watch", "wristwatch", "timepiece"]
}

BRANDS = [
    "Audora", "Carrafel", "Horavo", "Kesar Loom", "Kudova", "Ledgerly",
    "Loomsy", "Mehrin", "Northweft", "Pacevo", "Packwise", "Sonquil",
    "Strydo", "Tanaro", "Tikkra", "Urbanyx", "Wavlo", "Zentrail"
]

COLOURS = {
    "black": ["black", "kaala", "kala"],
    "white": ["white", "safed", "chitta"],
    "red": ["red", "laal", "lal"],
    "blue": ["blue", "neela", "nila"],
    "navy": ["navy", "navy blue"],
    "green": ["green", "hara", "hari"],
    "grey": ["grey", "gray", "sleti", "saleti"],
    "yellow": ["yellow", "peela", "pila"],
    "brown": ["brown", "bhoora", "bhura"],
    "beige": ["beige"],
    "olive": ["olive", "olive green"],
    "pink": ["pink", "gulabi"],
    "maroon": ["maroon"],
    "gold": ["gold", "golden"],
    "silver": ["silver"],
    "tan": ["tan"]
}

SIZES_MAP = {
    "xxl": "XXL", "double xl": "XXL", "2xl": "XXL",
    "xl": "XL", "extra large": "XL",
    "l": "L", "large": "L",
    "m": "M", "medium": "M",
    "s": "S", "small": "S",
    "xs": "XS", "extra small": "XS",
    "6": "6", "six": "6", "chhah": "6", "che": "6",
    "7": "7", "seven": "7", "saat": "7",
    "8": "8", "eight": "8", "aath": "8",
    "9": "9", "nine": "9", "nau": "9",
    "10": "10", "ten": "10", "dus": "10",
    "11": "11", "eleven": "11", "gyaarah": "11",
    "28": "28", "30": "30", "32": "32", "34": "34", "36": "36"
}

NUM_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "hundred": 100, "thousand": 1000
}

def parse_price(text):
    # k pattern: 1.1k -> 1100, 2k -> 2000, 0.7k -> 700
    m_k = re.search(r"(\d+(?:\.\d+)?)\s*k\b", text)
    if m_k:
        return int(float(m_k.group(1)) * 1000)
        
    # Hindi price patterns
    if "saadhe teen hazaar" in text:
        return 3500
    if "pandrah sau" in text:
        return 1500
    if "paanch sau" in text:
        return 500
    if "ek hazaar" in text:
        return 1000
    if "do hazaar" in text:
        return 2000
    if "teen hazaar" in text:
        return 3000
    if "chaar hazaar" in text:
        return 4000
    if "paanch hazaar" in text:
        return 5000
    if "dus hazaar" in text:
        return 10000
        
    # Spoken number patterns like "forty five hundred", "seven hundred", "two thousand", "four thousand"
    m_spoken = re.search(r"\b(forty\s+five\s+hundred|seven\s+hundred|eight\s+hundred|nine\s+hundred|one\s+thousand|two\s+thousand|three\s+thousand|four\s+thousand|five\s+thousand|fifteen\s+hundred)\b", text)
    if m_spoken:
        sp = m_spoken.group(1)
        if sp == "forty five hundred": return 4500
        if sp == "seven hundred": return 700
        if sp == "eight hundred": return 800
        if sp == "nine hundred": return 900
        if sp == "fifteen hundred": return 1500
        if sp == "one thousand": return 1000
        if sp == "two thousand": return 2000
        if sp == "three thousand": return 3000
        if sp == "four thousand": return 4000
        if sp == "five thousand": return 5000

    # Digits pattern
    m_dig = re.findall(r"\b(?:under|below|less than|within|max|up to|budget|not more than|tak|kam)\s+(?:rs\.?\s*|₹)?([\d,]+)\b", text)
    if m_dig:
        val = int(m_dig[-1].replace(",", ""))
        if 200 <= val <= 100000:
            return val
            
    m_simple = re.findall(r"\b(?:under|below|max|budget)\s+([\d,]+)\b", text)
    if m_simple:
        return int(m_simple[-1].replace(",", ""))

    return None

class Agent:
    def __init__(self, tools):
        self.tools = tools
        self.cat = load_catalogue()

    def start(self, request_id):
        self.request_id = request_id
        self.words = []
        self.last_search_filters = None
        self.cached_hits = []
        self.committed = None
        self.searches = 0

    def extract_filters(self, text):
        lower = text.lower()
        filters = {
            "category": None,
            "brand": None,
            "colour": None,
            "size": None,
            "max_price": None
        }

        # Check for corrections/retractions
        # e.g. "oops, XS", "sorry, size 7", "no wait", "actually", "I mean", "no, change that to", "make that", "nahi,"
        # Split text by correction markers
        corr_split = re.split(r"\b(?:oops|sorry|no wait|actually|i mean|no, change that to|make that|nahi|scratch that)\b", lower)
        segments = [s.strip() for s in corr_split if s.strip()]

        for seg in segments:
            # 1. Brand
            for b in sorted(BRANDS, key=len, reverse=True):
                if re.search(rf"\b{re.escape(b.lower())}\b", seg):
                    filters["brand"] = b
                    break

            # 2. Category
            for cat, aliases in CATEGORIES.items():
                for alias in sorted(aliases, key=len, reverse=True):
                    if re.search(rf"\b{re.escape(alias)}\b", seg):
                        filters["category"] = cat
                        break
                if filters["category"]:
                    break

            # 3. Colour
            for col, aliases in COLOURS.items():
                for alias in sorted(aliases, key=len, reverse=True):
                    if re.search(rf"\b{re.escape(alias)}\b", seg):
                        filters["colour"] = col
                        break
                if filters["colour"]:
                    break

            # 4. Size
            # Check explicit size patterns first
            m_sz = re.findall(r"\b(?:size|uk|waist)?\s*([a-z0-9]+)\s*(?:uk|waist)?\b", seg)
            for cand in m_sz:
                if cand in SIZES_MAP:
                    filters["size"] = SIZES_MAP[cand]
                    
            # Check multi-word sizes: "extra large", "double xl", "extra small"
            for k_sz in ["extra small", "double xl", "extra large", "medium", "small", "large"]:
                if re.search(rf"\b{k_sz}\b", seg):
                    filters["size"] = SIZES_MAP[k_sz]
                    break

        # 5. Price
        p = parse_price(lower)
        if p is not None:
            filters["max_price"] = p

        return filters

    def observe(self, word):
        self.words.append(word)
        text = " ".join(self.words)
        filters = self.extract_filters(text)

        # Early search trigger: only if we have at least category or brand, and at least 2 filters
        active_f = sum(1 for k in ["category", "brand", "colour", "size"] if filters[k] is not None)
        
        # Check if filters changed since last search
        if active_f >= 2 and filters != self.last_search_filters and self.searches < 3:
            self.cached_hits = self.tools.search(text, {k: v for k, v in filters.items() if v is not None}, k=5)
            self.last_search_filters = dict(filters)
            self.searches += 1

        # Check commit condition
        # If we have hits and only 1 product matches, or score gap is decisive
        if self.cached_hits and not self.committed:
            # Check if all key attributes required by category are present
            cat = filters.get("category")
            has_colour = bool(filters.get("colour"))
            has_size = bool(filters.get("size"))
            has_brand = bool(filters.get("brand"))

            # Caps, wallets, watches, backpacks don't need size
            size_required = cat in ["running shoes", "sneakers", "sandals", "hoodies", "jackets", "jeans", "kurtas", "shirts", "t-shirts", "track pants", "dresses"]
            
            # If all required attributes for this product are specified
            if cat and (not size_required or has_size) and has_colour and (has_brand or len(self.cached_hits) == 1):
                # Verify search is fresh with current filters
                if filters != self.last_search_filters:
                    self.cached_hits = self.tools.search(text, {k: v for k, v in filters.items() if v is not None}, k=5)
                    self.last_search_filters = dict(filters)
                    self.searches += 1

                if self.cached_hits:
                    top_prod = self.cached_hits[0]["product_id"]
                    # If single match or decisive lead
                    if len(self.cached_hits) == 1 or (self.cached_hits[0]["score"] > self.cached_hits[1]["score"]):
                        self.committed = top_prod
                        return {"commit": top_prod, "filters": filters}

        return {"filters": filters}

    def finish(self):
        text = " ".join(self.words)
        filters = self.extract_filters(text)
        clean_filters = {k: v for k, v in filters.items() if v is not None}
        
        hits = self.tools.search(text, clean_filters, k=1)
        if hits:
            return hits[0]["product_id"]
            
        # Fallback drop filters
        for drop in ("max_price", "size", "colour", "brand", "category"):
            clean_filters.pop(drop, None)
            hits = self.tools.search(text, clean_filters, k=1)
            if hits:
                return hits[0]["product_id"]
                
        return self.committed
