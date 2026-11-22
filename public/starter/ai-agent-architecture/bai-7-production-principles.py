# -*- coding: utf-8 -*-
"""bai-7-production-principles.py — Starter kit bài 7: 12 nguyên lý production.

Ba mảnh logic đắt giá nhất của bài, viết thành hàm thuần để self-test chạy
không cần API key:

1. reducer + idempotency (Factor 12): event trùng id bị bỏ qua khi replay —
   chống tác dụng phụ lặp (hoàn tiền hai lần).
2. dispatch qua dict TOOL_HANDLERS (Factor 1 + Factor 8): mọi tool call —
   kể cả tool lạ — đều sinh ra một tool result chuỗi, không raise.
3. eval_trace: chấm trace bằng Python thuần, chạy trong CI được.

Chạy:
    python bai-7-production-principles.py
Không có OPENAI_API_KEY -> self-test + mock demo (ask_human trả "approve").
Phần gọi API thật (client.chat.completions) nằm trong bài viết; logic thuần
ở đây là phần bạn giữ trong code của mình và test được (Factor 8).
"""

import json
import os

# ============================================================
# 1) Stateless reducer + idempotency (Factor 12)
# ============================================================

def initial_state() -> dict:
    """State ban đầu: events, seen_ids, step, status — đủ để replay từ đầu."""
    return {"events": [], "seen_ids": [], "step": 0, "status": "idle"}

def reducer(state: dict, event: dict) -> dict:
    """Hàm thuần + idempotency: state hiện tại + 1 event -> state mới.

    Event đã xử lý (id có trong seen_ids) thì bỏ qua khi replay — replay
    không tạo tác dụng phụ lần hai. Không đụng biến ngoài, không side effect.
    """
    if event.get("id") in state.get("seen_ids", []):
        return state  # replay không tạo tác dụng phụ lần hai
    new = dict(state)
    new["events"] = state["events"] + [event]
    new["seen_ids"] = state.get("seen_ids", []) + [event["id"]]
    new["step"] = state["step"] + 1
    kind = event.get("kind")
    if kind == "tool_call":
        new["status"] = "running"
    elif kind == "approval":
        new["status"] = "approved" if event["approved"] else "rejected"
    elif kind == "done":
        new["status"] = "completed"
    return new

def drive(events: list, target: str = "completed") -> dict:
    """Driver: chạy reducer qua danh sách events tới trạng thái mục tiêu.

    Resume = gọi lại đúng hàm này với đúng danh sách events — state không
    nằm trong RAM của process nào (Factor 6 ghép Factor 12).
    """
    state = initial_state()
    for ev in events:
        state = reducer(state, ev)
        if state["status"] == target:
            break
    return state

# ============================================================
# 2) Dispatch tool qua dict TOOL_HANDLERS (Factor 1 + Factor 8)
# ============================================================

def ask_human_mock(question: str) -> str:
    """Mock của ask_human: trả "approve" luôn.

    Bản thật của Factor 7 KHÔNG dùng input(): đẩy notification + chờ approval
    qua queue, ghi event approval_requested vào store, đánh dấu state
    awaiting_approval — process chết vẫn resume được khi duyệt xong.
    """
    print(f"[CHỜ DUYỆT] {question}")
    return "approve"

def _handle_ask_human(args: dict) -> str:
    return ask_human_mock(args.get("question", ""))

def _handle_lookup_order(args: dict) -> str:
    # Tool mẫu: tra đơn hàng — trả chuỗi result như một API call thật
    return f"order_{args.get('order_id', 'unknown')}"

# Thêm tool mới chỉ là thêm một entry vào dict, không đụng dispatch
TOOL_HANDLERS = {
    "ask_human": _handle_ask_human,
    "lookup_order": _handle_lookup_order,
}

def dispatch(name: str, raw_arguments: str) -> str:
    """Mọi tool call đều trả một tool result chuỗi — kể cả tool lạ.

    dispatch không raise: lỗi là dữ liệu append vào context (Factor 9).
    Thiếu tool result cho một tool call là protocol error ở lượt sau.
    """
    try:
        args = json.loads(raw_arguments) if raw_arguments else {}
    except json.JSONDecodeError as exc:
        return f"Lỗi: arguments của '{name}' không parse được JSON ({exc})."
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return f"Lỗi: tool '{name}' không có handler trong TOOL_HANDLERS."
    try:
        return str(handler(args))
    except Exception as exc:  # handler lỗi vẫn sinh tool result để loop tiếp
        return f"Lỗi: handler '{name}' raise {type(exc).__name__}: {exc}"

def tool_result(call_id: str, content: str) -> dict:
    """Đóng gói tool result đúng cấu trúc để append vào context."""
    return {"role": "tool", "tool_call_id": call_id, "content": content}

# ============================================================
# 3) eval_trace — chấm trace bằng Python thuần
# ============================================================

def eval_trace(actual_steps: list, expected_steps: list) -> dict:
    """So khớp chuỗi step với ground truth.

    score: tỉ lệ step khớp đúng vị trí (đếm theo zip, dừng ở list ngắn hơn).
    order_ok: phần đầu của actual có khớp đúng thứ tự expected — step dư
    ở cuối không bị phạt.
    """
    hits = sum(1 for a, e in zip(actual_steps, expected_steps) if a == e)
    return {
        "score": hits / max(len(expected_steps), 1),
        "order_ok": actual_steps[:len(expected_steps)] == expected_steps,
    }

# ============================================================
# Self-test — không gọi API, chạy được với `python file.py` không có key
# ============================================================

