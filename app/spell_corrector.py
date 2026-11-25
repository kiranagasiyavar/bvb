"""
app/spell_corrector.py - Fuzzy Vocabulary Spelling Corrector
Auto-corrects misspelled words against catalogue vocabulary using Levenshtein distance.
Includes prefix safety so partial word streaming is not prematurely distorted.
"""
import re
from typing import List, Tuple, Dict, Optional, Set
from search import get_searcher

def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes standard edit distance."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
        
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
        
    return previous_row[-1]

class CatalogueSpellCorrector:
    def __init__(self):
        self.vocabulary: Set[str] = set()
        self.canonical_map: Dict[str, str] = {}
        self.build_vocabulary()

    def build_vocabulary(self):
        searcher = get_searcher()
        self.catalogue_tokens: Set[str] = set()
        
        for p in searcher.products:
            # Add brand
            b = p["brand"].lower()
            self.vocabulary.add(b)
            self.catalogue_tokens.add(b)
            self.canonical_map[b] = p["brand"]
            for token in b.split():
                self.vocabulary.add(token)
                self.catalogue_tokens.add(token)
                
            # Add category tokens
            for token in p["category"].split():
                self.vocabulary.add(token)
                self.catalogue_tokens.add(token)
                self.canonical_map[token] = token
                
            # Add colour
            self.vocabulary.add(p["colour"])
            self.catalogue_tokens.add(p["colour"])
            self.canonical_map[p["colour"]] = p["colour"]
            
        # Common eCommerce query stopwords/words and brands
        from app.predictor import KNOWN_BRANDS
        for b in KNOWN_BRANDS:
            b_l = b.lower()
            self.vocabulary.add(b_l)
            self.catalogue_tokens.add(b_l)
            self.canonical_map[b_l] = b

        common_words = [
            "size", "under", "below", "price", "budget", "need", "want", "show", "looking",
            "searching", "shoes", "shirt", "running", "formal", "black", "white", "blue",
            "red", "green", "grey", "yellow", "navy", "brown", "for", "from", "with"
        ]
        for cw in common_words:
            self.vocabulary.add(cw)
            self.canonical_map[cw] = cw

    def correct_word(self, word: str, is_last_word_streaming: bool = False) -> Tuple[str, bool]:
        """
        Returns (corrected_word, was_corrected).
        If is_last_word_streaming is True and word is a prefix of a valid vocab word,
        we do NOT correct it (to preserve streaming partial typing).
        """
        w = word.lower().strip()
        if not w or len(w) <= 2 or w.isdigit():
            return word, False
            
        # If exact match exists, no correction needed
        if w in self.vocabulary:
            return self.canonical_map.get(w, word), False
            
        # Prefix check: if streaming and user is currently typing a known word
        if is_last_word_streaming:
            for vocab in self.vocabulary:
                if vocab.startswith(w):
                    return word, False  # Keep partial word intact
                    
        # Find best candidate with edit distance <= 2, prioritizing catalogue product tokens
        best_candidate = None
        best_dist = 3
        best_is_cat = False
        
        for vocab in self.vocabulary:
            if abs(len(vocab) - len(w)) > 2:
                continue
            dist = levenshtein_distance(w, vocab)
            is_cat = vocab in self.catalogue_tokens
            
            if dist < best_dist:
                best_dist = dist
                best_candidate = vocab
                best_is_cat = is_cat
            elif dist == best_dist:
                if is_cat and not best_is_cat:
                    best_candidate = vocab
                    best_is_cat = True
                
        if best_candidate and best_dist <= 2:
            return self.canonical_map.get(best_candidate, best_candidate), True
            
        return word, False

    def correct_query(self, query: str, is_streaming: bool = False) -> Tuple[str, bool, List[str]]:
        """
        Corrects entire query.
        Returns: (corrected_query, was_changed, list_of_corrections)
        """
        tokens = query.split()
        if not tokens:
            return query, False, []
            
        corrected_tokens = []
        corrections = []
        changed = False
        
        for i, t in enumerate(tokens):
            is_last = (i == len(tokens) - 1) and is_streaming
            c_word, was_corr = self.correct_word(t, is_last_word_streaming=is_last)
            if was_corr:
                changed = True
                corrections.append(f"'{t}' -> '{c_word}'")
            corrected_tokens.append(c_word)
            
        return " ".join(corrected_tokens), changed, corrections

_spell_corrector = None

def get_spell_corrector() -> CatalogueSpellCorrector:
    global _spell_corrector
    if _spell_corrector is None:
        _spell_corrector = CatalogueSpellCorrector()
    return _spell_corrector
