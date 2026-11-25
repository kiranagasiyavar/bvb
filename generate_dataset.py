"""
Script to generate:
1. catalogue.csv (~1,000 products: category, colour, size, price, brand)
2. dev.jsonl (~300 word-by-word streaming requests with ground truth filters and target product)
"""
import csv
import json
import random

# Seed for reproducibility
random.seed(42)

CATEGORIES = [
    "running shoes", "sneakers", "formal shoes", "sandals", "boots",
    "t-shirt", "polo shirt", "formal shirt", "hoodie", "jacket",
    "jeans", "trousers", "joggers", "shorts", "dress",
    "smartwatch", "analog watch", "backpack", "duffle bag", "sunglasses",
    "wireless headphones", "earbuds", "laptop", "tablet", "smartphone"
]

BRANDS = {
    "running shoes": ["Nike", "Adidas", "Puma", "Asics", "Reebok", "New Balance"],
    "sneakers": ["Nike", "Adidas", "Puma", "Converse", "Vans", "Puma"],
    "formal shoes": ["Clarks", "Bata", "Hush Puppies", "Louis Philippe", "Woodland"],
    "sandals": ["Bata", "Crocs", "Woodland", "Birkenstock", "Sparx"],
    "boots": ["Woodland", "Timberland", "Red Tape", "Clarks"],
    "t-shirt": ["Nike", "Adidas", "Puma", "Zara", "H&M", "Levi's", "Roadster", "Under Armour"],
    "polo shirt": ["Lacoste", "Ralph Lauren", "Tommy Hilfiger", "US Polo", "Allen Solly"],
    "formal shirt": ["Peter England", "Arrow", "Van Heusen", "Raymond", "Louis Philippe"],
    "hoodie": ["Nike", "Adidas", "Puma", "H&M", "Zara", "GAP"],
    "jacket": ["Wildcraft", "Columbia", "Zara", "Levi's", "The North Face", "Puma"],
    "jeans": ["Levi's", "Wrangler", "Pepe Jeans", "Spykar", "Diesel", "Lee"],
    "trousers": ["Peter England", "Arrow", "Van Heusen", "Raymond", "Blackberrys"],
    "joggers": ["Nike", "Adidas", "Puma", "Under Armour", "HRX"],
    "shorts": ["Nike", "Adidas", "Puma", "Decathlon", "Under Armour"],
    "dress": ["Zara", "H&M", "Forever 21", "Marks & Spencer", "AND", "ONLY"],
    "smartwatch": ["Apple", "Samsung", "Garmin", "Fossil", "Fitbit", "Noise", "Boat", "Fire-Boltt"],
    "analog watch": ["Titan", "Fossil", "Timex", "Casio", "Tommy Hilfiger", "Fastrack"],
    "backpack": ["Wildcraft", "American Tourister", "Skybags", "Samsonite", "Nike", "Puma"],
    "duffle bag": ["Nike", "Adidas", "Wildcraft", "Puma", "American Tourister"],
    "sunglasses": ["Ray-Ban", "Oakley", "Fastrack", "Polaroid", "Carrera"],
    "wireless headphones": ["Sony", "Bose", "Sennheiser", "JBL", "Boat", "Marshall"],
    "earbuds": ["Apple", "Samsung", "Sony", "Boat", "JBL", "OnePlus", "Noise"],
    "laptop": ["Apple", "Dell", "HP", "Lenovo", "Asus", "Acer"],
    "tablet": ["Apple", "Samsung", "Lenovo", "OnePlus", "Xiaomi"],
    "smartphone": ["Apple", "Samsung", "Google", "OnePlus", "Xiaomi", "Vivo", "Realme"]
}

COLOURS = [
    "black", "white", "red", "blue", "navy", "green", "grey", "yellow", "brown", "beige", "olive", "pink"
]

SIZES_BY_CATEGORY = {
    "footwear": ["6", "7", "8", "9", "10", "11", "12"],
    "clothing": ["XS", "S", "M", "L", "XL", "XXL"],
    "waist": ["28", "30", "32", "34", "36", "38"],
    "one_size": ["Standard", "Free Size"],
    "tech": ["64GB", "128GB", "256GB", "512GB", "1TB"]
}