def self_test() -> None:
    ok = []

    # --- Test 1: replay cùng events 2 lần -> state giống hệt nhau ---
    events = [
        {"id": "ev1", "kind": "tool_call", "name": "lookup_order", "args": {"order_id": "42"}, "result": "order_42"},
        {"id": "ev2", "kind": "approval", "approved": True},
        {"id": "ev3", "kind": "done"},
    ]
    s1 = drive(events)
    s2 = drive(events)
    assert s1 == s2, "replay cùng events phải cho state giống hệt nhau"
    assert s1["status"] == "completed" and s1["step"] == 3
    ok.append("Test 1: replay cùng events 2 lần -> state giống hệt nhau")

    # --- Test 2: event trùng id xuất hiện 2 lần -> chỉ tính MỘT lần ---
    # Event trùng đặt ĐẦU danh sách để drive không break sớm tại "done"
    duplicated = [events[0]] + events
    s3 = drive(duplicated)
    assert len(s3["events"]) == 3, f"event trùng id phải bị bỏ qua (thấy {len(s3['events'])})"
    assert s3["seen_ids"] == ["ev1", "ev2", "ev3"]
    assert s3["step"] == 3
    # Sau khi state đã completed, replay tiếp event cũ vẫn là no-op
    assert reducer(s1, events[0]) is s1, "event đã processed phải là no-op khi replay"
    ok.append("Test 2: event trùng id -> state chỉ tính một lần (idempotency)")

    # --- Test 3: dispatch tool lạ / JSON hỏng -> chuỗi lỗi, không raise ---
    err_unknown = dispatch("send_sms", json.dumps({"to": "+84xxx"}))
    assert isinstance(err_unknown, str) and "không có handler" in err_unknown
    err_bad_json = dispatch("ask_human", "{không phải json")
    assert isinstance(err_bad_json, str) and "JSON" in err_bad_json
    err_ok = dispatch("ask_human", json.dumps({"question": "Duyệt hoàn 7 triệu cho đơn 42?"}))
    assert err_ok == "approve"
    ok.append("Test 3: dispatch tool lạ / JSON hỏng -> chuỗi lỗi, không raise")

    # --- Test 4: eval_trace đúng score/order_ok trên case cứng ---
    expected = ["tìm đơn", "hỏi duyệt", "hoàn tiền"]
    # Case cứng 1: dư step ở cuối -> order_ok True, score vẫn 1.0
    r1 = eval_trace(["tìm đơn", "hỏi duyệt", "hoàn tiền", "gửi email"], expected)
    assert r1 == {"score": 1.0, "order_ok": True}
    # Case cứng 2: thứ tự sai hai step đầu -> chỉ 1 hit, order_ok False
    r2 = eval_trace(["hỏi duyệt", "tìm đơn", "hoàn tiền"], expected)
    assert abs(r2["score"] - 1 / 3) < 1e-9 and r2["order_ok"] is False
    # Case cứng 3: actual rỗng -> score 0, order_ok False
    r3 = eval_trace([], expected)
    assert r3 == {"score": 0.0, "order_ok": False}
    ok.append("Test 4: eval_trace score/order_ok đúng trên case cứng")

    print("\n".join(ok))
    print("SELF-TEST PASS: 4/4 nhóm test (không gọi API)")

# ============================================================
# Mock mode — in kịch bản approval + replay demo
# ============================================================

def mock_mode() -> None:
    line = "=" * 62
    print(line)
    print("MOCK MODE — kịch bản approval + replay reducer (không gọi API)")
    print(line)

    # Kịch bản 1: agent gọi ask_human qua dispatch — mock trả "approve"
    print("\n[1] Agent gọi tool ask_human (mock, không dùng input()):")
    answer = dispatch("ask_human", json.dumps({"question": "Duyệt hoàn 7 triệu cho đơn 42?"}))
    print(f"    tool result: {tool_result('call_1', answer)}")

    # Kịch bản 2: model gọi tool lạ — vẫn có tool result, không sập loop
    print("\n[2] Agent gọi tool lạ 'send_sms' (không có handler):")
    result = dispatch("send_sms", json.dumps({"to": "+84xxx", "text": "xin chao"}))
    print(f"    tool result: {tool_result('call_2', result)}")

    # Kịch bản 3: replay reducer — chạy 2 lần, state như cũ
    events = [
        {"id": "ev1", "kind": "tool_call", "name": "lookup_order", "args": {"order_id": "42"}, "result": "order_42"},
        {"id": "ev2", "kind": "approval", "approved": True},
        {"id": "ev3", "kind": "done"},
    ]
    print("\n[3] Replay reducer:")
    print("    events: ev1 tool_call lookup_order | ev2 approval | ev3 done")
    state_a = drive(events)
    state_b = drive(events)
    print(f"    drive() lần 1: status={state_a['status']}, step={state_a['step']}")
    print(f"    drive() lần 2 (replay): status={state_b['status']}, step={state_b['step']}")
    mark = "✓" if state_a == state_b else "✗"
    print(f"    {mark} state sau 2 lần chạy giống hệt nhau — replay an toàn")

    # Kịch bản 4: idempotency — event trùng id bị bỏ qua
    state_c = drive([events[0]] + events)
    mark = "✓" if len(state_c["events"]) == 3 else "✗"
    print(f"    {mark} event trùng id bị bỏ qua: {len(state_c['events'])} events, không tính hai lần")

    print("\nBài tập: chuyển agent loop bài 1 thành reducer này; thêm test event")
    print("trùng id vào CI (Mức 3 trong bài viết).")

def main() -> None:
    self_test()
    mock_mode()
    if not os.getenv("OPENAI_API_KEY"):
        print("\n(Chưa có OPENAI_API_KEY — file vẫn chạy hết: mọi hàm ở đây đều thuần.)")

if __name__ == "__main__":
    main()
