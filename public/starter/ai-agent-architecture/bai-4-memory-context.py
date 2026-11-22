"""bai-4 — Memory và Context Engineering: agent nhớ được gì, bỏ quên gì.

Chạy được hai chế độ, chọn tự động theo OPENAI_API_KEY:

- Mock mode (không có key): demo MemoryManager (add / retrieve / compact)
  và kịch bản compaction giảm token — kèm self-test assert hành vi cốt lõi.
- Live mode (có key): tóm tắt hội thoại bằng model thật như trong bài viết.

Bài viết: /bai-viet/agent-memory-va-context-engineering
"""
import os
import time
from dataclasses import dataclass, field

MOCK = not os.getenv("OPENAI_API_KEY")  # có key -> live, không có -> mock
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

RECENT_KEEP = 6        # số lượt gần nhất giữ nguyên khi compaction
COMPACT_TRIGGER = 16   # tổng lượt chạm mốc này thì nén


# ============ Hàm thuần dùng chung cho cả hai chế độ ============

def estimate_tokens(messages: list[dict]) -> int:
    """Xấp xỉ ~4 ký tự/token + 8 overhead — chỉ dùng để so sánh tương đối."""
    return sum(len(m["content"]) // 4 + 8 for m in messages)


def split_history(messages: list[dict], keep: int = RECENT_KEEP) -> tuple[list[dict], list[dict]]:
    """Tách lịch sử thành (old, recent) — hàm thuần, không gọi API.

    Tách riêng để self-test được: old + recent khớp thứ tự gốc,
    recent nguyên vẹn từng message.
    """
    if keep >= len(messages):
        return [], list(messages)
    return messages[:-keep], messages[-keep:]


def compact_messages(messages: list[dict], summarize) -> list[dict]:
    """Nén lịch sử cũ thành một message tóm tắt, giữ nguyên lượt gần nhất."""
    old, recent = split_history(messages)
    if not old:
        return messages
    summary = summarize(old)
    return [{"role": "system", "content": f"[Tóm tắt hội thoại trước đó]\n{summary}"}, *recent]


# ============ Phân tầng memory: MemoryManager (không framework) ============

@dataclass
class MemoryItem:
    text: str
    kind: str  # "event" | "fact"
    created: float = field(default_factory=time.time)


class MemoryManager:
    """Memory trong bộ nhớ, không framework: add / retrieve / compact."""

    def __init__(self, max_items: int = 50):
        self.items: list[MemoryItem] = []
        self.max_items = max_items

    # --- ghi: event là lượt xảy ra, fact là kiến thức bền ---
    def add(self, text: str, kind: str = "event") -> None:
        self.items.append(MemoryItem(text=text, kind=kind))
        if len(self.items) > self.max_items:
            self.compact()

    # --- đọc: keyword scoring cộng recency decay ---
    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        terms = {t for t in query.lower().split() if len(t) > 2}
        scored = []
        for item in self.items:
            words = item.text.lower().split()
            overlap = sum(1 for t in terms if t in words)
            if overlap == 0:
                continue
            recency = 1.0 / (time.time() - item.created + 1)
            scored.append((overlap + recency, item))
        scored.sort(key=lambda pair: -pair[0])
        return [i.text for _, i in scored[:top_k]]

    # --- nén: gộp nửa event cũ thành một fact ---
    def compact(self) -> None:
        events = [i for i in self.items if i.kind == "event"]
        if len(events) < 2:
            return
        old, kept = events[:len(events) // 2], events[len(events) // 2:]
        others = [i for i in self.items if i.kind != "event"]
        fact = MemoryItem(text=" | ".join(i.text for i in old), kind="fact")
        self.items = [fact, *kept, *others]


# ============ LIVE MODE (cần OPENAI_API_KEY) ============

if not MOCK:
    from openai import OpenAI

    client = OpenAI()  # đọc OPENAI_API_KEY từ env

    def summarize_llm(old: list[dict]) -> str:
        # Instruction tóm tắt PHẢI ghi rõ giữ nguyên con số, tên riêng, mã đơn —
        # mất "giá 12 triệu" hay "hạn 30/12" là mất thông tin người dùng.
        return client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": (
                    "Tóm tắt hội thoại dưới đây thành tối đa 10 gạch đầu dòng. "
                    "Giữ NGUYÊN: con số, tên riêng, mã đơn, ràng buộc người dùng đã đưa."
                )},
                {"role": "user", "content": "\n".join(f"{m['role']}: {m['content']}" for m in old)},
            ],
        ).choices[0].message.content

    def compact(messages: list[dict]) -> list[dict]:
        return compact_messages(messages, summarize=summarize_llm)

    def send(messages: list[dict]) -> str:
        if len(messages) >= COMPACT_TRIGGER:  # chỉ nén khi vượt ngưỡng, không nén mỗi lượt
            messages = compact(messages)
        resp = client.chat.completions.create(model=MODEL, messages=messages)
        return resp.choices[0].message.content


# ============ MOCK MODE (không cần API key) ============

