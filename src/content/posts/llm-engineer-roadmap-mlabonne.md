---
title: "Lộ trình LLM Engineer: curriculum 3 phần từ foundation đến deployment (llm-course mlabonne)"
description: "Bài học elearning phân tích curriculum llm-course của Maxime Labonne (85.000 sao GitHub): ba phần Machine Learning fundamentals, LLM Scientist và LLM Engineer — kèm kỹ năng từng phần và lộ trình thực hành bằng notebook."
topic: "lap-trinh-va-cong-nghe"
date: "2026-11-19"
cover: "/images/covers/posts/llm-engineer-roadmap-mlabonne.jpg"
views: 165
faq:
  - q: "llm-course phù hợp với ai?"
    a: "Developer hoặc data scientist đã biết Python, muốn chuyển hướng làm LLM Engineer. Curriculum chia làm ba phần nên có thể vào đúng phần phù hợp trình độ hiện tại — không bắt buộc học tuần tự nếu đã có nền ML."
  - q: "Học llm-course bao lâu thì xong?"
    a: "Với 10 giờ/tuần: phần foundation khoảng 3–4 tuần, LLM Scientist 6–8 tuần, LLM Engineer 6–8 tuần. Tổng khoảng 4–5 tháng. Có notebook Colab sẵn nên thời gian cài môi trường gần như bằng không."
  - q: "llm-course có phải khóa học chính thống không?"
    a: "Đây là open-source curriculum được cộng đồng duy trì (85.000+ sao), tác giả Maxime Labonne là LLM engineer có tên tuổi trong cộng đồng open-source. Nội dung cập nhật liên tục — điểm mạnh hơn khóa video cố định là không bị lỗi thời."
---

