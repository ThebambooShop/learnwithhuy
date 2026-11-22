# Starter kit — Kiến trúc AI Agent (LearnWithHuy)

Bộ code chạy được cho lộ trình 8 bài. Mỗi bài một file, đặt tên theo bài:
`bai-1-agent-loop.py` ... `bai-8-architecture-picker.py`. Mỗi file chạy được
ở **hai chế độ**:

- **Mock mode (không cần API key)**: chạy ngay, in lại đúng luồng output mẫu
  trong bài + tự chạy self-test (assert) kiểm tra hành vi agent.
- **Live mode (có API key)**: gọi model thật như trong bài viết.

## Cài đặt từ đầu (5 phút)

```bash
# 1. Tạo thư mục làm việc và venv
mkdir docmind && cd docmind
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Tải starter kit: tải từng file .py về thư mục này, cùng 2 file dưới đây
#    - requirements.txt
#    - .env.example  (đổi tên thành .env)

# 3. Cài dependency
pip install -r requirements.txt
```

## Cấu hình

```bash
cp .env.example .env
# Sửa .env: điền OPENAI_API_KEY của bạn (bỏ qua nếu chỉ chạy mock mode)
```

File `.env` không bao giờ commit lên git. Starter kit không đọc `.env` tự động
— dùng `export` cho gọn:

```bash
export OPENAI_API_KEY=sk-...            # để chạy live mode
export OPENAI_MODEL=gpt-4o-mini         # tùy chọn, mặc định gpt-4o-mini
```

## Chạy

```bash
python bai-1-agent-loop.py        # không có key -> mock mode + self-test
python bai-1-agent-loop.py        # có key -> live mode, gọi model thật
```

Kết quả mẫu khi chạy bài 1 live mode (số lượt có thể khác nhẹ tùy model):

```
Lượt 1: tool call get_weather(city="Hà Nội"), get_weather(city="Đà Nẵng")
Lượt 2: tool call calculate(expression="22 - 30")
Lượt 3: "Hà Nội 22°C, Đà Nẵng 30°C — Hà Nội mát hơn Đà Nẵng 8 độ."
```

## Bài tập 3 mức

Mỗi bài viết kết thúc bằng bài tập chia 3 mức — làm đúng thứ tự:

1. **Làm theo**: sửa starter kit đúng chỉ dẫn, chạy lại, thấy kết quả đổi.
2. **Tự sửa**: tự thay đổi một phần (tool mới, điều kiện dừng, ngưỡng confidence).
3. **Mở rộng**: ghép pattern của bài này vào DocMind — trợ lý tra cứu tài liệu
   nội bộ là dự án xuyên suốt của lộ trình.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'openai'` | Chưa cài hoặc quên activate venv | `source .venv/bin/activate` rồi `pip install -r requirements.txt` |
| `AuthenticationError` / `401` | `OPENAI_API_KEY` chưa export hoặc sai | `export OPENAI_API_KEY=...` trong cùng terminal chạy code |
| `invalid_request_error` / model không tồn tại | Tên model sai hoặc hết quyền | Kiểm tra model trong console nhà cung cấp, đổi `OPENAI_MODEL` |
| Protocol error ở lượt 2 | Thiếu append message tool_calls hoặc tool result | Đọc lại phần agent loop bài 1 — cả hai đều bắt buộc |
| Chạy và im lặng mãi | Agent lặp không có điểm dừng | Kiểm tra `max_turns` đã truyền đúng |

## Ghi chú về phiên bản API

Code dùng **Chat Completions API** qua `openai` SDK bản 1.x, kiểm tra với
`gpt-4o-mini`. Kiến trúc agent loop (tool call JSON → execute → append context
→ lặp) **ổn định theo thời gian**; tên API và model có thể đổi theo nhà cung cấp.
OpenAI đã ngừng Assistants API ngày 26/8/2026 và hướng dự án mới sang Responses
API — chuyển API không làm đổi kiến trúc loop bạn học trong lộ trình này.

## Lộ trình

1. [Bài 1 — Nền tảng agent và agent loop](/bai-viet/nen-tang-agent-va-agent-loop)
2. [Bài 2 — Tool use và Routing](/bai-viet/agent-routing-va-tool-design)
3. [Bài 3 — Planning và Reflection](/bai-viet/agent-planning-va-reflection)
4. [Bài 4 — Memory và Context Engineering](/bai-viet/agent-memory-va-context-engineering)
5. [Bài 5 — Multi-agent orchestration](/bai-viet/agent-multi-agent-orchestration)
6. [Bài 6 — RAG trong agent](/bai-viet/agent-rag-va-graphrag)
7. [Bài 7 — 12 nguyên lý production](/bai-viet/12-nguyen-ly-agent-production)
8. [Bài 8 — Chọn architecture: 36 mẫu](/bai-viet/chon-agent-architecture-36-mau)
