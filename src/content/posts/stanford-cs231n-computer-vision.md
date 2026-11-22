---
title: "Stanford CS231n: kinh điển CNN và computer vision — khóa hình thành thế hệ vision engineer"
description: "Bài học elearning về Stanford CS231n — CNNs for Visual Recognition: nội dung cốt lõi, vì sao đây là khóa tham chiếu cho computer vision, và cách học theo tài liệu gốc free."
topic: "machine-learning"
date: "2026-11-19"
cover: "/images/covers/posts/stanford-cs231n-computer-vision.jpg"
views: 130
faq:
  - q: "CS231n có cần thiết nếu tôi không làm computer vision?"
    a: "Phần đầu (CNN, training tricks, architectures) là nền chung cho mọi deep learning — transformer cũng sinh ra từ dòng nghiên cứu vision. Nếu bạn theo hướng LLM, Course này vẫn đáng học để hiểu attention ra đời từ đâu; chỉ phần chuyên sâu detection/segmentation là có thể bỏ."
  - q: "Tài liệu CS231n có free không?"
    a: "Có — course notes, slides và các phiên bản lecture video cũ đều public miễn phí trên trang course. Điểm hạn chế: video lecture chính thức năm 2017, phần sau của lĩnh vực thay đổi nhiều nên cần bổ sung tài liệu mới."
  - q: "Nền tảng cần có trước khi học?"
    a: "Linear algebra, calculus cơ bản (đạo hàm theo ma trận), Python + NumPy. Nếu đã học Deep Learning Specialization Course 1–2 thì đủ nền vào CS231n."
---

