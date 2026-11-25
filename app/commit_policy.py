"""
app/commit_policy.py - Conservative Anticipatory Commit-or-Wait Engine
Enforces high-accuracy, zero-wrong-commit policy by checking:
1. Calibrated confidence >= tunable threshold
2. Required anchor filters present (brand + category + colour/size)
3. Search result candidate uniqueness or score gap margin
4. Temporal stability across consecutive tokens
"""
from typing import Dict, Any, List, Optional
from config import config

class CommitPolicyEngine:
    def __init__(
        self,
        threshold: float = config.CONFIDENCE_THRESHOLD,
        min_score_gap: float = config.MIN_SCORE_GAP,
        min_stable_tokens: int = config.MIN_STABLE_TOKENS,
        wasted_search_limit: int = config.WASTED_SEARCH_LIMIT_PER_REQUEST
    ):
        self.threshold = threshold
        self.min_score_gap = min_score_gap
        self.min_stable_tokens = min_stable_tokens
        self.wasted_search_limit = wasted_search_limit

    def should_fire_early_search(
        self,
        prediction: Dict[str, Any],
        searches_fired_so_far: int
    ) -> bool:
        """
        Determines whether firing an early partial search is justified.
        Avoids wasting searches on non-informative prefixes (e.g., 'i', 'show me').
        Respects wasted_search_limit.
        """
        if searches_fired_so_far >= self.wasted_search_limit:
            return False

        filters = prediction.get("filters", {})
        active_filters = sum(1 for v in filters.values() if v is not None)
        overall_conf = prediction.get("overall_confidence", 0.0)

        # Trigger search if we have at least category or brand, and conf >= 0.35
        has_anchor = bool(filters.get("category") or filters.get("brand"))
        if has_anchor and active_filters >= 2 and overall_conf >= 0.35:
            return True
        if active_filters >= 3:
            return True
        return False

    def evaluate_commit(
        self,
        prediction: Dict[str, Any],
        search_results: List[Dict[str, Any]],
        previous_top_id: Optional[str] = None,
        consecutive_stable_count: int = 0,
        is_final_word: bool = False
    ) -> Dict[str, Any]:
        """
        Decides whether to COMMIT or WAIT.
        """
        overall_conf = prediction.get("overall_confidence", 0.0)
        filters = prediction.get("filters", {})
        
        # If no results returned by search, must wait or fail safe
        if not search_results:
            return {
                "decision": "WAIT",
                "reason": "Zero search results match current filter hypothesis",
                "product": None,
                "confidence": overall_conf,
                "gap": 0.0,
                "stable_count": consecutive_stable_count
            }

        top_match = search_results[0]
        top_product = top_match["product"]
        top_score = top_match["score"]

        # Calculate score gap to 2nd result
        if len(search_results) > 1:
            second_score = search_results[1]["score"]
            score_gap = round(top_score - second_score, 4)
        else:
            score_gap = 2.0  # Decisive single match

        # Track stability
        current_top_id = top_product.get("product_id") or top_product.get("id")
        if previous_top_id == current_top_id:
            stable_count = consecutive_stable_count + 1
        else:
            stable_count = 1

        # Final word fallback: if it's the end of the query, we must return the top result
        if is_final_word:
            return {
                "decision": "COMMIT",
                "reason": "Final word reached - resolving query",
                "product": top_product,
                "confidence": overall_conf,
                "gap": score_gap,
                "stable_count": stable_count
            }

        # Check threshold
        if overall_conf < self.threshold:
            return {
                "decision": "WAIT",
                "reason": f"Confidence {overall_conf:.3f} below threshold {self.threshold:.3f}",
                "product": None,
                "confidence": overall_conf,
                "gap": score_gap,
                "stable_count": stable_count
            }

        # Check required filters: category AND brand are crucial to prevent wrong commits
        has_category = bool(filters.get("category"))
        has_brand = bool(filters.get("brand"))
        has_variant = bool(filters.get("colour") or filters.get("size"))

        if not (has_category and has_brand and has_variant):
            return {
                "decision": "WAIT",
                "reason": "Awaiting essential attributes (brand + category + colour/size)",
                "product": None,
                "confidence": overall_conf,
                "gap": score_gap,
                "stable_count": stable_count
            }

        # Check stability or decisive score gap
        is_decisive = (len(search_results) == 1) or (score_gap >= self.min_score_gap)
        is_stable = (stable_count >= self.min_stable_tokens)

        if is_decisive or is_stable:
            return {
                "decision": "COMMIT",
                "reason": f"High confidence ({overall_conf:.3f}) and decisive/stable top result (gap={score_gap:.2f})",
                "product": top_product,
                "confidence": overall_conf,
                "gap": score_gap,
                "stable_count": stable_count
            }
        else:
            return {
                "decision": "WAIT",
                "reason": f"Top result candidate ambiguous (gap={score_gap:.2f} < {self.min_score_gap})",
                "product": None,
                "confidence": overall_conf,
                "gap": score_gap,
                "stable_count": stable_count
            }
