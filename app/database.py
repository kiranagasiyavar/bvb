"""
app/database.py - SQLite Database Management
Handles schemas for users, product stock, restock notifications, cart, and orders.
"""
import sqlite3
import os
import csv
from typing import List, Dict, Any, Optional
from config import config

DB_PATH = config.DATABASE_PATH
CATALOGUE_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "catalogue.csv")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL,
        user_type TEXT NOT NULL, -- 'standard' or 'accessibility'
        speech_rate REAL DEFAULT 1.0,
        font_size TEXT DEFAULT 'normal',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Products Table (mirrors catalogue.csv with mutable stock)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        brand TEXT NOT NULL,
        colour TEXT NOT NULL,
        size TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        usage TEXT,
        image_url TEXT
    )
    """)
    
    # 3. Restock Subscriptions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restock_subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        is_notified INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)
    
    # 4. In-App & Spoken Notifications
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        notification_type TEXT NOT NULL, -- 'restock', 'order', 'info'
        is_read INTEGER DEFAULT 0,
        is_spoken INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    # 5. Search History
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        query TEXT NOT NULL,
        predicted_filters TEXT,
        committed_product_id TEXT,
        earliness_words INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 6. Cart & Orders
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        quantity INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'CONFIRMED',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    # Seed default users
    cursor.execute("SELECT COUNT(*) as cnt FROM users")
    if cursor.fetchone()["cnt"] == 0:
        cursor.executemany("""
        INSERT INTO users (id, username, display_name, user_type) VALUES (?, ?, ?, ?)
        """, [
            ("usr_std_01", "standard_user", "Alex Johnson", "standard"),
            ("usr_acc_01", "accessibility_user", "Samira Khan", "accessibility"),
            ("usr_admin", "admin", "Store Administrator", "standard")
        ])
        
    # Sync products from catalogue.csv if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM products")
    if cursor.fetchone()["cnt"] == 0 and os.path.exists(CATALOGUE_CSV):
        with open(CATALOGUE_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append((
                    row["id"], row["title"], row["category"],
                    row["brand"], row["colour"], row["size"],
                    float(row["price"]), int(row["stock"]), row.get("usage", ""),
                    row.get("image_url", "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80")
                ))
            cursor.executemany("""
            INSERT INTO products (id, title, category, brand, colour, size, price, stock, usage, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
