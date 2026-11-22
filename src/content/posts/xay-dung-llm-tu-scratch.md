---
title: "Xây dựng LLM từ scratch: học tokenization, attention, pretraining bằng cách tự viết từng tầng"
description: "Bài học elearning dựa trên phương pháp Build a Large Language Model (From Scratch) của Sebastian Raschka — repo 108.000 sao: lộ trình từ tokenization đến pretraining và fine-tuning, kèm khái niệm cốt lõi diễn giải và checklist thực hành."
topic: "generative-ai-llm"
date: "2026-11-19"
cover: "/images/covers/posts/xay-dung-llm-tu-scratch.jpg"
views: 180
faq:
  - q: "Xây LLM từ scratch cần máy mạnh không?"
    a: "Với một GPT kiến trúc nhỏ (khoảng 124 triệu tham số) bạn có thể pretrain trên GPU nội bộ hoặc Google Colab trong vài giờ với dataset vừa phải. Mục tiêu học là hiểu cơ chế, không phải cạnh đua benchmark — scale lớn chỉ cần khi làm sản phẩm thật."
  - q: "Khác gì với dùng thư viện Hugging Face?"
    a: "Hugging Face cho bạn model làm xong; từ scratch cho bạn hiểu model làm thế nào. Sau khóa này bạn đọc được mã nguồn transformers, debug lỗi attention shape, và tự tin tùy biến kiến trúc — kỹ năng mà chỉ gọi pre-trained model không cho được."
  - q: "Nên có nền tảng gì trước khi học?"
    a: "Python thành thạo (class, generator, context manager), đại số tuyến tính cơ bản (nhân ma trận, dot product) và lý thuyết xác suất entry-level. Chưa cần biết PyTorch trước — phần dẫn nhập đã dạy đủ tensor operations."
---

Câu hỏi phổ biến nhất của người học LLM: *"Dùng API thì thoải mái rồi, cần gì phải tự xây?"* Câu trả lời nằm ở chỗ khác: bạn không xây LLM từ đầu để có model dùng — bạn xây để **đọc được code của mọi framework**, debug được lỗi attention shape lúc 2h sáng, và hiểu vì sao fine-tuning có tác dụng mà RAG không.

Bài học này dẫn theo phương pháp của cuốn *Build a Large Language Model (From Scratch)* của Sebastian Raschka — kèm repo thực hành [LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) trên GitHub, hiện **108.000+ sao và vẫn cập nhật đều đặn** (verify 11/2026) — là tài nguyên được đánh giá cao nhất trong nhóm học LLM toàn hệ Awesome lists.

<div style="margin:1.6em 0;">
  <span class="level-badge level-badge--adv">🔴 Nâng cao</span>
  <span class="level-badge">🧩 Cần Python thành thạo</span>
  <span class="level-badge">⏱️ 2–3 tháng (10 giờ/tuần)</span>
</div>

## Bạn sẽ học được gì

<div class="lesson-grid">
  <div class="lesson-card">
    <div class="lc-icon">🔤</div>
    <p class="lc-title">Pipeline dữ liệu</p>
    <p class="lc-desc">Tokenization, embedding, attention — viết tay từng khối với PyTorch.</p>
  </div>
  <div class="lesson-card">
    <div class="lc-icon">⚙️</div>
    <p class="lc-title">Vòng pretraining</p>
    <p class="lc-desc">Loss, optimizer, learning rate scheduling, checkpoint — vòng lặp train một GPT nhỏ.</p>
  </div>
  <div class="lesson-card">
    <div class="lc-icon">🎯</div>
    <p class="lc-title">Fine-tuning</p>
    <p class="lc-desc">Instruction fine-tuning và classification fine-tuning trên model đã pretrain.</p>
  </div>
  <div class="lesson-card">
    <div class="lc-icon">🧠</div>
    <p class="lc-title">Tư duy kiến trúc</p>
    <p class="lc-desc">Đọc hiểu mã nguồn Hugging Face, GPT-2, Llama sau khi tự viết một lần.</p>
  </div>
</div>

## Lộ trình các phần học

<ol class="steps">
  <li>
    <p class="st-title">Phần 1 — Làm việc với text data</p>
    <p class="st-desc">Biến văn bản thành token ID bằng byte pair encoding (BPE), tạo input–target pairs cho training, embedding với positional information.</p>
  </li>
  <li>
    <p class="st-title">Phần 2 — Khối attention</p>
    <p class="st-desc">Viết causal self-attention từ dot product thuần, thêm masked attention, multi-head attention, rồi so sánh với triển khai tối ưu của PyTorch.</p>
  </li>
  <li>
    <p class="st-title">Phần 3 — Lắp ráp GPT architecture</p>
    <p class="st-desc">Layer normalization, feed forward với GELU, residual connections — ghép thành block, lặp N block thành model hoàn chỉnh có thể sinh text.</p>
  </li>
  <li>
    <p class="st-title">Phần 4 — Pretraining trên unlabeled data</p>
    <p class="st-desc">Cross-entropy loss, AdamW optimizer, human evaluation qua text generation, load weight GPT-2 để so sánh kết quả.</p>
  </li>
  <li>
    <p class="st-title">Phần 5 — Fine-tuning cho ứng dụng cụ thể</p>
    <p class="st-desc">Hai hướng: classification fine-tuning (phân loại spam) và instruction fine-tuning (làm model theo chỉ dẫn) — kèm đánh giá bằng LLM-as-a-judge.</p>
  </li>