CATEGORY_SIZE_TYPE = {
    "running shoes": "footwear", "sneakers": "footwear", "formal shoes": "footwear",
    "sandals": "footwear", "boots": "footwear",
    "t-shirt": "clothing", "polo shirt": "clothing", "formal shirt": "clothing",
    "hoodie": "clothing", "jacket": "clothing", "dress": "clothing",
    "jeans": "waist", "trousers": "waist", "joggers": "clothing", "shorts": "clothing",
    "smartwatch": "one_size", "analog watch": "one_size", "backpack": "one_size",
    "duffle bag": "one_size", "sunglasses": "one_size", "wireless headphones": "one_size",
    "earbuds": "one_size",
    "laptop": "tech", "tablet": "tech", "smartphone": "tech"
}

PRICE_RANGES = {
    "running shoes": (1800, 14000), "sneakers": (1500, 11000), "formal shoes": (1800, 9500),
    "sandals": (600, 4500), "boots": (2500, 12000),
    "t-shirt": (499, 2999), "polo shirt": (899, 5999), "formal shirt": (999, 4999),
    "hoodie": (1499, 6999), "jacket": (2499, 14999), "dress": (1199, 7999),
    "jeans": (1299, 6999), "trousers": (1199, 4999), "joggers": (899, 3999), "shorts": (599, 2499),
    "smartwatch": (1999, 45000), "analog watch": (1499, 18000), "backpack": (899, 5499),
    "duffle bag": (999, 4999), "sunglasses": (799, 12000),
    "wireless headphones": (1499, 29999), "earbuds": (999, 24999),
    "laptop": (28000, 145000), "tablet": (14000, 85000), "smartphone": (9999, 125000)
}

CATEGORY_IMAGES = {
    "running shoes": [
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1600185365483-26d7a4cc7519?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1515955656352-a1fa3ffcd111?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=600&q=80"
    ],
    "sneakers": [
        "https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1560769629-975ec94e6a86?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=600&q=80"
    ],
    "formal shoes": [
        "https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1533867617858-e7b97e060509?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1582588678413-dbf45f4823e9?auto=format&fit=crop&w=600&q=80"
    ],
    "sandals": [
        "https://images.unsplash.com/photo-1603808033192-082d6919d3e1?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1562273138-f46be4ebdf33?auto=format&fit=crop&w=600&q=80"
    ],
    "boots": [
        "https://images.unsplash.com/photo-1608256246200-53e635b5b65f?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1520639888713-7851133b1ed0?auto=format&fit=crop&w=600&q=80"
    ],
    "t-shirt": [
        "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1576566588028-4147f3842f27?auto=format&fit=crop&w=600&q=80"
    ],
    "polo shirt": [
        "https://images.unsplash.com/photo-1625910513413-5626c9f65d64?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1586363104862-3a5e2ab60d99?auto=format&fit=crop&w=600&q=80"
    ],
    "formal shirt": [
        "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?auto=format&fit=crop&w=600&q=80"
    ],
    "hoodie": [
        "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1509967419530-da38b4704bc6?auto=format&fit=crop&w=600&q=80"
    ],
    "jacket": [
        "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1548883354-7622d03aca27?auto=format&fit=crop&w=600&q=80"
    ],
    "jeans": [
        "https://images.unsplash.com/photo-1542272604-780c96856592?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=600&q=80"
    ],
    "trousers": [
        "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?auto=format&fit=crop&w=600&q=80"
    ],
    "joggers": [
        "https://images.unsplash.com/photo-1517445312882-bc9910d016b7?auto=format&fit=crop&w=600&q=80"
    ],
    "shorts": [
        "https://images.unsplash.com/photo-1591195853828-11db59a44f6b?auto=format&fit=crop&w=600&q=80"
    ],
    "dress": [
        "https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?auto=format&fit=crop&w=600&q=80"
    ],
    "smartwatch": [
        "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?auto=format&fit=crop&w=600&q=80"
    ],
    "analog watch": [
        "https://images.unsplash.com/photo-1524805444758-089113d48a6d?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=600&q=80"
    ],
    "backpack": [
        "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?auto=format&fit=crop&w=600&q=80"
    ],
    "duffle bag": [
        "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=600&q=80"
    ],
    "sunglasses": [
        "https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1572635196237-14b3f281503f?auto=format&fit=crop&w=600&q=80"
    ],
    "wireless headphones": [
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=600&q=80"
    ],
    "earbuds": [
        "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?auto=format&fit=crop&w=600&q=80"
    ],
    "laptop": [
        "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=600&q=80"
    ],
    "tablet": [
        "https://images.unsplash.com/photo-1561154464-82e9adf32764?auto=format&fit=crop&w=600&q=80"
    ],
    "smartphone": [
        "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=600&q=80"
    ]
}