if MOCK:
    def summarize_mock(old: list[dict]) -> str:
        # Deterministic: ghép nội dung cũ thành gạch cắt ngắn — đủ để demo token giảm
        return "\n".join(f"- {m['role']}: {m['content'][:60]}" for m in old[:10])

    def compact(messages: list[dict]) -> list[dict]:
        return compact_messages(messages, summarize=summarize_mock)

    def send(messages: list[dict]) -> str:
        if len(messages) >= COMPACT_TRIGGER:
            messages = compact(messages)
        return "[mock] Phản hồi mẫu — live mode (có OPENAI_API_KEY) mới gọi model thật."


# ============ Mock run: in lại kịch bản trong bài ============

def mock_run() -> None:
    print("=" * 60)
    print("MOCK MODE 1 — MemoryManager: add / retrieve")
    print("=" * 60)
    memory = MemoryManager()
    memory.add("Người dùng đặt gói Cloud Pro ngày 20/11")
    memory.add("Người dùng hỏi về chính sách hoàn tiền")
    memory.add("Hạn thanh toán là 30/12/2026", kind="fact")
    print(f"retrieve('hạn thanh toán') → {memory.retrieve('hạn thanh toán')}")
    # → ['Hạn thanh toán là 30/12/2026']  (khớp output mẫu trong bài)
    print()
    print("=" * 60)
    print("MOCK MODE 2 — Compaction: token trước / sau")
    print("=" * 60)
    conversation = [{"role": "system", "content": "Bạn là DocMind, trợ lý tra cứu tài liệu."}]
    for i in range(1, 8):
        conversation.append({"role": "user", "content": f"Câu hỏi {i}: chính sách về đơn hàng là gì?"})
        conversation.append({"role": "tool", "content": f"Kết quả tool câu {i}: " + "chi tiết chính sách dài " * 30})
        conversation.append({"role": "assistant", "content": f"Trả lời câu {i}: đã tổng hợp theo tài liệu."})
    before = estimate_tokens(conversation)
    compacted = compact(conversation)
    after = estimate_tokens(compacted)
    print(f"Tổng lượt: {len(conversation)} (chạm ngưỡng {COMPACT_TRIGGER}) → nén lịch sử cũ")
    print(f"Token trước: {before} | Token sau: {after} | Tiết kiệm: {before - after} ({100 * (before - after) / before:.0f}%)")
    print(f"Lượt gần nhất giữ nguyên: {len(compacted) - 1} lượt")


# ============ Self-test: assert hành vi, không gọi API ============

def self_test() -> None:
    # 1) retrieve trả đúng item chứa con số người dùng đã nói
    m = MemoryManager()
    m.add("Người dùng đặt gói Cloud Pro ngày 20/11")
    m.add("Người dùng hỏi về chính sách hoàn tiền")
    m.add("Hạn thanh toán là 30/12/2026", kind="fact")
    hits = m.retrieve("hạn thanh toán")
    assert hits and "30/12/2026" in hits[0], f"retrieve sai: {hits}"

    # 2) compact: gộp event cũ thành fact, giữ nguyên fact có sẵn
    m2 = MemoryManager()
    for text in ("Sự kiện 1", "Sự kiện 2", "Sự kiện 3", "Sự kiện 4"):
        m2.add(text)
    m2.add("Hạn thanh toán là 30/12/2026", kind="fact")
    m2.compact()
    kinds = [i.kind for i in m2.items]
    assert kinds.count("fact") == 2, f"sau compact cần 2 fact (mới gộp + sẵn), thực tế {kinds}"
    merged = next(i for i in m2.items if i.kind == "fact" and "Sự kiện 1" in i.text)
    assert "Sự kiện 2" in merged.text, "fact mới phải gộp đủ nửa event cũ"
    assert any("30/12/2026" in i.text for i in m2.items), "compact phải giữ nguyên fact có sẵn"
    assert {"Sự kiện 3", "Sự kiện 4"} <= {i.text for i in m2.items if i.kind == "event"}

    # 3) split_history: old + recent đúng thứ tự, recent nguyên vẹn
    messages = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"lượt {i}"}
                for i in range(10)]
    old, recent = split_history(messages, keep=6)
    assert len(old) == 4 and len(recent) == 6
    assert old == messages[:4] and recent == messages[4:], "thứ tự old + recent phải giữ nguyên"
    assert recent[-1]["content"] == "lượt 9", "recent phải nguyên vẹn"
    # edge: keep >= tổng lượt → old rỗng, recent là toàn bộ
    old2, recent2 = split_history(messages, keep=20)
    assert old2 == [] and recent2 == messages

    print("Self-test bai-4: PASS — retrieve fact, compact memory, split_history thuần")


if __name__ == "__main__":
    self_test()
    if MOCK:
        mock_run()
    else:
        # Live mode — demo đúng luồng trong bài
        memory = MemoryManager()
        memory.add("Người dùng đặt gói Cloud Pro ngày 20/11")
        memory.add("Hạn thanh toán là 30/12/2026", kind="fact")
        print("retrieve:", memory.retrieve("hạn thanh toán"))
        conversation = [{"role": "system", "content": "Bạn là DocMind."}]
        for i in range(1, 8):
            conversation += [{"role": "user", "content": f"Câu hỏi {i}."},
                             {"role": "tool", "content": "Kết quả dài " * 30},
                             {"role": "assistant", "content": "Đã trả lời."}]
        print(f"Token trước compact: {estimate_tokens(conversation)}")
        conversation = compact(conversation)
        print(f"Token sau compact:  {estimate_tokens(conversation)}")
        print("send:", send(conversation))
