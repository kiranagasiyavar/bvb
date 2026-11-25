"""
app/notifications.py - Restock and Order Notification Engine
Manages restock subscriptions, triggers notifications on inventory updates,
and queues audio/visual alerts for Accessibility Users.
"""
import sqlite3
from typing import List, Dict, Any, Optional
from config import config

def subscribe_to_restock(user_id: str, product_id: str) -> bool:
    """Subscribes a user to be alerted when a product is restocked."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO restock_subscriptions (user_id, product_id, is_notified)
    VALUES (?, ?, 0)
    """, (user_id, product_id))
    conn.commit()
    conn.close()
    return True

def update_product_stock_and_notify(product_id: str, new_stock: int) -> Dict[str, Any]:
    """
    Admin action: updates inventory and dispatches notifications to subscribed users.
    """
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Update stock
    cursor.execute("UPDATE products SET stock = ? WHERE product_id = ?", (new_stock, product_id))
    
    # Fetch product title
    cursor.execute("SELECT title FROM products WHERE product_id = ?", (product_id,))
    prod_row = cursor.fetchone()
    title = prod_row["title"] if prod_row else product_id
    
    # 2. If stock > 0, find subscribed users
    notified_users = []
    if new_stock > 0:
        cursor.execute("""
        SELECT DISTINCT user_id FROM restock_subscriptions
        WHERE product_id = ? AND is_notified = 0
        """, (product_id,))
        subs = cursor.fetchall()
        
        for sub in subs:
            u_id = sub["user_id"]
            notified_users.append(u_id)
            cursor.execute("""
            INSERT INTO notifications (user_id, title, message, notification_type, is_read, is_spoken)
            VALUES (?, ?, ?, 'restock', 0, 0)
            """, (
                u_id,
                "Restock Alert!",
                f"{title} is now back in stock with {new_stock} units available!"
            ))
            
        cursor.execute("UPDATE restock_subscriptions SET is_notified = 1 WHERE product_id = ?", (product_id,))
        
    conn.commit()
    conn.close()
    
    return {
        "product_id": product_id,
        "new_stock": new_stock,
        "notified_user_count": len(notified_users),
        "notified_users": notified_users
    }

def get_user_notifications(user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
    """Retrieves notifications for a given user."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM notifications WHERE user_id = ?"
    if unread_only:
        query += " AND is_read = 0"
    query += " ORDER BY created_at DESC LIMIT 20"
    
    cursor.execute(query, (user_id,))
    rows = cursor.fetchall()
    
    results = [dict(r) for r in rows]
    conn.close()
    return results

def mark_notification_spoken(notification_id: int):
    """Marks a notification as spoken so speech engine does not repeat it."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_spoken = 1 WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()
