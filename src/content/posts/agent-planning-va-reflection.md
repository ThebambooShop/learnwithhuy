---
title: "Planning và Reflection: agent tự lập kế hoạch và tự sửa lỗi"
description: "Hai pattern nâng năng lực agent lên mức hệ: planning phân rã tác vụ thành kế hoạch rồi thực thi có replan, reflection cho agent tự chấm điểm và tự sửa — kèm so sánh Self-Consistency, Tree of Thoughts, LATS và code thực hành."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-22"
cover: "/images/covers/posts/agent-planning-va-reflection.jpg"
featured: false
views: 300
faq:
  - q: "Planning khác agent loop thường ở chỗ nào?"
    a: "Agent loop cơ bản chỉ quyết định bước tiếp theo mỗi vòng dựa trên kết quả vừa nhận, không nhìn toàn cảnh. Planning thêm pha decompose: model viết ra toàn bộ kế hoạch trước khi chạy, nên bạn đọc và review được tiến trình trước khi đốt chi phí thực thi. Khi một bước fail, replan viết lại phần kế hoạch còn lại thay vì để agent mò mẫm từ đầu."
  - q: "Bao nhiêu vòng reflection là đủ?"
    a: "2-3 vòng là điểm cân bằng thực tế. Vòng đầu sửa được phần lớn lỗi rõ ràng; từ vòng ba trở đi chỉ còn sửa lỗi rất nhỏ trong khi chi phí tăng tuyến tính. Đặt stop condition rõ: dừng khi rubric pass hoặc điểm không tăng giữa hai vòng liên tiếp — điểm đi ngang nghĩa là thêm vòng cũng không cải thiện."
  - q: "Self-Consistency và Tree of Thoughts khác nhau thế nào?"
    a: "Self-Consistency chạy song song N mẫu độc lập của cùng một prompt rồi majority vote — các mẫu không nhìn thấy nhau. Tree of Thoughts làm việc trên cây: mỗi nhánh là một thought giữa chừng, được đánh giá để cắt nhánh xấu và mở rộng nhánh tốt. Self-Consistency hợp câu hỏi có đáp án duy nhất; ToT hợp bài toán xây dựng từng bước mà bạn đánh giá được trạng thái giữa chừng."
  - q: "Reflexion khác reflection thường ra sao?"
    a: "Reflection thường sửa trong một phiên rồi hết — lần chạy sau không biết gì về lần trước. Reflexion (Shinn 2023) lưu lời tự phản tư dạng chữ vào episodic memory: sau khi thất bại, agent viết nguyên nhân fail và hướng dẫn cho lần sau, lần thử kế tiếp đọc lại để không lặp lỗi. Lời phản tư cần nằm ở nơi bền — dict, file, bảng — chứ không chỉ prompt tạm thời."
---

Một agent chạy agent loop cơ bản xử lý tốt tác vụ một đến vài vòng: nhận yêu cầu, gọi tool, trả kết quả. Đổi sang tác vụ phức tạp gồm nhiều bước phụ thuộc nhau, loop trần thường thất bại theo ba cách dễ đoán: bỏ sót bước, làm sai thứ tự, và chết ở bước đầu khi tool fail mà không quay lại. Hai pattern trong bài vá đúng ba lỗi đó: **planning** tự lập kế hoạch trước khi chạy, **reflection** tự chấm điểm và tự sửa sau khi chạy.

Nguyên lý chung: cả hai đều thêm lần gọi model bổ sung để kiểm soát lần gọi chính — luôn đổi chi phí lấy chất lượng. Bài này đi qua cơ chế, code chạy được và chi phí thật của mỗi lựa chọn.

## Planning: phân rã, thực thi, replan

> **Planning là pattern agent phân rã mục tiêu thành danh sách bước rõ ràng, thực thi từng bước và lập kế hoạch lại khi thực tế lệch khỏi dự đoán.**

