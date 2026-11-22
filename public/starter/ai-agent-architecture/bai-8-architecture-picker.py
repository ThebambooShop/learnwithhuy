# -*- coding: utf-8 -*-
"""bai-8-architecture-picker.py — Starter kit bài 8: deterministic-picker.

Pattern từ bài 8: LLM chỉ phân loại nhãn, Python compose quyết định cuối —
nhãn lạ hoặc nhãn None đều fallback về architecture mặc định (Factor 8 —
own your control flow, nối với bài 7). ARCHS ở đây là 3 architecture giả để
chạy không cần API: mỗi arch là một hàm nhận task, trả chuỗi kết quả mẫu.

Chạy:
    python bai-8-architecture-picker.py
Không có OPENAI_API_KEY -> self-test + mock demo (MockClient trả nhãn canned).
Có key -> make_client() trả client OpenAI thật, pick_architecture gọi model.
"""

import json
import os
from types import SimpleNamespace

# ============================================================
# 1) 3 architecture giả — cùng interface arch(task)
# ============================================================

def agentic_rag(task: str) -> str:
    """Giả lập notebook Agentic RAG: tự quyết khi nào cần truy vấn corpus."""
    return f"[Agentic RAG] Tự truy vấn corpus và trả lời: '{task}'"

def self_rag(task: str) -> str:
    """Giả lập notebook Self-RAG: retrieve + tự chấm trích dẫn trước khi trả lời."""
    return f"[Self-RAG] Retrieve + tự đánh giá trích dẫn cho: '{task}'"

def plan_execute_verify(task: str) -> str:
    """Giả lập notebook Plan-Execute-Verify: plan từng bước, verify khi lệch."""
    return f"[Plan-Execute-Verify] Plan -> Execute -> Verify cho: '{task}'"

ARCHS = {
    "qa_chinh_xac": self_rag,
    "nhanh_chi_phi": agentic_rag,
    "da_buoc_dai": plan_execute_verify,
}
DEFAULT_LABEL = "nhanh_chi_phi"  # fallback khi nhãn lạ — luôn có mặc định

# ============================================================
# 2) resolve_arch — hàm thuần: nhãn -> architecture (test được, không API)
# ============================================================

def resolve_arch(label):
    """Nhãn -> architecture. Nhãn lạ hoặc None -> fallback về DEFAULT_LABEL.

    Đây là điểm Python compose quyết định cuối (Factor 8): nhãn model sinh ra
    không được tin tuyệt đối, `.get(label, default)` đảm bảo không crash.
    """
    return ARCHS.get(label, ARCHS[DEFAULT_LABEL])

# ============================================================
# 3) pick_architecture — LLM chỉ phân loại, Python chọn pipeline
# ============================================================

PICK_PROMPT = (
    "Phân loại task thành đúng một nhãn: "
    "qa_chinh_xac | nhanh_chi_phi | da_buoc_dai. "
    'Chỉ trả JSON dạng {"label": "..."}.'
)

class MockClient:
    """Client giả: luôn trả cùng một nhãn canned, không gọi API.

    Giả lập đúng shape của Chat Completions:
    client.chat.completions.create(...) -> object .choices[0].message.content
    """

    def __init__(self, canned_label: str = DEFAULT_LABEL):
        self._canned = canned_label
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, **kwargs):
        content = json.dumps({"label": self._canned})
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )

def make_client():
    """Trả client thật khi OPENAI_API_KEY có sẵn, ngược lại MockClient."""
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI  # import muộn: file chạy được chưa cài openai
            return OpenAI()
        except ImportError:
            print("Chưa cài openai SDK — dùng MockClient thay thế.")
    return MockClient(canned_label=DEFAULT_LABEL)

def pick_architecture(task: str, client=None):
    """LLM phân loại nhãn; Python compose quyết định cuối.

    nhãn lạ / nhãn None / JSON không parse được -> fallback về mặc định.
    """
    if client is None:
        client = make_client()
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PICK_PROMPT},
            {"role": "user", "content": task},
        ],
    )
    try:
        label = json.loads(resp.choices[0].message.content).get("label")
    except json.JSONDecodeError:
        label = None  # model trả rác -> fallback, không crash
    return resolve_arch(label)

# ============================================================
# Self-test — không gọi API, chạy được với `python file.py` không có key
# ============================================================

def self_test() -> None:
    ok = []

    # --- Test 1: nhãn hợp lệ trả đúng architecture (so identity) ---
    assert resolve_arch("qa_chinh_xac") is ARCHS["qa_chinh_xac"]
    assert resolve_arch("nhanh_chi_phi") is ARCHS["nhanh_chi_phi"]
    assert resolve_arch("da_buoc_dai") is ARCHS["da_buoc_dai"]
    ok.append("Test 1: 3 nhãn hợp lệ -> trả đúng arch (identity)")

    # --- Test 2: nhãn lạ -> fallback về mặc định (assert identity) ---
    assert resolve_arch("arch_nghe_xin_nhieu") is ARCHS[DEFAULT_LABEL]
    assert resolve_arch("") is ARCHS[DEFAULT_LABEL]
    ok.append("Test 2: nhãn lạ -> fallback default (không crash)")

    # --- Test 3: nhãn None -> fallback ---
    assert resolve_arch(None) is ARCHS[DEFAULT_LABEL]
    ok.append("Test 3: nhãn None -> fallback default")

    # --- Bonus: pick_architecture end-to-end với MockClient (không API) ---
    arch = pick_architecture("QA nội bộ cần chính xác cao", client=MockClient("da_buoc_dai"))
    assert arch is ARCHS["da_buoc_dai"]
    arch_fallback = pick_architecture("task bất kỳ", client=MockClient("ten_khong_hop_le"))
    assert arch_fallback is ARCHS[DEFAULT_LABEL]
    ok.append("Bonus: pick_architecture + MockClient -> chọn đúng / fallback đúng")

    print("\n".join(ok))
    print("SELF-TEST PASS: 3/3 nhóm test + bonus (không gọi API)")

# ============================================================
# Mock mode — in kịch bản picker chọn nhãn + chạy arch tương ứng
# ============================================================

def mock_mode() -> None:
    line = "=" * 62
    print(line)
    print("MOCK MODE — deterministic-picker chọn architecture (không gọi API)")
    print(line)

    task = "Trả lời câu hỏi chính sách hoàn tiền từ tài liệu nội bộ"
    print(f"\nTask mẫu: {task}")

    # Kịch bản 1: model trả nhãn hợp lệ
    print('    Model trả JSON: {"label": "qa_chinh_xac"}')
    arch = pick_architecture(task, client=MockClient("qa_chinh_xac"))
    print(f"    Python chọn: {arch.__name__}")
    print(f"    {arch(task)}")

    # Kịch bản 2: model trả nhãn lạ -> Python fallback, không crash
    print("\nCùng task nhưng model trả nhãn lạ 'arch_vip_pro':")
    arch = pick_architecture(task, client=MockClient("arch_vip_pro"))
    print(f"    Python fallback về: {arch.__name__} (nhãn lạ không crash)")
    print(f"    {arch(task)}")

    print("\nBài tập: thêm 1 test case nhãn lạ cho CI (Mức 2 trong bài viết),")
    print("rồi cài picker vào DocMind (Mức 3).")

def main() -> None:
    self_test()
    mock_mode()
    if not os.getenv("OPENAI_API_KEY"):
        print("\n(Chưa có OPENAI_API_KEY — set key để pick_architecture gọi model thật.)")

if __name__ == "__main__":
    main()
