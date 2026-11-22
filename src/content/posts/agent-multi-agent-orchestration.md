---
title: "Multi-agent orchestration: điều phối đội agent như một hệ thống"
description: "Từ một agent lên nhiều agent: supervisor và specialist, manager pattern với as_tool, handoff phi tập trung, debate, blackboard và Mixture of Agents — so sánh framework AutoGen, CrewAI, LangGraph và code thực hành supervisor."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-22"
cover: "/images/covers/posts/agent-multi-agent-orchestration.jpg"
featured: false
views: 300
faq:
  - q: "Khi nào nên tách từ single-agent sang multi-agent?"
    a: "Chỉ khi single-agent đã cạn đường: đã thêm tools từng bước, viết lại prompt template nhưng vẫn sai vì quá nhiều tools chồng lấn hoặc chuỗi nhánh if-else khó mở rộng. Multi-agent là chi phí thêm — thêm token, thêm độ trễ, thêm điểm lỗi — không phải nâng cấp miễn phí."
  - q: "Manager pattern và handoff khác nhau thế nào?"
    a: "Manager (supervisor) giữ quyền điều phối: gọi specialist như một tool, thu kết quả về và ra quyết định cuối. Handoff chuyển hẳn quyền thực thi và trạng thái hội thoại cho agent kế tiếp, không quay lại. Chọn manager khi cần một điểm tương tác duy nhất; chọn handoff khi mỗi chuyên gia tiếp quản trọn vẹn một pha."
  - q: "Nên chọn framework multi-agent nào?"
    a: "LangGraph khi cần kiểm soát flow bằng graph state machine; AutoGen cho demo conversational nhanh; CrewAI cho business flow theo role; OpenAI Swarm/Agents SDK cho handoff nhẹ. Khuyến nghị: tự dựng supervisor bằng OpenAI SDK thuần trước để hiểu vòng lặp tool-call, rồi mới chuyển framework."
  - q: "Làm sao giảm nhiễu giao tiếp giữa các agent?"
    a: "Mỗi agent giữ một vai trò hẹp, đầu-ra theo contract cố định (JSON schema), và supervisor là nơi duy nhất ra quyết định. Giới hạn số vòng bằng max_rounds cứng và log từng tool-call — không để agent nói chuyện tự do qua lại vô hạn."
---

Bài [Nền tảng agent và agent loop](/bai-viet/nen-tang-agent-va-agent-loop) đã dựng một agent hoàn chỉnh: model, tools và vòng lặp quyết định. Câu hỏi tiếp theo rất tự nhiên khi agent bắt đầu làm việc thật: một agent có đủ không? Nguyên tắc của bài này khó chịu nhưng đúng: **thường là đủ — và khi không đủ, multi-agent phải trả giá**. Không có nâng cấp miễn phí nào ở đây.

Bài đi qua bốn phần: thời điểm nên tách nhiều agent, hai mẫu orchestration gốc (supervisor và handoff), các kiến trúc multi-agent đáng nhớ, rồi bảng so sánh framework và một bản dựng supervisor bằng OpenAI SDK chạy được ngay.

## Khi nào cần nhiều agent

Bài 8 của Microsoft AI Agents for Beginners đặt nguyên tắc theo đúng thứ tự: **tối đa hóa single-agent trước, tách multi-agent là phương án cuối**. Trước khi nghĩ đến "đội agent", còn ba mỏ vàng chưa khai: thêm tools từng bước, dùng prompt template với biến chính sách thay vì nhiều prompt riêng, và cải thiện tên với mô tả tools — model chọn nhầm tool phần lớn là do mô tả mơ hồ.

Chỉ khi ba cách trên đã dùng hết mà agent vẫn sai, mới xét dấu hiệu chạm trần:

- **Quá nhiều tools chồng lấn** — model chọn nhầm dù mô tả đã tốt, và bảng danh sách tools chiếm chỗ trong context.
- **Nhánh if-else chồng chéo** — thêm một ca sử dụng là phải sửa prompt cũ và chờ nó không phá ca cũ.
- **Các phần công việc cần system prompt khác hẳn nhau** — nhét mọi vai trò vào một prompt làm ngữ cảnh dài và loãng.
- **Các phần độc lập có thể chạy song song** — ví dụ tra ba nguồn dữ liệu cùng lúc.

> **Bắt đầu single-agent. Multi-agent là chi phí — thêm token, thêm độ trễ, thêm điểm lỗi — không phải nâng cấp miễn phí.**