Khác với các khóa học dẫn bạn từng bước, [llm-course](https://github.com/mlabonne/llm-course) của Maxime Labonne là một **roadmap nghề nghiệp dạng curriculum mở**: 85.000+ sao trên GitHub, cập nhật liên tục (verify 11/2026), mỗi phần là một kỹ năng có checklist + notebook Colab thực hành. Đây là tài nguyên được cộng đồng Awesome-LLM xếp đầu trong nhóm roadmap LLM.

Ưu điểm lớn nhất: bạn luôn biết **mình đang ở đâu** trên bản đồ kỹ năng LLM Engineer, và thiếu gì thì đi lấp chỗ đó thay vì học lan man.

<div style="margin:1.6em 0;">
  <span class="level-badge level-badge--mid">🟡 Trung cấp trở lên</span>
  <span class="level-badge">🐍 Cần Python</span>
  <span class="level-badge">⏱️ 4–5 tháng trọn lộ trình</span>
</div>

## Cấu trúc curriculum: ba phần

<div class="lesson-grid">
  <div class="lesson-card">
    <div class="lc-icon">🧱</div>
    <p class="lc-title">Phần 1 — ML Fundamentals</p>
    <p class="lc-desc">Đại số tuyến tính, PyTorch, NLP cơ bản, khái niệm embedding và machine learning nền tảng.</p>
  </div>
  <div class="lesson-card">
    <div class="lc-icon">🔬</div>
    <p class="lc-title">Phần 2 — LLM Scientist</p>
    <p class="lc-desc">Hiểu và tạo LLM: kiến trúc, pretraining, fine-tuning, quantization, evaluation.</p>
  </div>
  <div class="lesson-card">
    <div class="lc-icon">🚀</div>
    <p class="lc-title">Phần 3 — LLM Engineer</p>
    <p class="lc-desc">Xây và vận hành ứng dụng LLM: RAG, agents, inference optimization, deployment.</p>
  </div>
</div>

## Kỹ năng đáng chú ý từng phần

<ol class="steps">
  <li>
    <p class="st-title">Phần 1 — Nền móng không được bỏ qua</p>
    <p class="st-desc">Tensor operations PyTorch, khái niệm neural network từ linear layer đến attention, tokenization, pipeline NLP truyền thống. Nếu đã học CS231n hoặc Deep Learning Specialization, phần này có thể lướt nhanh làm kiểm tra.</p>
  </li>
  <li>
    <p class="st-title">Phần 2 — Đi từ kiến trúc đến model "học nghề"</p>
    <p class="st-desc">Kiến trúc transformer chi tiết, kỹ thuật fine-tuning (full fine-tuning, LoRA, QLoRA), quantization (đưa model lớn chạy trên GPU nhỏ), DPO/RLHF cho alignment, và benchmark để biết model tốt hơn theo tiêu chí nào.</p>
  </li>
  <li>
    <p class="st-title">Phần 3 — Đưa model vào ứng dụng thật</p>
    <p class="st-desc">RAG (retrieval augmented generation), các mẫu agentic AI, prompt engineering có hệ thống, inference optimization (vLLM, streaming, batching), và deployment pattern cho production.</p>
  </li>
</ol>

## Khái niệm đáng học kỹ trong phần 2

<div class="concept-card">
  <div class="cc-head">
    <span class="cc-icon">📦</span>
    <h3 class="cc-name">Quantization: nén model mà giữ chất lượng</h3>
  </div>
  <div class="cc-body">
    <p>Weight của model mặc định lưu ở 16 bit; quantization nén xuống 8 hoặc 4 bit. Mục tiêu: chạy model 70B trên một GPU 48GB thay vì cần cả cụm. Điểm học kỹ là trade-off giữa mức nén và độ suy giảm chất lượng — không phải nén càng mạnh càng tốt.</p>
  </div>
</div>

<div class="concept-card">
  <div class="cc-head">
    <span class="cc-icon">🎛️</span>
    <h3 class="cc-name">LoRA: fine-tune rẻ mà hiệu quả</h3>
  </div>
  <div class="cc-body">
    <p>Thay vì cập nhật toàn bộ weight (tốn bộ nhớ và thời gian), LoRA đóng băng model gốc và chỉ train một cặp ma trận nhỏ thêm vào. Kết quả: fine-tune một model lớn trên GPU cá nhân là khả thi, và adapter có thể gỡ ra lắp vào tùy tác vụ.</p>
  </div>
</div>

<div class="concept-card">
  <div class="cc-head">
    <span class="cc-icon">🧭</span>
    <h3 class="cc-name">RAG: cho model tra cứu thay vì học thuộc</h3>
  </div>
  <div class="cc-body">
    <p>Thay vì fine-tune để model nhớ kiến thức (đắt, dễ lỗi thời), RAG truy xuất tài liệu liên quan từ database và đưa vào context lúc trả lời. Là kỹ năng bắt buộc trong mọi job description LLM Engineer hiện nay — và là chủ đề chúng tôi có loạt bài riêng về RAG nâng cao.</p>
  </div>
</div>

## Checklist thực hành

<ul class="checklist">
  <li>Lướt qua phần 1 với checklist tự đánh giá — đánh dấu kỹ năng đã có, thiếu gì bổ sung nấy</li>
  <li>Chạy notebook fine-tuning LoRA trên một open model nhỏ (7B) bằng Colab free</li>
  <li>Quantize model đã fine-tune xuống 4-bit, so sánh câu trả lời trước và sau</li>
  <li>Xây một RAG pipeline đơn giản với embedding + vector store, đo độ chính xác retrieval</li>
  <li>Deploy model lên API endpoint và đo latency, throughput với batch size khác nhau</li>
</ul>

<div class="quiz">
  <p class="quiz-label">Kiểm tra nhanh</p>
  <details>
    <summary>Khi nào chọn RAG thay vì fine-tuning?</summary>
    <p class="q-answer"><strong>Đáp án:</strong> Khi kiến thức thay đổi thường xuyên hoặc cần dẫn nguồn (citations) — RAG cập nhật bằng cách thêm tài liệu, không cần train lại. Fine-tuning phù hợp khi cần thay đổi hành vi, style hoặc format đầu ra, không phải kiến thức.</p>
  </details>
  <details>
    <summary>QLoRA khác LoRA chỗ nào?</summary>
    <p class="q-answer"><strong>Đáp án:</strong> QLoRA quantize model gốc xuống 4-bit rồi mới train adapter LoRA trên đó — giảm mạnh yêu cầu bộ nhớ, cho phép fine-tune model 70B trên GPU một cá nhân. Đổi lại là một chút overhead dequantize lúc tính toán.</p>
  </details>
</div>

<div class="callout callout--warn">
  <span class="co-icon">⚠️</span>
  <div class="co-body">
    <span class="co-title">Đừng học theo thứ tự cứng nhắc</span>
    <p>Curriculum được thiết kế tuần tự nhưng cách dùng hiệu quả là <strong>đi từ nhu cầu thật</strong>: cần deploy ứng dụng thì vào thẳng phần 3, thiếu nền thì quay lại phần 1. Chỉ phần 2 cần học kỹ theo trình tự vì các kỹ năng xếp lớp lên nhau.</p>
  </div>
</div>

Kết hợp với bài [Xây dựng LLM từ scratch](/bai-viet/xay-dung-llm-tu-scratch/) để hiểu bên trong trước khi học phần tuning, và [Roadmap AI Engineer 2026](/bai-viet/ai-engineer-roadmap-2026/) cho phần agent production.

<div class="src-grid">
  <a class="src-card" href="https://github.com/mlabonne/llm-course">
    <span class="sc-tag">Repo chính</span>
    <p class="sc-name">mlabonne/llm-course</p>
    <p class="sc-desc">85k sao — roadmap + notebooks, cập nhật liên tục.</p>
  </a>
  <a class="src-card" href="/bai-viet/rag-nang-cao-cam-nang/">
    <span class="sc-tag">LearnWithHuy</span>
    <p class="sc-name">Lộ trình RAG nâng cao</p>
    <p class="sc-desc">Đi sâu phần RAG của curriculum này bằng tiếng Việt.</p>
  </a>
</div>