Nếu Deep Learning Specialization là chuẩn mực nền tảng thì [Stanford CS231n](http://cs231n.stanford.edu/) — CNNs for Visual Recognition — là chuẩn mực **chuyên sâu**: khóa học được biên tập kỹ lưỡng nhất trong nhóm computer vision, được awesome-machine-learning liệt kê kèm nhiều phiên bản video, và là nguồn hình thành hàng thế hệ vision engineer. Giảng viên qua các năm gồm những nhà nghiên cứu làm chính các kiến trúc được dạy trong khóa.

Đặc điểm nổi bật: notes của khóa được viết như **tài liệu tham khảo học thuật** — đọc standalone được, không cần xem video. Đây là lý do khóa vẫn được nhắc dù video chính thức cũ.

<div style="margin:1.6em 0;">
  <span class="level-badge level-badge--mid">🟡 Trung cấp → Nâng cao</span>
  <span class="level-badge">🏛️ Stanford curriculum</span>
  <span class="level-badge">⏱️ 8–12 tuần</span>
</div>

## Nội dung cốt lõi theo khối

<ol class="steps">
  <li>
    <p class="st-title">Khối 1 — Từ image classification đến CNN</p>
    <p class="st-desc">Linear classifier trên ảnh, vì sao convolution thắng (parameter sharing + translation equivariance), pooling, và CNN architecture cơ bản. Viết cả forward và backward bằng NumPy trong assignment.</p>
  </li>
  <li>
    <p class="st-title">Khối 2 — Training dynamics</p>
    <p class="st-desc">Activation functions, BatchNorm, dropout, data augmentation, transfer learning — khối "vệ sinh" mà mọi project vision thật đều phụ thuộc.</p>
  </li>
  <li>
    <p class="st-title">Khối 3 — Kiến trúc kinh điển</p>
    <p class="st-desc">AlexNet, VGG, ResNet với residual connection (phát minh mở đường cho transformer), rồi Inception và efficiency tricks.</p>
  </li>
  <li>
    <p class="st-title">Khối 4 — Beyond classification</p>
    <p class="st-desc">Object detection, segmentation, và ở các phiên bản mới: attention, ViT, self-supervised learning — phần trực tiếp nối vào thế giới LLM.</p>
  </li>
</ol>

## Ba phát minh học kỹ nhất trong khóa

<div class="concept-card">
  <div class="cc-head">
    <span class="cc-icon">🔬</span>
    <h3 class="cc-name">Convolution: chia sẻ tham số theo giả định cấu trúc</h3>
  </div>
  <div class="cc-body">
    <p>Một kernel nhỏ quét khắp ảnh với cùng trọng số — model nhận diện "viền" ở góc nào cũng giống nhau. Vì chia sẻ trọng số, số tham số giảm hàng bậc so với fully-connected trên ảnh, và model học được bất biến không gian mà fully-connected phải tự khám phá.</p>
  </div>
</div>

<div class="concept-card">
  <div class="cc-head">
    <span class="cc-icon">🌉</span>
    <h3 class="cc-name">ResNet: shortcut connection cho network siêu sâu</h3>
  </div>
  <div class="cc-body">
    <p>Trước ResNet, network sâu hơn 20 tầng dễ train không nổi vì gradient suy kiệt. Residual connection cho phép mỗi block chỉ học "phần chỉnh sửa" (<code>f(x)</code>) thay vì toàn bộ transformation — gradient có đường tắt qua shortcut. Cơ chế này được transformer kế thừa nguyên vẹn.</p>
  </div>
</div>

<div class="concept-card">
  <div class="cc-head">
    <span class="cc-icon">🖼️</span>
    <h3 class="cc-name">Transfer learning trên vision = prototype của fine-tuning LLM</h3>
  </div>
  <div class="cc-body">
    <p>Pretrain trên ImageNet lớn, fine-tune tầng cuối cho task nhỏ — mô hình tư duy này giờ là chuẩn của cả thế giới LLM (pretrain → fine-tune/instruct-tune). Hiểu vision transfer learning nghĩa là hiểu nguyên mẫu của mọi quy trình model hiện đại.</p>
  </div>
</div>

## Checklist thực hành

<ul class="checklist">
  <li>Làm assignment 1: implement kNN, SVM, softmax classifier bằng NumPy — nền đọc hiểu phần sau</li>
  <li>Assignment 2: viết CNN forward + backward bằng tay, so với PyTorch autograd</li>
  <li>Transfer learning một model pretrained cho dataset domain của bạn, thử frozen vs fine-tune toàn bộ</li>
  <li>Đọc bài ResNet gốc một lần để hiểu động cơ phát minh — rồi quay lại notes của khóa</li>
  <li>Phần sau: thử ViT pretrained trên bài toán vision của bạn và so với CNN</li>
</ul>

<div class="quiz">
  <p class="quiz-label">Kiểm tra nhanh</p>
  <details>
    <summary>Vì sao Residual connection giúp train network sâu?</summary>
    <p class="q-answer"><strong>Đáp án:</strong> Gradient qua phép cộng được truyền nguyên vẹn về phía trước (đạo hàm của x + f(x) theo x là 1 + f'(x)) — mỗi block chỉ cần học phần dư, đường gradient chính luôn thông thoáng. Không có shortcut, gradient phải xuyên qua mọi nonlinear layer và suy giảm dần.</p>
  </details>
  <details>
    <summary>ViT khác CNN ở giả định nào về ảnh?</summary>
    <p class="q-answer"><strong>Đáp án:</strong> CNN bake-in giả định cục bộ (kernel nhìn lân cận, chia sẻ trọng số). ViT bỏ cả hai — cắt ảnh thành patch, coi mỗi patch như một token và để attention tự học quan hệ toàn cục. Đổi lại cần nhiều dữ liệu pretrain hơn, nhưng linh hoạt hơn khi data đủ lớn.</p>
  </details>
</div>

<div class="callout callout--info">
  <span class="co-icon">📚</span>
  <div class="co-body">
    <span class="co-title">Cách dùng CS231n hiệu quả nhất</span>
    <p>Đọc <strong>course notes theo thứ tự khối</strong> làm trục chính (viết chuẩn tài liệu tham khảo), xem lecture video bản 2017 bổ trợ phần giải thích trực quan, làm assignment bằng tay. Phần ngoài video cũ — cập nhật bằng tài liệu ViT/self-supervised riêng.</p>
  </div>
</div>

Bài liên quan: [Deep Learning Specialization](/bai-viet/deep-learning-specialization-andrew-ng/) cho nền khái niệm trước khi vào CS231n, [fast.ai](/bai-viet/fastai-practical-deep-learning/) cho hướng thực hành nhanh hơn.

<div class="src-grid">
  <a class="src-card" href="http://cs231n.stanford.edu/">
    <span class="sc-tag">Course chính thức</span>
    <p class="sc-name">cs231n.stanford.edu</p>
    <p class="sc-desc">Syllabus, notes, assignment — public mỗi năm học.</p>
  </a>
  <a class="src-card" href="https://cs231n.github.io/">
    <span class="sc-tag">Notes standalone</span>
    <p class="sc-name">cs231n.github.io</p>
    <p class="sc-desc">Bản notes đọc độc lập — tài liệu tham khảo giá trị nhất của khóa.</p>
  </a>
</div>