| Tình huống | Nên làm |
| --- | --- |
| Agent chưa đủ tools, prompt còn sơ sài | Ở lại single-agent |
| Đã tối ưu tools và prompt nhưng vẫn chọn nhầm tool | Cân nhắc tách theo nhóm tools |
| Một prompt gánh nhiều vai trò mâu thuẫn | Tách theo vai trò |
| Tác vụ độc lập, chạy song song được | Tách + fan-out từ một điểm điều phối |
| Chỉ muốn hệ thống "trông chuyên nghiệp hơn" | Ở lại single-agent |

## Hai mẫu orchestration gốc

Guide *A Practical Guide to Building Agents* của OpenAI (đã dịch trong bài [Hướng dẫn xây dựng Agent thực tế](/bai-viet/huong-dan-xay-dung-agent-thuc-te)) chỉ nêu đúng hai mẫu orchestration; mọi framework về sau đều là biến thể của hai mẫu này. Ở đây chỉ chốt bản chất, không lặp lại chi tiết cú pháp.

**Manager/supervisor pattern** — một agent trung tâm giữ toàn quyền điều phối. Specialist được bọc thành tool (trong Agents SDK là `as_tool`): supervisor gọi khi cần, nhận kết quả về, tự quyết bước tiếp. Specialist không nói chuyện với người dùng, cũng không nói chuyện với nhau.

**Handoff phi tập trung** — quyền thực thi và toàn bộ trạng thái hội thoại được chuyển hẳn cho agent kế tiếp, không quay lại. Kiểu quen nhất là pipeline chăm sóc khách hàng: agent ngôn ngữ nhận tin nhắn, chuyển quyền cho agent bán hàng, agent bán hàng chuyển cho agent hoàn tất thanh toán.

| Tiêu chí | Manager/supervisor | Handoff phi tập trung |
| --- | --- | --- |
| Ai giữ context | Supervisor giữ trọn hội thoại | Agent đang giữ quyền thực thi |
| Điểm tương tác | Một, tại supervisor | Nhiều, theo lượt chuyển quyền |
| Kiểm soát chất lượng | Tập trung: mọi kết quả đi qua supervisor | Phân tán: mỗi agent tự chịu phần mình |
| Chi phí context | Cao dần ở supervisor (tích lũy) | Thấp hơn mỗi agent, nhưng mất nhìn tổng thể |
| Khi nào chọn | Pipeline cần tổng hợp, quyết định cuối | Mỗi chuyên gia tiếp quản trọn vẹn một pha |

Hai mẫu khác nhau trong code thế nào? Vài dòng dưới đây đủ để thấy — bản supervisor đầy đủ nằm ở phần cuối bài:

```python
# Handoff (tham chiếu bài tập 2): quyền chuyển thẳng, không về supervisor.
def handoff_pipeline(topic: str) -> str:
    research = researcher(topic)      # specialist 1 chạy xong
    return writer(topic, research)    # specialist 2 tiếp quản, không quay lại
```

Quy tắc chọn gọn như sau: cần **một đầu ra cuối cùng có người chịu trách nhiệm** → supervisor. Workflow tự nhiên tách thành các pha rời rạc, mỗi pha một chủ nhân → handoff.

## Các kiến trúc multi-agent khác

Họ "Multi-Agent" trong [all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures) có thêm bốn kiến trúc đáng nhớ. Điểm chung: chúng là cách **cấu trúc lại quyền ra quyết định** — ai được nói gì, khi nào, và ai nghe.

**Debate** (Du et al., 2023). N agent trả lời độc lập, rồi K vòng phản biện lẫn nhau; một judge (hoặc bỏ phiếu đa số) chọn câu cuối. Paper gốc cho thấy debate tăng accuracy trên tác vụ suy luận toán học và chiến lược. Cái giá: một câu hỏi tốn N × K lần gọi LLM trở lên.

**Blackboard** — tư tưởng từ hệ AI cổ điển (Hearsay-II, thập niên 1970). Một workspace chung: agent nào xong phần mình ghi kết quả lên đó, agent khác đọc và tiếp nối. Không ai điều phối ai. Phù hợp khi không biết trước thứ tự công việc.

**STORM** (Shao et al., 2024). Mô phỏng nhóm nghiên cứu viết bài Wikipedia: nhiều perspective đặt câu hỏi khác nhau, khảo sát nguồn, tổng hợp thành bài có trích dẫn. Chọn kiến trúc này khi cần nội dung dài, đa góc nhìn, có căn cứ nguồn.

**Mixture of Agents** (Wang et al., 2024). Nhiều LLM xếp thành tầng proposer: tầng sau nhìn thấy output tầng trước, tầng cuối một aggregator tổng hợp. Trên benchmark, tập hợp model trung bình vượt cả model mạnh hơn từng cái một — cùng tinh thần với ensemble trong machine learning.

### Sơ đồ supervisor

Kiến trúc supervisor — mẫu mà phần code dưới đây dựng — trông như sau:

