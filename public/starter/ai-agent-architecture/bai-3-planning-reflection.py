"""bai-3 — Planning và Reflection: agent tự lập kế hoạch và tự sửa lỗi.

Chạy hai chế độ, chọn tự động theo OPENAI_API_KEY:
- Mock (không key): in lại luồng demo trong bài (plan 3 bước, reflection
  vòng 1 fail 9/15 rồi vòng 2 pass 13/15) + self-test.
- Live (có key): gọi model thật như trong bài viết.

Bài viết: /bai-viet/agent-planning-va-reflection
"""
import json
import os

MOCK = not os.getenv("OPENAI_API_KEY")  # có key -> live, không có -> mock
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# --- Hàm thuần dùng chung cho cả hai chế độ ---

def parse_steps(raw: str) -> list[dict]:
    """Tách JSON planner trả về thành danh sách bước.

    Tách riêng để self-test được: JSON lệch phải raise lỗi RÕ RÀNG.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Planner trả về không phải JSON hợp lệ: {e}") from e
    if not isinstance(data, dict) or "steps" not in data:
        raise ValueError(
            f'Planner trả thiếu key "steps" (cần {{"steps": [...]}}). '
            f"Nhận được: {raw[:200]}"
        )
    if not isinstance(data["steps"], list):
        raise ValueError(f'"steps" phải là list, nhận được: {type(data["steps"]).__name__}')
    return data["steps"]


# --- LIVE MODE (cần OPENAI_API_KEY) ---

if not MOCK:
    from openai import OpenAI

    client = OpenAI()  # đọc OPENAI_API_KEY từ env

    def llm(messages: list[dict], json_mode: bool = False) -> str:
        kwargs = {"model": MODEL, "messages": messages}
        if json_mode:  # chốt format cứng để planner/replan không trả lệch
            kwargs["response_format"] = {"type": "json_object"}
        return client.chat.completions.create(**kwargs).choices[0].message.content

    def _steps(messages: list[dict]) -> list[dict]:
        for attempt in (1, 2):  # parse lỗi thì retry MỘT lần, không lặp vô tận
            try:
                return parse_steps(llm(messages, json_mode=True))
            except ValueError:
                if attempt == 2:
                    raise

    def make_plan(goal: str) -> list[dict]:
        return _steps([
            {"role": "system", "content": (
                "Bạn là planner. Phân rã mục tiêu thành tối đa 5 bước, mỗi bước có "
                "action và expected. Chỉ trả JSON: "
                '{"steps": [{"id": 1, "action": "...", "expected": "..."}]}'
            )},
            {"role": "user", "content": f"Mục tiêu: {goal}"},
        ])

    def execute_step(step: dict, context: list[str]) -> str:
        return llm([
            {"role": "system", "content": "Thực thi bước dưới đây dựa trên kết quả đã có. Trả kết quả ngắn gọn."},
            {"role": "user", "content": f"Bước: {step['action']}\nKết quả trước đó: {context}"},
        ])

    def replan(goal, failed_step, error, done, remaining) -> list[dict]:
        return _steps([
            {"role": "system", "content": (
                "Bước dưới đây đã fail. Viết lại CHỈ phần kế hoạch còn lại để "
                "tránh nguyên nhân fail. Chỉ trả JSON đúng định dạng steps."
            )},
            {"role": "user", "content": (
                f"Mục tiêu: {goal}\nĐã làm xong: {done}\n"
                f"Bước lỗi: {failed_step['action']}\nLỗi: {error}\nBước chưa chạy: {remaining}"
            )},
        ])

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
        return json.loads(llm([
            {"role": "system", "content": RUBRIC},
            {"role": "user", "content": f"Yêu cầu: {task}\n\nBản nháp:\n{draft}"},
        ], json_mode=True))

    def refine(task: str, draft: str, issues: list[str]) -> str:
        return llm([
            {"role": "system", "content": "Sửa bản nháp theo từng issue. Giữ phần đạt, chỉ thay phần bị chê."},
            {"role": "user", "content": f"Yêu cầu: {task}\n\nBản nháp:\n{draft}\n\nIssues:\n" + "\n".join(issues)},
        ])


# --- MOCK MODE (không cần API key) ---

if MOCK:
    _critique_round = [0]  # đếm vòng để mock critique đổi kết quả: vòng 1 fail, vòng 2 pass

    def make_plan(goal: str) -> list[dict]:
        print("→ Planner (mock): trả plan cứng 3 bước")
        return [
            {"id": 1, "action": "Truy xuất nội dung 3 bài báo về agent", "expected": "Có đủ nội dung 3 bài"},
            {"id": 2, "action": "Rút gạch đầu dòng chính từ mỗi bài", "expected": "Tổng cộng ít nhất 5 gạch"},
            {"id": 3, "action": "Ghép và lọc thành brief 5 gạch đầu dòng", "expected": "Brief đúng 5 gạch"},
        ]

    def execute_step(step: dict, context: list[str]) -> str:
        print(f"→ Executor (mock): bước {step['id']} OK")
        return f"Bước {step['id']} hoàn thành: {step['action']}"

    def replan(goal, failed_step, error, done, remaining) -> list[dict]:
        print(f"→ Replan (mock): viết lại phần còn lại sau lỗi '{error}'")
        return [{"id": len(done) + 1, "action": f"Thử lại: {failed_step['action']}",
                 "expected": failed_step["expected"]}]

    def generate(task: str) -> str:
        print("→ Generate (mock): trả bản nháp vòng 1")
        return "Brief: agent gồm LLM + loop + tool. Có planning, có reflection. Hết."

    def critique(task: str, draft: str) -> dict:
        # Kết quả cứng theo luồng demo trong bài: vòng 1 fail (total 9), vòng 2 pass (total 13)
        _critique_round[0] += 1
        if _critique_round[0] == 1:
            print("→ Critique (mock) vòng 1: 9/15 → FAIL, 2 issues")
            return {"scores": {"factuality": 3, "completeness": 3, "clarity": 3}, "total": 9,
                    "issues": ["Completeness: brief chỉ có 3 gạch, thiếu 2 gạch còn lại",
                               "Factuality: 'có reflection' không nêu căn cứ"], "pass": False}
        print("→ Critique (mock) vòng 2: 13/15 → PASS")
        return {"scores": {"factuality": 5, "completeness": 4, "clarity": 4},
                "total": 13, "issues": [], "pass": True}

    def refine(task: str, draft: str, issues: list[str]) -> str:
        print(f"→ Refine (mock): sửa theo {len(issues)} issues")
        return ("Brief 5 gạch: (1) agent = LLM + loop + tool; (2) planning tách mục tiêu thành bước; "
                "(3) executor chạy từng bước, replan khi fail; (4) reflection tự chấm theo rubric "
                "15 điểm rồi refine; (5) điểm dừng: rubric pass hoặc điểm không tăng.")


# --- Orchestration dùng chung: *_fn để nhúng hàm giả khi self-test, không cần API ---

def run_plan(goal: str, max_replans: int = 2,
             make_plan_fn=make_plan, execute_fn=execute_step, replan_fn=replan) -> list[str]:
    steps, results, done, replans = make_plan_fn(goal), [], [], 0
    while steps:
        step = steps.pop(0)
        try:
            outcome = execute_fn(step, results)
            results.append(outcome)
            done.append(step)
        except Exception as e:
            replans += 1
            if replans > max_replans:  # van an toàn — không có là lặp vô tận
                raise RuntimeError(f"Replan vượt {max_replans} lần: {e}") from e
            steps = replan_fn(goal, step, str(e), done, [s["action"] for s in steps])
    return results

def reflect_loop(task: str, max_rounds: int = 3,
                 generate_fn=generate, critique_fn=critique, refine_fn=refine) -> tuple[str, int]:
    draft = generate_fn(task)
    prev_total = 0
    for round_no in range(1, max_rounds + 1):
        fb = critique_fn(task, draft)
        if fb["pass"]:
            return draft, round_no  # stop condition chính: rubric pass
        if prev_total and fb["total"] <= prev_total:
            break  # stop condition phụ: điểm không tăng — thêm vòng chỉ đốt tiền
        prev_total = fb["total"]
        draft = refine_fn(task, draft, fb["issues"])
    return draft, round_no


# --- Mock run: in lại luồng demo trong bài ---

def mock_run() -> None:
    _critique_round[0] = 0
    print("=" * 60)
    print("MOCK MODE 1 — Planning: decompose → execute → replan khi fail")
    print("=" * 60)
    results = run_plan("Tổng hợp 3 bài báo thành brief 5 gạch đầu dòng")
    print(f"Executor chạy xong {len(results)} bước. Kết quả cuối:\n  {results[-1]}")
    print("=" * 60)
    print("MOCK MODE 2 — Reflection: generate → critique → refine")
    print("=" * 60)
    draft, rounds = reflect_loop("Viết brief 5 gạch đầu dòng tóm tắt 3 bài báo cho lãnh đạo")
    print(f"Dừng sau {rounds} vòng — rubric pass.")
    print(f"Bản cuối:\n  {draft}")


# --- Self-test: assert hành vi, không gọi API ---

def self_test() -> None:
    # 1) parse_steps: JSON đúng trả list; JSON lệch (thiếu key "steps") raise lỗi rõ ràng
    ok = parse_steps('{"steps": [{"id": 1, "action": "a", "expected": "b"}]}')
    assert isinstance(ok, list) and ok[0]["action"] == "a"
    for bad in ('{"bước": []}', "{}", "không phải json"):
        try:
            parse_steps(bad)
        except ValueError as e:
            assert "steps" in str(e) or "JSON" in str(e), f"lỗi phải nói rõ: {e}"
        else:
            raise AssertionError(f"parse_steps phải raise với đầu vào lệch: {bad!r}")

    # 2) run_plan: executor luôn raise -> replan đúng max_replans lần rồi RuntimeError
    replan_calls = [0]

    def execute_fail(step, ctx):
        raise RuntimeError("tool không tồn tại")

    def replan_ok(goal, failed, error, done, remaining):
        replan_calls[0] += 1
        return [{"id": 1, "action": "thử lại", "expected": "y"}]

    try:
        run_plan("mục tiêu", max_replans=2,
                 make_plan_fn=lambda g: [{"id": 1, "action": "x", "expected": "y"}],
                 execute_fn=execute_fail, replan_fn=replan_ok)
    except RuntimeError as e:
        assert "Replan vượt 2 lần" in str(e)
    else:
        raise AssertionError("run_plan phải raise RuntimeError khi vượt max_replans")
    assert replan_calls[0] == 2, f"phải replan đúng max_replans lần, thực tế {replan_calls[0]}"

    # 3) reflect_loop: critique luôn fail + điểm không tăng -> break sớm trước max_rounds
    def crit_stall(task, draft):
        return {"total": 9, "issues": ["x"], "pass": False}

    draft, rounds = reflect_loop(
        "t", max_rounds=3, generate_fn=lambda t: "nháp",
        critique_fn=crit_stall, refine_fn=lambda t, d, i: d + "+")
    assert (rounds, draft) == (2, "nháp+"), (rounds, draft)

    # 3b) critique luôn fail nhưng điểm tăng dần -> dừng đúng max_rounds
    score = [8]

    def crit_rise(task, draft):
        score[0] += 1
        return {"total": score[0], "issues": ["x"], "pass": False}

    _, rounds2 = reflect_loop(
        "t", max_rounds=3, generate_fn=lambda t: "nháp",
        critique_fn=crit_rise, refine_fn=lambda t, d, i: d)
    assert rounds2 == 3, f"điểm tăng phải chạy đủ max_rounds, thực tế {rounds2}"

    print("Self-test bai-3: PASS — parse_steps, van an toàn max_replans, stop condition reflect_loop")


if __name__ == "__main__":
    self_test()
    if MOCK:
        mock_run()
    else:
        # Live mode — demo đúng luồng trong bài
        results = run_plan("Tổng hợp 3 bài báo thành brief 5 gạch đầu dòng")
        print(f"\nPlanning xong: {len(results)} bước.")
        final, rounds = reflect_loop("Viết brief 5 gạch đầu dòng tóm tắt 3 bài báo cho lãnh đạo")
        print(f"Reflection xong sau {rounds} vòng. Bản cuối:\n{final}")
