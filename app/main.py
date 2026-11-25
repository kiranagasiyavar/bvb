"""
app/main.py - AnticipateCart FastAPI Application
Provides RESTful APIs, Admin Controls, and High-Speed Streaming WebSockets
for Anticipatory Product Search, Voice Dialog, Image Scan, and Restock Alerts.
"""
import json
import logging
import sqlite3
import uuid
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import os

from config import config
from app.database import init_db, get_connection
from app.predictor import predict_filters_streaming
from app.commit_policy import CommitPolicyEngine
from app.search_adapter import get_search_service
from app.spell_corrector import get_spell_corrector
from app.image_search import scan_product_image
from app.descriptions import get_description_service
from app.notifications import (
    subscribe_to_restock,
    update_product_stock_and_notify,
    get_user_notifications,
    mark_notification_spoken
)
from app.voice_layer import get_voice_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AnticipateCart")

# Initialize database
init_db()

app = FastAPI(
    title="AnticipateCart",
    description="Anticipatory E-Commerce Agent for Rezolve Labs Challenge 1",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared Services
search_service = get_search_service()
spell_corrector = get_spell_corrector()
desc_service = get_description_service()
voice_manager = get_voice_manager()

# ----------------- Models -----------------
class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = "usr_std_01"

class CartAddRequest(BaseModel):
    user_id: str
    product_id: str
    quantity: int = 1

class CheckoutRequest(BaseModel):
    user_id: str

class RestockSubscribeRequest(BaseModel):
    user_id: str
    product_id: str

class AdminStockUpdateRequest(BaseModel):
    product_id: str
    new_stock: int

class VoiceCommandRequest(BaseModel):
    user_id: str
    transcript: str

# ----------------- REST Endpoints -----------------

@app.get("/api/config")
def get_current_config():
    """Returns runtime parameters for threshold and search limits."""
    return {
        "confidence_threshold": config.CONFIDENCE_THRESHOLD,
        "wasted_search_limit": config.WASTED_SEARCH_LIMIT_PER_REQUEST,
        "min_score_gap": config.MIN_SCORE_GAP,
        "rezolve_enabled": config.REZOLVE_ENABLED,
        "rezolve_base_url": config.REZOLVE_BASE_URL
    }

@app.get("/api/users")
def list_users():
    conn = get_connection()
    users = [dict(r) for r in conn.execute("SELECT * FROM users").fetchall()]
    conn.close()
    return {"users": users}

@app.get("/api/products")
def list_products(category: Optional[str] = None, in_stock_only: bool = False, limit: int = 50):
    conn = get_connection()
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category.lower())
    if in_stock_only:
        query += " AND stock > 0"
    query += " LIMIT ?"
    params.append(limit)
    
    rows = [dict(r) for r in conn.execute(query, params).fetchall()]
    conn.close()
    return {"products": rows}

@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    p = dict(row)
    p["usage"] = desc_service.get_or_generate_usage(p)
    return {"product": p}

@app.post("/api/search")
def manual_search(req: SearchRequest):
    # Spell check
    corrected_q, was_corrected, corrections = spell_corrector.correct_query(req.query)
    effective_q = corrected_q if was_corrected else req.query
    
    # Predict filters if not provided
    filters = req.filters
    if not filters:
        pred = predict_filters_streaming(effective_q.split())
        filters = pred["filters"]
        
    res = search_service.search(query=effective_q, filters=filters, limit=12)
    
    # Format usage descriptions
    results_with_usage = []
    for item in res.get("results", []):
        p = item["product"]
        p["usage"] = desc_service.get_or_generate_usage(p)
        results_with_usage.append(item)
        
    return {
        "original_query": req.query,
        "effective_query": effective_q,
        "was_corrected": was_corrected,
        "corrections": corrections,
        "filters_applied": filters,
        "adapter_used": res.get("adapter_used"),
        "results": results_with_usage
    }

@app.post("/api/spellcheck")
def spellcheck_query(data: Dict[str, str]):
    text = data.get("query", "")
    corrected, changed, items = spell_corrector.correct_query(text)
    return {
        "original": text,
        "corrected": corrected,
        "was_changed": changed,
        "corrections": items
    }

@app.post("/api/image-search")
async def search_by_image(file: UploadFile = File(...)):
    contents = await file.read()
    result = scan_product_image(contents)
    return result