```
                     ┌────────────────────────────────┐
  Người dùng ──────► │           Supervisor           │
                     │   giữ context, quyết định cuối  │
                     └────────┬──────────────┬────────┘
                              │              │
                  gọi như tool│              │gọi như tool
                              ▼              ▼
                      ┌────────────┐   ┌────────────┐
                      │ Researcher │   │   Writer   │
                      │ thu số liệu│   │ viết bài   │
                      └──────┬─────┘   └──────┬─────┘
                             │                │
                             └────────┬───────┘
                                      ▼
                         kết quả về lại Supervisor
```

Hai mũi tên xuống là hai lời gọi tool; hai đường về là hai kết quả trả về. Không có cạnh nối Researcher với Writer — mọi luồng dữ liệu đi qua supervisor. Đây là lý do supervisor dễ debug hơn handoff: toàn bộ lịch sử nằm ở một chỗ.

## Chọn framework

| Framework | Mô hình thiết kế | Điểm mạnh | Đánh đổi |
| --- | --- | --- | --- |
| LangGraph | Graph + state machine | Kiểm soát flow tốt nhất; checkpoint, replay, human-in-the-loop | Học dốc hơn; code dài hơn |
| AutoGen | Conversational multi-agent | Demo hội thoại giữa các agent nhanh nhất | Khó kiểm soát hội thoại dài; token khó đoán |
| CrewAI | Role-based crews | Map tự nhiên với business flow (PM, dev, QA) | Ít linh hoạt với flow phức tạp |
| OpenAI Swarm/Agents SDK | Handoff + as_tool mỏng | API nhỏ, dễ hiểu cơ chế gốc | Ecosystem ít hơn; pattern có hạn |

Khuyến nghị của bài này: **tự dựng supervisor bằng OpenAI SDK thuần trước, rồi mới sang framework**. Lý do nằm ở chỗ debug: framework giấu vòng lặp tool-call bên trong API của nó. Khi pipeline hỏng, người sửa cần biết vòng lặp đó chạy thế nào — state nằm ở đâu, tool-call hỏng chỗ nào, vòng lặp dừng khi nào. Bản dựng ~120 dòng dưới đây chính là vòng lặp mà LangGraph hay CrewAI bọc lại theo cách riêng của chúng.

## Cạm bẫy multi-agent

Bốn thất bại lặp lại nhiều nhất khi đội agent vận hành thật:

1. **Giao tiếp gây nhiễu.** Mỗi agent thêm output vào context chung; sau vài vòng, model bị nhiễu bởi chính văn bản do agent sinh ra.
2. **Chi phí nhân.** N agent × K vòng — một debate N=3, K=2 là ít nhất sáu lần gọi model cho một câu hỏi.
3. **Debugging khó.** State phân tán giữa các agent, model có tính ngẫu nhiên — lỗi không tái hiện được bằng chạy lại.
4. **Lỗi lan truyền.** Researcher sai một số liệu, writer viết cả bài trên số liệu sai, không ai phát hiện.

Giảm thiểu bằng bốn nguyên tắc, áp dụng được cho mọi kiến trúc phía trên:

| Nguyên tắc | Cách làm cụ thể |
| --- | --- |
| Mỗi agent một vai trò hẹp | Một system prompt một nhiệm vụ; writer không kiêm fact-check |
| Contract đầu-ra rõ | JSON schema cố định: field nào, kiểu gì, bắt buộc gì |
| Supervisor là nơi duy nhất ra quyết định | Specialist chỉ trả dữ liệu; nhánh if-else nằm ở supervisor |
| Giới hạn vòng, log từng bước | max_rounds cứng; log mỗi tool-call để tái hiện lỗi |

Nguyên tắc thứ ba quan trọng nhất: quyền ra quyết định ở một điểm duy nhất thì hệ thống có một nơi để đặt guardrail, một nơi để audit, một nơi để sửa khi sai.

## Code thực hành: supervisor pattern với OpenAI SDK

Môi trường: `pip install openai`, hai biến môi trường `OPENAI_API_KEY` và `OPENAI_MODEL` (ví dụ `gpt-4.1`). Supervisor chỉ điều phối qua hai tool (`call_researcher`, `call_writer`); mỗi specialist là một function gọi LLM riêng với system prompt riêng. Specialist không biết nhau tồn tại — đúng theo sơ đồ ở trên.