def get_product_image(category, product_id):
    imgs = CATEGORY_IMAGES.get(category, [
        "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80"
    ])
    return imgs[product_id % len(imgs)]

DESCRIPTIONS_TEMPLATES = {
    "running shoes": "Engineered for responsive cushioning, endurance running, and daily sprint training.",
    "sneakers": "Street-style casual footwear offering all-day comfort and durable grip.",
    "formal shoes": "Handcrafted leather formal footwear suited for business attire and black-tie events.",
    "sandals": "Breathable, lightweight open footwear crafted for tropical comfort and leisure.",
    "boots": "Rugged all-weather boots designed for trekking, outdoor adventures, and winter wear.",
    "t-shirt": "Breathable cotton tee crafted for casual outings, daily lounging, and gym sessions.",
    "polo shirt": "Smart-casual collared polo offering timeless style for golf, brunch, and semi-formals.",
    "formal shirt": "Crisp wrinkle-resistant formal shirt tailored for executive boardroom presentations.",
    "hoodie": "Cozy fleece-lined pullover hoodie providing thermal warmth during chilly mornings.",
    "jacket": "Weatherproof insulated outer layer protecting against heavy wind, rain, and cold.",
    "jeans": "Classic denim with stretch comfort, designed for effortless casual styling.",
    "trousers": "Tailored slim-fit trousers perfect for office wear and smart-casual meetings.",
    "joggers": "Flexible athletic joggers with tapered cuffs for training, running, and traveling.",
    "shorts": "Lightweight quick-drying athletic shorts offering unrestricted movement.",
    "dress": "Elegant silhouette crafted for evening parties, dinners, and celebratory occasions.",
    "smartwatch": "Feature-packed wearable monitoring heart rate, SpO2, sleep, and GPS workouts.",
    "analog watch": "Classic precision timepiece featuring metallic dial and premium leather strap.",
    "backpack": "Ergonomic multi-compartment travel pack with padded laptop sleeve and water resistance.",
    "duffle bag": "Spacious cylindrical gear bag with shoulder strap, ideal for gym and weekend trips.",
    "sunglasses": "UV400 polarized shades delivering crisp glare reduction and eye protection.",
    "wireless headphones": "Active noise-cancelling over-ear headphones delivering immersive studio fidelity.",
    "earbuds": "True wireless Bluetooth earbuds with low latency, ENC mics, and fast charging.",
    "laptop": "High-performance computing machine for coding, creative design, and multitasking.",
    "tablet": "Vibrant touchscreen tablet suited for digital illustration, reading, and streaming.",
    "smartphone": "Flagship 5G smartphone with multi-lens camera system and all-day battery life."
}

