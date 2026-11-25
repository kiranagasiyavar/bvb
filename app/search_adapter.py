"""
app/search_adapter.py - Rezolve Labs Search Adapter with Resilient Local Fallback
Provides a swappable interface connecting to Rezolve Labs Semantic Product Search /
Conversational Knowledge API, with seamless automatic fallback to local search.py.
"""
import logging
import httpx
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from config import config
from search import get_searcher

logger = logging.getLogger("AnticipateCart.SearchAdapter")

class BaseSearchAdapter(ABC):
    @abstractmethod
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        pass

class LocalSearchAdapter(BaseSearchAdapter):
    """Local catalogue search implementation using search.py."""
    def __init__(self):
        self.searcher = get_searcher()

    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        raw_results = self.searcher.search(query=query, filters=filters, limit=limit)
        results = []
        for r in raw_results:
            p_obj = r["product"] if "product" in r else r
            results.append({
                "product": p_obj,
                "score": r.get("score", 1.0),
                "source": "local_catalogue_search"
            })
        return results

class RezolveSearchAdapter(BaseSearchAdapter):
    """
    Rezolve Labs Semantic Product Search Adapter.
    Interacts with the Rezolve Labs Brain API using the hackathon credit coupon / API key.
    """
    def __init__(
        self,
        api_key: str = config.REZOLVE_API_KEY,
        base_url: str = config.REZOLVE_BASE_URL,
        timeout: float = config.REZOLVE_TIMEOUT_SEC
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        if not self.api_key or self.api_key == "none":
            raise ValueError("Rezolve Labs API Key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Rezolve-Client": "AnticipateCart-v1",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "filters": filters or {},
            "top_k": limit,
            "capabilities": ["semantic_ranking", "conversational_filtering"]
        }
        
        # Real HTTP call to Rezolve Labs endpoint
        with httpx.Client(timeout=self.timeout) as client:
            endpoint = f"{self.base_url}/commerce/search"
            response = client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Format results
            items = data.get("results", [])
            formatted = []
            for item in items:
                formatted.append({
                    "product": item.get("product", {}),
                    "score": item.get("semantic_score", 1.0),
                    "source": "rezolve_labs_semantic"
                })
            return formatted

class UnifiedSearchService:
    """
    Manages search dispatching, failover, and metrics tracking.
    """
    def __init__(self):
        self.local_adapter = LocalSearchAdapter()
        self.rezolve_adapter = RezolveSearchAdapter()
        self.rezolve_available = config.REZOLVE_ENABLED and bool(config.REZOLVE_API_KEY)
        self.search_count = 0
        self.rezolve_success_count = 0
        self.fallback_count = 0

    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        self.search_count += 1
        
        # Try Rezolve Labs if enabled
        if self.rezolve_available:
            try:
                results = self.rezolve_adapter.search(query=query, filters=filters, limit=limit)
                self.rezolve_success_count += 1
                return {
                    "results": results,
                    "adapter_used": "rezolve_labs",
                    "fallback_triggered": False
                }
            except Exception as e:
                logger.warning(
                    f"[Rezolve Adapter Failover] Rezolve Labs API error: {e}. "
                    f"Seamlessly falling back to LocalCatalogueSearch."
                )
                self.fallback_count += 1
        
        # Fallback to local catalogue search
        results = self.local_adapter.search(query=query, filters=filters, limit=limit)
        return {
            "results": results,
            "adapter_used": "local_catalogue_fallback",
            "fallback_triggered": True
        }

_unified_search = None

def get_search_service() -> UnifiedSearchService:
    global _unified_search
    if _unified_search is None:
        _unified_search = UnifiedSearchService()
    return _unified_search