```python
import json
import os

from openai import OpenAI

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ---------- Specialist 1: Researcher ----------
def researcher(topic: str) -> str:
    """Thu thập điểm chính, số liệu, rủi ro — trả JSON theo contract."""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Bạn là researcher. Với chủ đề được cho, trả về JSON gồm: "
                    "key_points (5 điểm chính), numbers (3 số liệu đáng chú ý), "
                    "risks (2 rủi ro). CHỈ trả JSON, không thêm chữ nào khác."
                ),
            },
            {"role": "user", "content": f"Chủ đề: {topic}"},
        ],
    )
    return resp.choices[0].message.content


# ---------- Specialist 2: Writer ----------
def writer(topic: str, research_json: str) -> str:
    """Biến kết quả nghiên cứu thành bài phân tích hoàn chỉnh."""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Bạn là writer. Dùng dữ liệu JSON từ researcher, viết bài "
                    "phân tích khoảng 300 từ: mở đầu nêu bối cảnh, thân bài dẫn "
                    "số liệu cụ thể, kết bài nêu rủi ro. Không bịa số liệu ngoài JSON."
                ),
            },
            {"role": "user", "content": f"Chủ đề: {topic}\nDữ liệu: {research_json}"},
        ],
    )
    return resp.choices[0].message.content


# ---------- Supervisor: chỉ điều phối qua tool ----------
SUPERVISOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "call_researcher",
            "description": "Gọi agent researcher thu thập điểm chính, số liệu, rủi ro cho một chủ đề.",
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string"}},
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "call_writer",
            "description": "Gọi agent writer viết bài phân tích từ dữ liệu JSON đã có.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "research_json": {"type": "string"},
                },
                "required": ["topic", "research_json"],
            },
        },
    },
]

SYSTEM = (
    "Bạn là supervisor điều phối đội specialist. Quy trình bắt buộc: "
    "1) call_researcher để lấy dữ liệu. "
    "2) call_writer để viết bài từ dữ liệu. "
    "3) Trả bài viết cho người dùng. Tuyệt đối không tự viết bài."
)


def run_supervisor(task: str, max_rounds: int = 6) -> str:
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": task},
    ]
    for _ in range(max_rounds):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=SUPERVISOR_TOOLS
        )
        msg = resp.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:  # supervisor đã trả lời xong
            return msg.content

        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            if call.function.name == "call_researcher":
                result = researcher(args["topic"])
            else:
                result = writer(args["topic"], args["research_json"])
            print(f"[supervisor] gọi {call.function.name}")
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": result}
            )
    return "Supervisor dừng: vượt số vòng cho phép."


if __name__ == "__main__":
    print(
        run_supervisor(
            "Viết bài phân tích thị trường GPU cloud cho ngành logistics tại Việt Nam"
        )
    )
```

Chạy ví dụ trên, supervisor làm đúng ba bước: gọi researcher, nhận JSON về, gọi writer với dữ liệu đó, trả bài viết. Ba điểm cần nhìn khi đọc log: mọi quyết định (gọi ai, khi nào, gọi thêm không) nằm ở supervisor; specialist có contract đầu ra cố định — researcher trả JSON ba field, writer bị cấm bịa số liệu ngoài JSON nhận vào; vòng lặp có điểm dừng cứng qua `max_rounds`. Khi bản dựng này chạy ổn, chuyển sang LangGraph hay CrewAI chỉ là đổi cách viết state và flow, không đổi cách nghĩ.

## Bài tập tự làm

1. **Thêm specialist thứ ba.** Viết `fact_checker` nhận `research_json`, trả JSON đã sửa. Sửa `SYSTEM` để supervisor buộc gọi researcher → fact_checker → writer đúng thứ tự đó.
2. **So sánh supervisor và handoff.** Thay supervisor bằng handoff: researcher chuyển quyền thẳng cho writer khi xong. Chạy cùng một task, so sánh output cuối và số token của hai cách.
3. **Xử lý khi hết vòng.** Đặt `max_rounds = 2` rồi chạy task đòi ba bước. Viết fallback: khi hết vòng, supervisor trả message rõ ràng cho người dùng ("chưa hoàn thành vì X") thay vì dừng im lặng.

## Tài liệu gốc

- Microsoft — AI Agents for Beginners, bài 8 (Agentic Design Patterns): [github.com/microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners)
- all-agentic-architectures (Debate, Blackboard, STORM, Mixture of Agents): [github.com/FareedKhan-dev/all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures)
- Nir Diamant — GenAI Agents (notebook multi-agent từng kiến trúc): [github.com/NirDiamant/GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents)
- Trên LearnWithHuy: [Hướng dẫn xây dựng Agent thực tế](/bai-viet/huong-dan-xay-dung-agent-thuc-te) — bản dịch guide OpenAI, có chi tiết `as_tool` và handoff; [Nền tảng agent và agent loop](/bai-viet/nen-tang-agent-va-agent-loop) — vòng lặp single-agent là nền của mọi thứ trong bài này.
