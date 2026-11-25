"""
replace_dataset.py - Ingests official Rezolve Labs Challenge 1 dataset (1,074 products)
Adds high-definition curated product images, stock numbers, and rebuilds SQLite.
"""
import csv
import json
import os
import random
import sqlite3
import shutil

random.seed(42)

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
    "sandals": [
        "https://images.unsplash.com/photo-1603808033192-082d6919d3e1?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1562273138-f46be4ebdf33?auto=format&fit=crop&w=600&q=80"
    ],
    "backpacks": [
        "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?auto=format&fit=crop&w=600&q=80"
    ],
    "caps": [
        "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1575428652377-a2d80e2277fc?auto=format&fit=crop&w=600&q=80"
    ],
    "dresses": [
        "https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?auto=format&fit=crop&w=600&q=80"
    ],
    "headphones": [
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=600&q=80"
    ],
    "hoodies": [
        "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1509967419530-da38b4704bc6?auto=format&fit=crop&w=600&q=80"
    ],
    "jackets": [
        "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1548883354-7622d03aca27?auto=format&fit=crop&w=600&q=80"
    ],
    "jeans": [
        "https://images.unsplash.com/photo-1542272604-780c96856592?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?auto=format&fit=crop&w=600&q=80"
    ],
    "kurtas": [
        "https://images.unsplash.com/photo-1583391733956-3750e0ff4e8b?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1607345366928-199ea26cfe3e?auto=format&fit=crop&w=600&q=80"
    ],
    "shirts": [
        "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?auto=format&fit=crop&w=600&q=80"
    ],
    "t-shirts": [
        "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1576566588028-4147f3842f27?auto=format&fit=crop&w=600&q=80"
    ],
    "track pants": [
        "https://images.unsplash.com/photo-1517445312882-bc9910d016b7?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1552902865-b72c031ac5ea?auto=format&fit=crop&w=600&q=80"
    ],
    "wallets": [
        "https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1606503837948-433054fecf79?auto=format&fit=crop&w=600&q=80"
    ],
    "watches": [
        "https://images.unsplash.com/photo-1524805444758-089113d48a6d?auto=format&fit=crop&w=600&q=80",
        "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=600&q=80"
    ]
}

def get_image_url(category, idx):
    cat_imgs = CATEGORY_IMAGES.get(category, [
        "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80"
    ])
    return cat_imgs[idx % len(cat_imgs)]

def main():
    src_dir = "official_starter/ps1-anticipatory-commerce"
    
    # 1. Read official catalogue
    with open(f"{src_dir}/catalogue.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        orig_products = list(reader)
        
    print(f"Loaded {len(orig_products)} products from official catalogue.csv")
    
    # 2. Add images and stock to products
    enriched_products = []
    fieldnames = ["product_id", "title", "brand", "category", "colour", "size", "price", "description", "stock", "image_url"]
    
    for idx, p in enumerate(orig_products):
        cat = p["category"]
        img = get_image_url(cat, idx)
        # ~8% out of stock for restock alert demos
        stock = 0 if random.random() < 0.08 else random.randint(5, 45)
        
        enriched = dict(p)
        enriched["stock"] = stock
        enriched["image_url"] = img
        enriched_products.append(enriched)
        
    # Write enriched catalogue.csv to root
    with open("catalogue.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched_products)
    print("Wrote enriched catalogue.csv with image_url and stock.")
    
    # Copy dev.jsonl, search.py, evaluate.py
    shutil.copy(f"{src_dir}/dev.jsonl", "dev.jsonl")
    shutil.copy(f"{src_dir}/search.py", "search.py")
    shutil.copy(f"{src_dir}/evaluate.py", "evaluate.py")
    print("Copied official dev.jsonl, search.py, evaluate.py.")
    
    # Rebuild SQLite Database
    db_path = "anticipatecart.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Users
    cursor.execute("""
    CREATE TABLE users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL,
        user_type TEXT NOT NULL,
        speech_rate REAL DEFAULT 1.0,
        font_size TEXT DEFAULT 'normal',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.executemany("INSERT INTO users (id, username, display_name, user_type) VALUES (?, ?, ?, ?)", [
        ("usr_std_01", "standard_user", "Alex Johnson", "standard"),
        ("usr_acc_01", "accessibility_user", "Samira Khan", "accessibility"),
        ("usr_admin", "admin", "Store Administrator", "standard")
    ])
    
    # Products
    cursor.execute("""
    CREATE TABLE products (
        product_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        brand TEXT NOT NULL,
        category TEXT NOT NULL,
        colour TEXT NOT NULL,
        size TEXT,
        price REAL NOT NULL,
        description TEXT,
        stock INTEGER NOT NULL,
        image_url TEXT
    )
    """)
    
    batch = []
    for p in enriched_products:
        batch.append((
            p["product_id"], p["title"], p["brand"], p["category"],
            p["colour"], p.get("size", ""), float(p["price"]),
            p.get("description", ""), int(p["stock"]), p["image_url"]
        ))
        
    cursor.executemany("""
    INSERT INTO products (product_id, title, brand, category, colour, size, price, description, stock, image_url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, batch)
    
    # Restock subscriptions
    cursor.execute("""
    CREATE TABLE restock_subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        is_notified INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Notifications
    cursor.execute("""
    CREATE TABLE notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        notification_type TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        is_spoken INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Cart items
    cursor.execute("""
    CREATE TABLE cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        quantity INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Orders
    cursor.execute("""
    CREATE TABLE orders (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'CONFIRMED',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()
    print("Rebuilt SQLite anticipatecart.db with all 1,074 official products.")

if __name__ == "__main__":
    main()