def generate_catalogue(n=1000):
    products = []
    used_combos = set()
    product_id = 1

    while len(products) < n:
        cat = random.choice(CATEGORIES)
        brand = random.choice(BRANDS[cat])
        colour = random.choice(COLOURS)
        size_type = CATEGORY_SIZE_TYPE[cat]
        size = random.choice(SIZES_BY_CATEGORY[size_type])
        
        # Ensure 100% unique (brand, category, colour, size) combinations
        combo = (brand, cat, colour, size)
        if combo in used_combos:
            continue
        used_combos.add(combo)
        
        min_p, max_p = PRICE_RANGES[cat]
        # round price to nice numbers (e.g. 1999, 2499, 4999)
        raw_price = random.randint(min_p // 100, max_p // 100) * 100 - 1
        if raw_price < min_p:
            raw_price = min_p
        
        title = f"{brand} {colour.capitalize()} {cat.title()}"
        if size_type in ["footwear", "waist", "clothing", "tech"]:
            title_with_size = f"{title} (Size {size})"
        else:
            title_with_size = title
            
        # 92% in stock, 8% out of stock for demo of restock notifications
        in_stock = 0 if random.random() < 0.08 else random.randint(5, 50)
        
        desc = DESCRIPTIONS_TEMPLATES.get(cat, "High-quality premium product tailored for everyday lifestyle needs.")
        img_url = get_product_image(cat, product_id)
        
        products.append({
            "id": f"PRD{product_id:04d}",
            "title": title_with_size,
            "category": cat,
            "brand": brand,
            "colour": colour,
            "size": size,
            "price": raw_price,
            "stock": in_stock,
            "usage": desc,
            "image_url": img_url
        })
        product_id += 1
        
    return products

# Hindi translation dict for code-mixed generation
HINDI_COLOURS = {
    "black": "kaala", "white": "safed", "red": "laal", "blue": "neela",
    "green": "hara", "yellow": "peela", "brown": "bhoora", "grey": "sleti"
}
HINDI_NUMBERS = {
    "6": "chhah", "7": "saat", "8": "aath", "9": "nau", "10": "dus", "11": "gyaarah", "12": "baarah"
}

def generate_dev_set(catalogue, count=320):
    dev_records = []
    
    for i in range(count):
        target = random.choice(catalogue)
        req_type = random.choices(
            ["early_rich", "standard", "late_budget", "correction", "hindi_codemix", "minimal"],
            weights=[25, 25, 20, 15, 10, 5]
        )[0]
        
        brand = target["brand"]
        cat = target["category"]
        colour = target["colour"]
        size = target["size"]
        price = target["price"]
        
        # Budget ceiling slightly above product price
        budget_ceil = int(price * random.uniform(1.05, 1.35))
        # Round budget to neat 500/1000
        budget_ceil = ((budget_ceil + 499) // 500) * 500
        
        words = []
        expected_filters = {
            "category": cat,
            "brand": brand,
            "colour": colour,
            "size": size,
            "budget": budget_ceil
        }
        
        if req_type == "early_rich":
            # "Nike black running shoes size 9 under 5000"
            phrase = f"{brand} {colour} {cat} size {size} under {budget_ceil}"
            words = phrase.split()
            
        elif req_type == "standard":
            # "I want blue jeans from Levi's size 32 under 3000"
            fillers = ["looking for", "need a", "show me", "i want", "searching for"]
            lead = random.choice(fillers).split()
            phrase = f"{colour} {cat} from {brand} size {size} under {budget_ceil}"
            words = lead + phrase.split()
            
        elif req_type == "late_budget":
            # "Red hoodie Puma size M with price under 4000"
            phrase = f"{colour} {cat} {brand} size {size} with budget below {budget_ceil}"
            words = phrase.split()
            
        elif req_type == "correction":
            # Mid-request correction: "Nike red no wait black running shoes size 9 under 5000"
            other_colour = random.choice([c for c in COLOURS if c != colour])
            correct_triggers = ["no wait", "actually", "sorry i meant", "scratch that"]
            trig = random.choice(correct_triggers).split()
            lead = [brand, other_colour] + trig + [colour, cat, "size", str(size), "under", str(budget_ceil)]
            words = lead
            
        elif req_type == "hindi_codemix":
            # Code-mixed query: "Mujhe Nike kaala running shoes size nau chahiye under 5000"
            h_col = HINDI_COLOURS.get(colour, colour)
            h_size = HINDI_NUMBERS.get(str(size), str(size))
            phrase = f"mujhe {brand} {h_col} {cat} size {h_size} chahiye under {budget_ceil}"
            words = phrase.split()
            
        elif req_type == "minimal":
            phrase = f"{brand} {colour} {cat} {size}"
            expected_filters["budget"] = None
            words = phrase.split()
            
        dev_records.append({
            "request_id": f"REQ_{i+1:03d}",
            "type": req_type,
            "target_product_id": target["id"],
            "target_title": target["title"],
            "words": words,
            "full_text": " ".join(words),
            "expected_filters": expected_filters
        })
        
    return dev_records

def main():
    prods = generate_catalogue(1000)
    with open("catalogue.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "category", "brand", "colour", "size", "price", "stock", "usage", "image_url"])
        writer.writeheader()
        writer.writerows(prods)
    print(f"Generated catalogue.csv with {len(prods)} products.")
    
    devs = generate_dev_set(prods, 320)
    with open("dev.jsonl", "w", encoding="utf-8") as f:
        for item in devs:
            f.write(json.dumps(item) + "\n")
    print(f"Generated dev.jsonl with {len(devs)} evaluation requests.")

if __name__ == "__main__":
    main()