</ol>

## Khái niệm cốt lõi diễn giải

<div class="concept-card">
  <div class="cc-head">
    <span class="cc-icon">🔤</span>
    <h3 class="cc-name">Tokenization là bước quy đổi</h3>
  </div>
  <div class="cc-body">
    <p>Model không đọc chữ — nó đọc số. Tokenizer là bảng quy đổi từ chuỗi ký tự sang số nguyên, và điểm hay của BPE là bảng này tự học từ corpus: ký tự hay đi cùng nhau gộp thành một token. Đây là lý do token không trùng khớp từ tiếng — cùng một câu Việt hóa có thể tốn token nhiều hơn tiếng Anh.</p>
  </div>
</div>

<div class="concept-card">
  <div class="cc-head">
    <span class="cc-icon">👁️</span>
    <h3 class="cc-name">Self-attention: mỗi token "nhìn" các token khác</h3>
  </div>
  <div class="cc-body">
    <p>Mỗi token được chiếu thành 3 vector: query (tôi cần gì), key (tôi có gì), value (tôi mang gì). Attention score là query của một token chấm product với key của mọi token trước đó — sau đó softmax thành trọng số để trộn value. Mask causal đảm bảo token không nhìn thấy tương lai, giữ tính autoregressive khi sinh text.</p>
  </div>
</div>

<div class="concept-card">
  <div class="cc-head">
    <span class="cc-icon">🔗</span>
    <h3 class="cc-name">Residual connection giữ gradient sống sót</h3>
  </div>
  <div class="cc-body">
    <p>Mỗi sub-layer thêm output vào input gốc thay vì thay thế: <code>x = x + f(x)</code>. Nghĩa là gradient có đường tắt quay về đầu network, giúp train network sâu mà không bị vanishing gradient. Đây là phát minh cho phép network có hàng chục block như hiện nay.</p>
  </div>
</div>

## Checklist thực hành

<ul class="checklist">
  <li>Cài PyTorch và clone repo thực hành, chạy được notebook đầu tiên trên Colab hoặc máy local</li>
  <li>Viết lại BPE tokenizer của chính mình (không copy) — test với một đoạn tiếng Việt xem tốn bao nhiêu token</li>
  <li>Triển khai causal self-attention với chiều shape `(B, num_heads, seq_len, head_dim)` vẽ ra giấy trước khi code</li>
  <li>Pretrain một GPT nhỏ (124M tham số) trên corpus vừa phải vài giờ GPU</li>
  <li>Fine-tune model cho một tác vụ cụ thể bạn chọn (classification hoặc instruction)</li>
</ul>

<div class="quiz">
  <p class="quiz-label">Kiểm tra nhanh</p>
  <details>
    <summary>Vì sao cần masked (causal) attention khi pretrain một GPT?</summary>
    <p class="q-answer"><strong>Đáp án:</strong> Để giữ tính autoregressive — khi sinh text, token thứ n không được biết thông tin token phía sau. Nếu cho nhìn thấy tương lai, model sẽ học "bịa" mapping không dùng được lúc inference.</p>
  </details>
  <details>
    <summary>Khi nào chọn classification fine-tuning thay vì instruction fine-tuning?</summary>
    <p class="q-answer"><strong>Đáp án:</strong> Khi bài toán có nhãn cố định và bạn cần accuracy cao trên nhãn đó (phân loại spam, sentiment). Instruction fine-tuning mạnh hơn cho tác vụ mở — nhưng tốn dữ liệu và chi phí train hơn.</p>
  </details>
</div>

<div class="callout callout--tip">
  <span class="co-icon">💡</span>
  <div class="co-body">
    <span class="co-title">Cách học hiệu quả nhất với tài liệu này</span>
    <p>Đọc từng phần → gõ code theo → <strong>xóa đi viết lại không nhìn</strong> → so kết quả output với reference. Phần cuối mỗi chương đều có exercise — bỏ qua exercise là bạn chỉ đọc hiểu, chưa làm được.</p>
  </div>
</div>

Đọc song song bài [LLM hoạt động như thế nào?](/bai-viet/llm-hoat-dong-nhu-the-nao/) để có bức tranh khái niệm trước khi vào code, và [Karpathy Zero to Hero](/bai-viet/karpathy-zero-to-hero/) cho phần video bổ trợ.

<div class="src-grid">
  <a class="src-card" href="https://github.com/rasbt/LLMs-from-scratch">
    <span class="sc-tag">Repo chính</span>
    <p class="sc-name">rasbt/LLMs-from-scratch</p>
    <p class="sc-desc">108k sao — notebooks, exercises, solutions cho từng phần.</p>
  </a>
  <a class="src-card" href="https://www.manning.com/books/build-a-large-language-model-from-scratch">
    <span class="sc-tag">Sách gốc</span>
    <p class="sc-name">Build a Large Language Model (From Scratch)</p>
    <p class="sc-desc">Manning — Sebastian Raschka. Bìa là nguồn tham khảo chính thức.</p>
  </a>
</div>
