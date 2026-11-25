"""
app/voice_layer.py - Accessibility Voice Interface & Dialog Manager
Processes natural voice commands, generates spoken response scripts,
and handles audio confirmation flows for visually impaired and motor-impaired users.
"""
import re
from typing import Dict, Any, Optional, List
from app.descriptions import get_description_service

class VoiceDialogManager:
    def __init__(self):
        self.desc_service = get_description_service()

    def get_welcome_script(self, user_name: str = "Shopper") -> str:
        return (
            f"Welcome to AnticipateCart Accessibility Mode, {user_name}. "
            "Our anticipatory voice assistant is ready. "
            "Speak what you want to buy, and we will find it before you even finish speaking. "
            "You can also say 'add to cart', 'view cart', or 'place order' at any time."
        )

    def format_search_results_speech(self, results: List[Dict[str, Any]], max_items: int = 3) -> str:
        if not results:
            return "No matching products were found in the catalogue. Please try another search or different colour and size."
            
        speech_parts = [f"Found {len(results)} matching products. Here are the top items:"]
        for idx, item in enumerate(results[:max_items], 1):
            p = item.get("product", item)
            announcement = self.desc_service.format_accessibility_announcement(p)
            speech_parts.append(f"Option {idx}: {announcement}")
            
        speech_parts.append("To select, say 'add option 1 to cart', or speak another search.")
        return " ".join(speech_parts)

    def parse_voice_command(self, transcript: str) -> Dict[str, Any]:
        """
        Parses spoken voice input into structured intents:
        - SEARCH
        - SELECT_ITEM
        - ADD_TO_CART
        - VIEW_CART
        - CHECKOUT
        - CONFIRM_ORDER
        - CANCEL
        - HELP
        """
        text = transcript.lower().strip()
        
        # Confirmation intents
        if text in ["yes", "confirm", "yes confirm", "place order now", "agree", "proceed", "haan"]:
            return {"intent": "CONFIRM_ORDER"}
        if text in ["no", "cancel", "stop", "back", "nahi"]:
            return {"intent": "CANCEL"}
            
        # Cart / Checkout intents
        if any(kw in text for kw in ["place order", "checkout", "order now", "buy now"]):
            return {"intent": "CHECKOUT"}
        if any(kw in text for kw in ["view cart", "show cart", "open cart", "my cart"]):
            return {"intent": "VIEW_CART"}
            
        # Add to cart: "add to cart", "add option 1 to cart", "add item 2 to cart"
        m_add = re.search(r"\badd\s+(?:(?:option|item|number)\s*(\d+)|this|that)?\s*(?:in\s*to|to)\s*cart\b", text)
        if m_add or "cart mein dalo" in text or text.startswith("add to cart"):
            item_index = 1
            if m_add and m_add.group(1):
                item_index = int(m_add.group(1))
            else:
                m_num = re.search(r"(?:option|item|number)\s*(\d+)", text)
                if m_num:
                    item_index = int(m_num.group(1))
            return {"intent": "ADD_TO_CART", "item_index": item_index}
            
        # Select item
        m_sel = re.search(r"(?:select|open|show)\s+(?:option|item)?\s*(\d+)", text)
        if m_sel:
            return {"intent": "SELECT_ITEM", "item_index": int(m_sel.group(1))}
            
        # Help
        if any(kw in text for kw in ["help", "what can i say", "commands"]):
            return {"intent": "HELP"}
            
        # Default: Search query
        cleaned_search = re.sub(r"^(?:search for|find|look for|show me|mujhe chahiye)\s+", "", text)
        return {"intent": "SEARCH", "query": cleaned_search}

_voice_manager = None

def get_voice_manager() -> VoiceDialogManager:
    global _voice_manager
    if _voice_manager is None:
        _voice_manager = VoiceDialogManager()
    return _voice_manager
