"""
tests/test_pipeline.py - Comprehensive Unit & Integration Test Suite
Validates Part A Core Anticipatory Engine and Part B Extra Features.
"""
import pytest
from app.predictor import predict_filters_streaming, extract_budget, compute_overall_confidence
from app.commit_policy import CommitPolicyEngine
from app.corrections import resolve_corrections
from app.spell_corrector import get_spell_corrector
from app.search_adapter import get_search_service, LocalSearchAdapter
from app.voice_layer import get_voice_manager
from app.notifications import subscribe_to_restock, update_product_stock_and_notify, get_user_notifications
from search import get_searcher

def test_filter_prediction_basic():
    tokens = "Nike black running shoes size 9 under 5000".split()
    res = predict_filters_streaming(tokens)
    f = res["filters"]
    assert f["category"] == "running shoes"
    assert f["brand"] == "Nike"
    assert f["colour"] == "black"
    assert f["size"] == "9"
    assert f["budget"] == 5000.0
    assert res["overall_confidence"] >= 0.85

def test_mid_request_correction():
    tokens = "Nike red no wait black running shoes size 9".split()
    res = predict_filters_streaming(tokens)
    f = res["filters"]
    assert f["colour"] == "black"
    assert f["brand"] == "Nike"
    assert f["category"] == "running shoes"
    assert f["size"] == "9"
    assert any("Retracted colour='red'" in ev for ev in res["events"])

def test_hindi_codemix():
    tokens = "mujhe Puma kaala sneakers size nau chahiye under 4000".split()
    res = predict_filters_streaming(tokens)
    f = res["filters"]
    assert f["brand"] == "Puma"
    assert f["colour"] == "black"  # from kaala
    assert f["category"] == "sneakers"
    assert f["size"] == "9"        # from nau
    assert f["budget"] == 4000.0

def test_spelling_corrector():
    sc = get_spell_corrector()
    corrected, changed, items = sc.correct_query("nikke shooz blak")
    assert changed is True
    assert "Nike" in corrected
    assert "shoes" in corrected
    assert "black" in corrected
    
    # Incomplete prefix during streaming should not be distorted
    prefix_corr, changed_prefix, _ = sc.correct_query("nik", is_streaming=True)
    assert prefix_corr == "nik"
    assert changed_prefix is False

def test_commit_policy_wait_vs_commit():
    engine = CommitPolicyEngine(threshold=0.85)
    
    # Ambiguous/partial query -> should WAIT
    partial_pred = predict_filters_streaming("Nike".split())
    eval_wait = engine.evaluate_commit(partial_pred, [{"product": {"id": "P1"}, "score": 2.0}])
    assert eval_wait["decision"] == "WAIT"
    
    # Fully qualified query with unique candidate -> should COMMIT
    full_pred = predict_filters_streaming("Nike black running shoes size 9 under 5000".split())
    eval_commit = engine.evaluate_commit(
        full_pred,
        [{"product": {"id": "P1"}, "score": 10.0}],
        consecutive_stable_count=2
    )
    assert eval_commit["decision"] == "COMMIT"

def test_search_service_fallback():
    service = get_search_service()
    res = service.search("Nike running", filters={"category": "running shoes", "colour": "black"})
    assert "results" in res
    assert len(res["results"]) > 0

def test_voice_dialog_manager():
    vm = get_voice_manager()
    # Confirm
    cmd_confirm = vm.parse_voice_command("yes confirm")
    assert cmd_confirm["intent"] == "CONFIRM_ORDER"
    
    # Checkout
    cmd_checkout = vm.parse_voice_command("place order")
    assert cmd_checkout["intent"] == "CHECKOUT"
    
    # Add to cart
    cmd_add = vm.parse_voice_command("add option 1 to cart")
    assert cmd_add["intent"] == "ADD_TO_CART"
    assert cmd_add["item_index"] == 1

def test_restock_notification_flow():
    user_id = "test_user_99"
    prod_id = "P0001"
    
    subscribe_to_restock(user_id, prod_id)
    update_res = update_product_stock_and_notify(prod_id, 20)
    assert update_res["new_stock"] == 20
    assert user_id in update_res["notified_users"]
    
    notifs = get_user_notifications(user_id)
    assert any(n["notification_type"] == "restock" for n in notifs)

if __name__ == "__main__":
    print("Running tests...")
    test_filter_prediction_basic()
    print("✓ Filter prediction passed")
    test_mid_request_correction()
    print("✓ Mid-request correction passed")
    test_hindi_codemix()
    print("✓ Hindi-English code-mix passed")
    test_spelling_corrector()
    print("✓ Spelling corrector passed")
    test_commit_policy_wait_vs_commit()
    print("✓ Commit policy passed")
    test_search_service_fallback()
    print("✓ Search service passed")
    test_voice_dialog_manager()
    print("✓ Voice dialog manager passed")
    test_restock_notification_flow()
    print("✓ Restock notification flow passed")
    print("\nALL TESTS PASSED SUCCESSFULLY! 🎯")