Bài 7 của khóa [Microsoft AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) dành riêng cho pattern này; trong repo [all-agentic-architectures](https://github.com/FareedKhan-dev/all-agentic-architectures), planning nằm trong họ **"Tools & Actions"** cùng tool use và routing — bản chất nó cũng chỉ là cách tổ chức việc gọi tool có hệ thống.

Vòng đời chuẩn gồm ba pha:

1. **Decompose** — planner nhận mục tiêu, trả danh sách bước, mỗi bước có action và expected.
2. **Execute** — executor chạy từng bước, kết quả bước trước làm context cho bước sau.
3. **Replan** — bước fail thì planner viết lại phần kế hoạch còn lại dựa trên đã làm và lỗi vừa gặp.

```
              ┌───────────────┐
 Mục tiêu ──→ │    PLANNER    │ ──→ kế hoạch: [bước 1, bước 2, bước 3]
              └───────────────┘
                        │
                        ▼
              ┌───────────────┐  bước fail     ┌───────────────┐
              │   EXECUTOR    │ ─────────────→ │    REPLAN     │
              │ (chạy từng    │                │ (viết lại phần│
              │    bước)      │ ←───────────── │  kế hoạch)    │
              └───────────────┘  kế hoạch mới  └───────────────┘
                        │
                        ▼  bước OK → chạy tiếp đến hết kế hoạch
                 Kết quả cuối
```

### Plan-then-execute hay interleave?

Hai phong cách lập kế hoạch, chọn theo hình dáng tác vụ:

| Tiêu chí | Plan-then-execute | Interleave (lập bước chạy bước) |
| --- | --- | --- |
| Cách làm | Planner viết ra toàn bộ kế hoạch, executor chạy lần lượt | Model chỉ quyết định bước tiếp theo mỗi vòng, không có bản kế hoạch tổng |
| Ưu điểm | Kế hoạch rõ, dễ review và debug trước khi đốt chi phí thực thi | Linh hoạt với bài toán không nhìn trước được hết; không lãng phí lập kế hoạch rồi vứt |
| Nhược điểm | Sai ở đầu thì cả chuỗi sai theo; chậm thích ứng với tín hiệu mới giữa đường | Dễ lạc đề sau nhiều vòng; khó audit tiến trình tổng thể |
| Hợp với | Tác vụ có cấu trúc rõ: deploy, migrate dữ liệu, tổng hợp báo cáo nhiều nguồn | Tác vụ khám phá: research web, debug hệ thống lạ, tìm kiếm đa nhánh |

ReAct trong bài [nền tảng agent](/bai-viet/nen-tang-agent-va-agent-loop) là interleave thuần túy — planning thêm bản kế hoạch trên đó. Nhiều agent production dùng cả hai: kế hoạch thô trước, rồi cho phép một bước sinh bước con khi cần.

### PEV: thêm verify sau mỗi bước

Plan-Execute-Verify (PEV) là biến thể đáng nhớ của họ "Tools & Actions": sau mỗi bước execute thêm một bước **verify độc lập** — tool có trả về dữ liệu đúng dạng không, kết quả có hợp lý không, bước này có làm tiến gần mục tiêu không. Verify pass mới sang bước kế; fail thì mới đụng đến replan.

Không verify, executor chỉ biết bước "chạy xong" chứ không biết bước "chạy đúng" — kết quả lỗi ở bước 2 được bước 3 dùng làm đầu vào và lan cả chuỗi. Verify mỗi bước cắt lỗi ngay tại chỗ sinh ra, đổi lấy một lần gọi model cho mỗi bước.

Code thực hành đầu tiên: plan-then-execute có replan khi bước fail.

```python
import os
import json
from openai import OpenAI

client = OpenAI()  # đọc OPENAI_API_KEY từ env
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def llm(messages: list[dict]) -> str:
    resp = client.chat.completions.create(model=MODEL, messages=messages)
    return resp.choices[0].message.content

def make_plan(goal: str) -> list[dict]:
    raw = llm([
        {"role": "system", "content": (
            "Bạn là planner. Phân rã mục tiêu thành tối đa 5 bước, mỗi bước có "
            "action và expected. Chỉ trả JSON: "
            '{"steps": [{"id": 1, "action": "...", "expected": "..."}]}'
        )},
        {"role": "user", "content": f"Mục tiêu: {goal}"},
    ])
    return json.loads(raw)["steps"]

def execute_step(step: dict, context: list[str]) -> str:
    return llm([
        {"role": "system", "content": "Thực thi bước dưới đây dựa trên kết quả đã có. Trả kết quả ngắn gọn."},
        {"role": "user", "content": f"Bước: {step['action']}\nKết quả trước đó: {context}"},
    ])

def replan(goal, failed_step, error, done, remaining) -> list[dict]:
    raw = llm([
        {"role": "system", "content": (
            "Bước dưới đây đã fail. Viết lại CHỈ phần kế hoạch còn lại để "
            "tránh nguyên nhân fail. Chỉ trả JSON đúng định dạng steps."
        )},
        {"role": "user", "content": (
            f"Mục tiêu: {goal}\nĐã làm xong: {done}\n"
            f"Bước lỗi: {failed_step['action']}\nLỗi: {error}\n"
            f"Bước chưa chạy: {remaining}"
        )},
    ])
    return json.loads(raw)["steps"]

def run_plan(goal: str, max_replans: int = 2) -> list[str]:
    steps, results, done, replans = make_plan(goal), [], [], 0
    while steps:
        step = steps.pop(0)
        try:
            outcome = execute_step(step, results)
            results.append(outcome)
            done.append(step)
        except Exception as e:
            replans += 1
            if replans > max_replans:
                raise RuntimeError(f"Replan vượt {max_replans} lần: {e}")
            steps = replan(goal, step, str(e), done, [s["action"] for s in steps])
    return results
```

Ba chi tiết đáng chú ý hơn phần thân code:

- **JSON thay vì free text** làm planner và replan nối vào executor không đổi giao diện. Model hay trả lệch format thì thêm `response_format={"type": "json_object"}` và retry một lần khi parse lỗi.
- **Replan chỉ viết phần còn lại**: phần đã pass không bị model viết lại thành khác, tránh regression ở những bước đã chạy đúng.
- **max_replans là van an toàn** — không có nó, một bước fail lặp vô tận sẽ đốt hóa đơn trong lúc bạn đi ăn trưa.

## Reflection: generate → critique → refine

> **Reflection là pattern agent tự đánh giá kết quả của chính mình và sửa lại trước khi giao cho người dùng.**

Nền lý thuyết: bài 9 "Metacognition" của khóa Microsoft — cho agent khả năng suy nghĩ về việc mình đang làm — và notebook **Reflection** trong repo [GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents). Công trình gốc là Self-Refine (Madaan 2023), vòng ba bước:

1. **Generate** — tạo bản nháp đầu tiên.
2. **Critique** — chính model chấm bản nháp theo rubric và liệt kê issues cụ thể.
3. **Refine** — sửa bản nháp theo issues, quay lại critique.

Lặp đến khi pass hoặc hết vòng. Rubric quyết định chất lượng cả vòng: "hay hơn" là critique vô dụng vì model không biết sửa đâu; "mỗi khẳng định phải có căn cứ, thiếu thì ghi rõ chỗ nào" mới dùng được.

### Ba biến thể critique

Notebook Reflection triển khai ba biến thể thực hành, tăng dần độ chắc:

| Biến thể | Cách làm | Hợp với |
| --- | --- | --- |
| **Self-review** | Agent tự chấm theo rubric viết sẵn | Mọi tác vụ văn bản; rẻ nhất, dễ thêm nhất |
| **Skeptical reviewer** | Cùng model nhưng reviewer được hướng dẫn đọc hoài nghi, nghi ngờ từng khẳng định, tìm chỗ lý luận hụt | Nội dung có khẳng định mạnh, lý luận, bản dịch |
| **Fail-tests-as-feedback** | Chạy test thật, dùng assertion fail làm feedback cho vòng refine tiếp | Code: chắc chắn nhất vì feedback đến từ runtime |

Biến thể thứ hai đáng dừng một chút: cùng một model, chỉ đổi system prompt sang "bạn là reviewer hoài nghi..." là critique bắt được lớp lỗi mà self-review tử tế bỏ sót. Không cần model thứ hai — cần một góc nhìn khác.

Code thực hành thứ hai: vòng refine với rubric chấm điểm và stop condition rõ.

```python
import os
import json
from openai import OpenAI

client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def llm(messages: list[dict]) -> str:
    resp = client.chat.completions.create(model=MODEL, messages=messages)
    return resp.choices[0].message.content

RUBRIC = """Chấm bản nháp theo 3 tiêu chí, mỗi tiêu chí 1-5 điểm:
1. Factuality: mỗi khẳng định có căn cứ trong yêu cầu.
2. Completeness: trả lời đủ mọi phần của yêu cầu.
3. Clarity: người đọc hiểu ngay, không vòng vo.
Trả JSON: {"scores": {"factuality": int, "completeness": int, "clarity": int},
"total": int, "issues": ["..."], "pass": true|false} — pass khi total >= 12/15."""

def generate(task: str) -> str:
    return llm([
        {"role": "system", "content": "Viết câu trả lời chất lượng cao cho yêu cầu."},
        {"role": "user", "content": task},
    ])

def critique(task: str, draft: str) -> dict:
    raw = llm([
        {"role": "system", "content": RUBRIC},
        {"role": "user", "content": f"Yêu cầu: {task}\n\nBản nháp:\n{draft}"},
    ])
    return json.loads(raw)

def refine(task: str, draft: str, issues: list[str]) -> str:
    return llm([
        {"role": "system", "content": "Sửa bản nháp theo từng issue. Giữ phần đạt, chỉ thay phần bị chê."},
        {"role": "user", "content": f"Yêu cầu: {task}\n\nBản nháp:\n{draft}\n\nIssues:\n" + "\n".join(issues)},
    ])

def reflect_loop(task: str, max_rounds: int = 3) -> tuple[str, int]:
    draft = generate(task)
    prev_total = 0
    for round_no in range(1, max_rounds + 1):
        fb = critique(task, draft)
        if fb["pass"]:
            return draft, round_no
        if prev_total and fb["total"] <= prev_total:
            break  # điểm không tăng nữa — thêm vòng chỉ đốt tiền
        prev_total = fb["total"]
        draft = refine(task, draft, fb["issues"])
    return draft, round_no
```

Hai stop condition đều cần: pass theo rubric là chính; **điểm không tăng giữa hai vòng** là phụ — điểm đi ngang thì vòng sau gần như chắc chắn không cải thiện, và từ vòng ba reflection chỉ còn sửa lỗi rất nhỏ.

### Reflexion: lưu lỗi để không lặp

Reflexion (Shinn 2023) là bước nâng cấp của reflection thường, khác biệt nằm ở nơi lưu lời tự phản tư:

- **Reflection thường**: critique và refine diễn ra trong một phiên; hết phiên là hết — lần chạy sau không biết gì về lần trước.
- **Reflexion**: sau khi thất bại, agent viết lời tự phản tư dạng chữ ("lần trước fail vì thiếu kiểm tra dữ liệu đầu vào; lần sau kiểm tra trước khi xử lý") lưu vào **episodic memory**; lần thử kế đọc lại trước khi làm, không lặp cùng lỗi.

Triển khai tối giản: một list hoặc file, mỗi lần thử push một note, lần thử sau nạp các note cũ vào system prompt. Ba lời phản tư là đủ để tránh lớp lỗi lặp — pattern rẻ nhất trong bài nhưng tăng chất lượng qua các phiên, không chỉ một phiên.

## Sampling & Search: chạy nhiều phương án rồi chọn

Nhóm pattern thứ ba không tự sửa theo vòng lặp mà **chạy nhiều phương án rồi chọn phương án tốt nhất**. Đầu ra model một lần chỉ là một sample và sample có thể rơi vào trạng thái kém; sinh nhiều sample rồi tìm kiếm giữa chúng tăng xác suất có phương án tốt.

| Pattern | Ý tưởng | Chi phí (số lần gọi LLM) | Khi nào đáng dùng |
| --- | --- | --- | --- |
| **Self-Consistency** (Wang 2022) | Sample N lần cùng prompt, chọn đáp án chiếm đa số (majority vote) | ~x5-x7 với N=5 | Câu hỏi có đáp án đúng duy nhất (toán, trắc nghiệm); không hợp output tự do vì vote không định nghĩa được |
| **Tree of Thoughts** (Yao 2023) | Beam search trên "thoughts": mỗi bước sinh nhiều nhánh, đánh giá và chỉ giữ nhánh tốt | ~x10+, tăng theo depth × beam | Bài toán xây dựng từng bước, biết đánh giá trạng thái giữa chừng (lập kế hoạch phức tạp, chơi cờ) |
| **LATS** (Zhou 2024) | MCTS trên không gian action, reward từ tín hiệu thực (test pass/fail) backup ngược lên cha | ~x10+ mỗi iteration | Tác vụ code/debug có verifier tự động; đáng đổi chi phí khi có tín hiệu runtime |
| **Chain-of-Verification** (Dhuliawala 2023) | Sinh câu trả lời, tự đặt câu verify từng khẳng định, trả lời các câu verify đó độc lập rồi ghép lại | ~x3 | Nội dung fact-dense: bản dịch kỹ thuật, tổng hợp tài liệu — nơi hallucination nguy hiểm nhất |

Chain-of-Verification đáng chú ý vì các câu verify được trả lời trong những lần gọi riêng, không nhìn thấy câu trả lời gốc — tránh việc model "tự xác nhận" chính sai lầm của mình.

## Chi phí thật: đếm số lần gọi trước khi bật pattern

Mọi pattern trong bài đều **nhân số lần gọi model** — và số lần gọi nhân trực tiếp cả hóa đơn lẫn độ trễ. Quy tắc nhanh:

- **Reflection rẻ**: ~x2 (generate + critique); mỗi vòng refine thêm x1.
- **Self-Consistency trung**: ~x5-x7 với N=5.
- **ToT / LATS đắt**: ~x10+ và tăng theo beam width; thực tế có thể nhiều hơn nếu phải đánh giá mỗi node.
- **PEV**: thêm x1 cho mỗi bước — pipeline 5 bước thành ~10 lần gọi, không phải x2 toàn pipeline.

Bật pattern khi **accuracy đáng giá hơn chi phí**: tác vụ production có hậu quả thật — email khách hàng, commit lên main, báo cáo tài chính — đáng đổi x2-x5; tác vụ nội bộ dùng thử hoặc baseline đã pass 95% thì không đáng.

⚠️ Đo baseline trước khi bật: không có eval đo accuracy trước/sau, bạn chỉ đốt tiền theo niềm tin — cùng nguyên tắc chọn model trong bài nền tảng.

## Bài tập tự làm

1. Chạy `run_plan` với mục tiêu "tổng hợp 3 bài báo thành brief 5 gạch đầu dòng". In danh sách bước planner trả về và để ý bước nào model tưởng có tool nhưng thực tế không có — đó là chỗ cần thêm verify trước executor.
2. Thêm verify vào pipeline: sau mỗi `execute_step`, verifier chấm 1-5 theo expected; dưới 3 thì replan. Đếm tổng lần gọi LLM thực tế — so với dự đoán của bạn trước khi chạy.
3. Áp Reflexion cho một tác vụ viết: lần thử 1 fail theo rubric, lưu lời tự phản tư; lần thử 2 nạp nó vào system prompt. So `total` điểm rubric giữa hai lần — không tăng nghĩa là lời phản tư vô dụng, chỉnh rubric trước khi thử thêm.

## Tài liệu gốc

- [Microsoft AI Agents for Beginners — lesson 7 (Planning) và lesson 9 (Metacognition)](https://github.com/microsoft/ai-agents-for-beginners)
- [all-agentic-architectures — family "Tools & Actions"](https://github.com/FareedKhan-dev/all-agentic-architectures)
- [GenAI_Agents — notebook Reflection](https://github.com/NirDiamant/GenAI_Agents)
- Paper nền: Self-Refine (Madaan 2023), Reflexion (Shinn 2023), Self-Consistency (Wang 2022), Tree of Thoughts (Yao 2023), LATS (Zhou 2024), Chain-of-Verification (Dhuliawala 2023)
- Đọc trước trong series: [Nền tảng agent và agent loop](/bai-viet/nen-tang-agent-va-agent-loop) — vòng agent loop và ReAct mà planning, reflection dựa trên; [Agent routing và tool design](/bai-viet/agent-routing-va-tool-design) — tool mà executor gọi, routing mà planner điều hướng.