@app.get("/api/cart")
def get_cart(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.id as cart_id, c.quantity, p.*
    FROM cart_items c
    JOIN products p ON c.product_id = p.product_id
    WHERE c.user_id = ?
    """, (user_id,))
    items = [dict(r) for r in cursor.fetchall()]
    total = sum(item["price"] * item["quantity"] for item in items)
    conn.close()
    return {"items": items, "total_amount": total, "count": len(items)}

@app.post("/api/cart/add")
def add_to_cart(req: CartAddRequest):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check product exists
    cursor.execute("SELECT product_id, title, stock FROM products WHERE product_id = ?", (req.product_id,))
    prod = cursor.fetchone()
    if not prod:
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found")
        
    # Check existing cart item
    cursor.execute("SELECT id, quantity FROM cart_items WHERE user_id = ? AND product_id = ?", (req.user_id, req.product_id))
    existing = cursor.fetchone()
    if existing:
        cursor.execute("UPDATE cart_items SET quantity = quantity + ? WHERE id = ?", (req.quantity, existing["id"]))
    else:
        cursor.execute("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)", (req.user_id, req.product_id, req.quantity))
        
    conn.commit()
    conn.close()
    return {"success": True, "message": f"Added {prod['title']} to cart"}

@app.post("/api/orders/checkout")
def checkout(req: CheckoutRequest):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Fetch cart items
    cursor.execute("""
    SELECT c.quantity, p.product_id, p.price, p.title
    FROM cart_items c
    JOIN products p ON c.product_id = p.product_id
    WHERE c.user_id = ?
    """, (req.user_id,))
    items = cursor.fetchall()
    if not items:
        conn.close()
        raise HTTPException(status_code=400, detail="Cart is empty")
        
    total_amount = sum(it["price"] * it["quantity"] for it in items)
    order_id = f"ORD_{uuid.uuid4().hex[:8].upper()}"
    
    cursor.execute("INSERT INTO orders (id, user_id, total_amount, status) VALUES (?, ?, ?, 'CONFIRMED')", (order_id, req.user_id, total_amount))
    cursor.execute("DELETE FROM cart_items WHERE user_id = ?", (req.user_id,))
    
    # Create notification
    cursor.execute("""
    INSERT INTO notifications (user_id, title, message, notification_type, is_read, is_spoken)
    VALUES (?, 'Order Confirmed!', ?, 'order', 0, 0)
    """, (req.user_id, f"Order {order_id} placed successfully for ₹{int(total_amount):,}!"))
    
    conn.commit()
    conn.close()
    return {"success": True, "order_id": order_id, "total_amount": total_amount}

@app.get("/api/notifications")
def list_notifications(user_id: str, unread_only: bool = False):
    return {"notifications": get_user_notifications(user_id, unread_only=unread_only)}

@app.post("/api/notifications/{notification_id}/spoken")
def mark_spoken(notification_id: int):
    mark_notification_spoken(notification_id)
    return {"success": True}

@app.post("/api/restock/subscribe")
def register_restock(req: RestockSubscribeRequest):
    subscribe_to_restock(req.user_id, req.product_id)
    return {"success": True, "message": "Subscribed to restock alerts"}

# ----------------- Admin Endpoints for Live Demo -----------------

@app.post("/api/admin/stock")
def admin_update_stock(req: AdminStockUpdateRequest):
    res = update_product_stock_and_notify(req.product_id, req.new_stock)
    return {"success": True, "details": res}

@app.get("/api/admin/catalogue-summary")
def admin_catalogue_summary():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN stock = 0 THEN 1 ELSE 0 END) as out_of_stock FROM products")
    stats = dict(cursor.fetchone())
    
    # Get 10 out of stock products for demo
    cursor.execute("SELECT id, title, category, brand, price, stock FROM products WHERE stock = 0 LIMIT 10")
    oos_items = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"stats": stats, "out_of_stock_samples": oos_items}

# ----------------- Voice Dialog Endpoint -----------------

@app.post("/api/voice/command")
def process_voice_command(req: VoiceCommandRequest):
    parsed = voice_manager.parse_voice_command(req.transcript)
    intent = parsed.get("intent")
    
    spoken_response = ""
    action_data = {}
    
    if intent == "CONFIRM_ORDER":
        # Execute checkout
        try:
            order_res = checkout(CheckoutRequest(user_id=req.user_id))
            spoken_response = f"Your order {order_res['order_id']} has been placed successfully! Total amount {int(order_res['total_amount'])} Rupees."
            action_data = {"action": "order_confirmed", "order": order_res}
        except HTTPException as e:
            spoken_response = f"Could not place order: {e.detail}."
            action_data = {"error": e.detail}
            
    elif intent == "CHECKOUT":
        cart_info = get_cart(req.user_id)
        if cart_info["count"] == 0:
            spoken_response = "Your cart is currently empty. Speak a product name to search and add items."
        else:
            spoken_response = f"You have {cart_info['count']} items in your cart totaling {int(cart_info['total_amount'])} Rupees. Say yes or confirm to place this order now."
            action_data = {"action": "prompt_confirmation"}
            
    elif intent == "VIEW_CART":
        cart_info = get_cart(req.user_id)
        if cart_info["count"] == 0:
            spoken_response = "Your cart is empty."
        else:
            item_names = ", ".join(it["title"] for it in cart_info["items"])
            spoken_response = f"Your cart contains {cart_info['count']} items: {item_names}. Total is {int(cart_info['total_amount'])} Rupees. Say place order to checkout."
            action_data = {"action": "view_cart", "cart": cart_info}
            
    elif intent == "HELP":
        spoken_response = (
            "Voice assistance commands: Say the product you want to find, such as 'Nike black running shoes size 9'. "
            "Say 'add option 1 to cart', 'view cart', 'place order', or 'yes' to confirm."
        )
        action_data = {"action": "help"}
        
    else:  # SEARCH
        query = parsed.get("query", req.transcript)
        search_res = manual_search(SearchRequest(query=query, user_id=req.user_id))
        spoken_response = voice_manager.format_search_results_speech(search_res.get("results", []))
        action_data = {"action": "search_results", "search_res": search_res}

    return {
        "transcript": req.transcript,
        "intent": intent,
        "spoken_response": spoken_response,
        "action_data": action_data
    }

# ----------------- WebSocket Anticipatory Streaming Endpoint -----------------

@app.websocket("/ws/anticipate")
async def websocket_anticipate(websocket: WebSocket):
    """
    Real-time streaming anticipation endpoint.
    Client sends JSON messages:
      {"type": "token_stream", "words": ["Nike", "black", "running"]}
      {"type": "reset"}
    Server streams back real-time prediction, confidence, commit policy decisions, and product cards.
    """
    await websocket.accept()
    logger.info("WebSocket connected for anticipatory streaming session.")
    
    engine = CommitPolicyEngine(
        threshold=config.CONFIDENCE_THRESHOLD,
        min_score_gap=config.MIN_SCORE_GAP,
        min_stable_tokens=config.MIN_STABLE_TOKENS,
        wasted_search_limit=config.WASTED_SEARCH_LIMIT_PER_REQUEST
    )
    
    searches_fired = 0
    cached_results = []
    last_searched_filters = None
    previous_top_id = None
    stable_count = 0
    committed = False
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "token_stream")
            
            if msg_type == "reset":
                searches_fired = 0
                cached_results = []
                last_searched_filters = None
                previous_top_id = None
                stable_count = 0
                committed = False
                await websocket.send_json({"type": "reset_ack"})
                continue
                
            words = data.get("words", [])
            is_final = data.get("is_final", False)
            
            if not words:
                continue
                
            # 1. Filter prediction & confidence calculation
            prediction = predict_filters_streaming(words)
            curr_filters = prediction["filters"]
            
            # 2. Check if early search should be fired
            filters_changed = (curr_filters != last_searched_filters)
            should_search = (filters_changed and engine.should_fire_early_search(prediction, searches_fired)) or is_final
            
            adapter_used = "cached"
            if should_search:
                search_out = search_service.search(
                    query=" ".join(words),
                    filters=curr_filters,
                    limit=6
                )
                cached_results = search_out.get("results", [])
                adapter_used = search_out.get("adapter_used", "local")
                last_searched_filters = dict(curr_filters)
                searches_fired += 1
                
            # 3. Evaluate commit-or-wait policy
            commit_eval = engine.evaluate_commit(
                prediction=prediction,
                search_results=cached_results,
                previous_top_id=previous_top_id,
                consecutive_stable_count=stable_count,
                is_final_word=is_final
            )
            
            # Pre-commit verification search: ensures cached results reflect current filters
            if commit_eval["decision"] == "COMMIT" and curr_filters != last_searched_filters:
                search_out = search_service.search(
                    query=" ".join(words),
                    filters=curr_filters,
                    limit=6
                )
                cached_results = search_out.get("results", [])
                adapter_used = search_out.get("adapter_used", "local")
                last_searched_filters = dict(curr_filters)
                searches_fired += 1
                commit_eval = engine.evaluate_commit(
                    prediction=prediction,
                    search_results=cached_results,
                    previous_top_id=previous_top_id,
                    consecutive_stable_count=stable_count,
                    is_final_word=is_final
                )
                
            if cached_results:
                top_p = cached_results[0]["product"]
                previous_top_id = top_p.get("product_id") or top_p.get("id")
                stable_count = commit_eval.get("stable_count", 1)
                
            # Format product usage on top matches
            for item in cached_results:
                p = item["product"]
                if "usage" not in p or not p["usage"]:
                    p["usage"] = desc_service.get_or_generate_usage(p)
                    
            committed_product = commit_eval.get("product")
            if commit_eval["decision"] == "COMMIT" and not committed:
                committed = True
                
            # Spoken announcement for accessibility mode
            spoken_line = ""
            if committed_product:
                spoken_line = desc_service.format_accessibility_announcement(committed_product)
                
            response_payload = {
                "type": "anticipation_update",
                "word_count": len(words),
                "words": words,
                "text_so_far": " ".join(words),
                "filters": curr_filters,
                "confidences": prediction["confidences"],
                "overall_confidence": prediction["overall_confidence"],
                "decision": commit_eval["decision"],
                "reason": commit_eval["reason"],
                "score_gap": commit_eval.get("gap", 0.0),
                "stable_count": stable_count,
                "searches_fired": searches_fired,
                "adapter_used": adapter_used,
                "committed_product": committed_product,
                "search_results": cached_results[:6],
                "spoken_line": spoken_line,
                "events": prediction.get("events", [])
            }
            
            await websocket.send_json(response_payload)
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

# Mount static frontend files
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "AnticipateCart Backend Running. Static index.html loading."}
