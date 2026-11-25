"""
app/corrections.py - Mid-Request Corrections & Late-Added Constraints Handler
Detects retraction pivots ("no wait", "actually", "sorry i meant") and overrides earlier filters.
Also handles late-added constraints (e.g. "under 2000" appearing at the end).
"""
import re
from typing import List, Dict, Any, Tuple, Optional

CORRECTION_TRIGGERS = [
    r"\bno wait\b",
    r"\bwait no\b",
    r"\bactually\b",
    r"\bsorry i meant\b",
    r"\bsorry\b",
    r"\bscratch that\b",
    r"\bnot that\b",
    r"\binstead\b",
    r"\bnot (?P<old>\w+)\b",
]

COMPILED_TRIGGERS = [re.compile(pattern, re.IGNORECASE) for pattern in CORRECTION_TRIGGERS]

def detect_correction_segment(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Checks if a correction pivot exists in the text.
    Returns: (pre_correction_text, matched_trigger, post_correction_text)
    If no correction found, returns (None, None, None).
    """
    for trig_re in COMPILED_TRIGGERS:
        match = trig_re.search(text)
        if match:
            start, end = match.span()
            pre_text = text[:start].strip()
            trigger = match.group(0)
            post_text = text[end:].strip()
            return pre_text, trigger, post_text
    return None, None, None

def resolve_corrections(
    words: List[str],
    raw_filter_func
) -> Tuple[Dict[str, Any], Dict[str, float], List[str]]:
    """
    Processes words through correction logic.
    raw_filter_func is a callable: (text: str) -> (filters: dict, confidences: dict)
    
    Returns:
    (final_filters, final_confidences, events_logged)
    """
    text = " ".join(words)
    pre_text, trigger, post_text = detect_correction_segment(text)
    events = []
    
    if pre_text is not None and trigger is not None:
        events.append(f"Detected correction trigger '{trigger}'")
        pre_filters, pre_confs = raw_filter_func(pre_text)
        post_filters, post_confs = raw_filter_func(post_text)
        
        # Merge: start with pre_filters, then override with any filter present in post_filters
        merged_filters = dict(pre_filters)
        merged_confs = dict(pre_confs)
        
        for k, val in post_filters.items():
            if val is not None:
                if pre_filters.get(k) is not None and pre_filters.get(k) != val:
                    events.append(f"Retracted {k}='{pre_filters[k]}' -> Overridden to '{val}'")
                merged_filters[k] = val
                merged_confs[k] = post_confs.get(k, 0.9)
                
        return merged_filters, merged_confs, events
    else:
        filters, confs = raw_filter_func(text)
        return filters, confs, events
