# 🗄️ Database Schema Documentation

Tài liệu chi tiết về cấu trúc database cho IELTS AI Platform (B2B).

## 📑 Table of Contents

- [Overview](#overview)
- [ERD Diagram](#erd-diagram)
- [Core Tables](#core-tables)
- [Content Tables](#content-tables)
- [Submission Tables](#submission-tables)
- [Payment Tables](#payment-tables)
- [Relationships](#relationships)
- [Indexes](#indexes)
- [Sample Queries](#sample-queries)

---

## Overview

Database: **MySQL 8.0+**
Charset: **utf8mb4**
Collation: **utf8mb4_unicode_ci**
Total Tables: **16 tables**

---

## ERD Diagram

```
┌──────────────┐
│    users     │ (Admin/Teacher/Student)
│   (role)     │
└──────┬───────┘
       │
       ├─────────────────────────────────────┐
       │                                     │
       │ (teacher_id)                        │ (created_by)
       ▼                                     ▼
┌─────────────────┐                 ┌──────────────────┐
│ teacher_classes │                 │  writing_tasks   │
│   (code)        │                 │  reading_passages│
└────────┬────────┘                 │  listening_...   │
         │                          │  speaking_topics │
         ├──────────┐               │  (is_public)     │
         │          │               └─────────┬────────┘
         ▼          ▼                         │
┌──────────────┐  ┌────────────┐            │
│ assignments  │  │class_students│           │
│ (polymorphic)│  │            │             │
└──────┬───────┘  └────────────┘            │
       │                                     │
       ▼                                     ▼
┌──────────────────┐              ┌──────────────────┐
│   submissions    │              │   questions      │
│ (writing/speaking)│              │ (MCQ/TrueFalse) │
└──────────────────┘              └──────────────────┘
```

---

## Core Tables

### 1. `users`

Quản lý tất cả users (Admin/Teacher/Student) trong một bảng.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | User ID |
| `email` | VARCHAR(120) UNIQUE | Email đăng nhập |
| `password_hash` | VARCHAR(255) | Bcrypt hashed password |
| `full_name` | VARCHAR(100) | Họ tên đầy đủ |
| `role` | VARCHAR(20) | 'admin', 'teacher', 'student' |
| **Teacher-specific** | | |
| `center_name` | VARCHAR(200) | Tên trung tâm |
| `phone` | VARCHAR(20) | Số điện thoại |
| `address` | VARCHAR(500) | Địa chỉ |
| `tax_code` | VARCHAR(50) | Mã số thuế |
| `website` | VARCHAR(200) | Website |
| `approved_at` | DATETIME | Ngày admin duyệt |
| `approved_by` | INT FK(users.id) | Admin đã duyệt |
| **Student-specific** | | |
| `teacher_id` | INT FK(users.id) | Giáo viên của học sinh |
| **Common** | | |
| `credits` | INT DEFAULT 0 | Số credits hiện có |
| `is_active` | BOOLEAN DEFAULT TRUE | Account active? |
| `email_verified` | BOOLEAN DEFAULT FALSE | Email đã verify? |
| `created_at` | DATETIME | Ngày tạo |
| `last_login` | DATETIME | Lần login cuối |

**Indexes:**
- PRIMARY KEY: `id`
- UNIQUE: `email`
- INDEX: `role`, `teacher_id`

**Business Rules:**
- Teachers: `credits` > 0, `approved_at` NOT NULL để được sử dụng
- Students: `credits` luôn = 0, dùng credits của teacher
- Admin: `credits` unlimited (không check)

---

### 2. `teacher_classes`

Lớp học do teacher tạo ra.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Class ID |
| `teacher_id` | INT FK(users.id) | Teacher sở hữu class |
| `name` | VARCHAR(200) | Tên lớp (VD: "IELTS Foundation June 2024") |
| `description` | TEXT | Mô tả lớp |
| `code` | VARCHAR(10) UNIQUE | Mã lớp 6-ký tự (VD: "ABC123") |
| `max_students` | INT NULL | Giới hạn số học sinh (NULL = unlimited) |
| `status` | VARCHAR(20) | 'active', 'archived' |
| `created_at` | DATETIME | Ngày tạo |
| `updated_at` | DATETIME | Ngày cập nhật cuối |

**Indexes:**
- PRIMARY KEY: `id`
- UNIQUE: `code`
- INDEX: `teacher_id`, `status`

**Code Generation:**
- Format: 6 ký tự uppercase A-Z, 0-9
- Example: `ABC123`, `XY7K9P`
- Unique trong toàn hệ thống

---

### 3. `class_students`

Quan hệ Many-to-Many giữa Classes và Students.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Membership ID |
| `class_id` | INT FK(teacher_classes.id) | Class |
| `student_id` | INT FK(users.id) | Student |
| `status` | VARCHAR(20) | 'active', 'removed' |
| `joined_at` | DATETIME | Ngày join |
| `removed_at` | DATETIME NULL | Ngày bị remove |

**Constraints:**
- UNIQUE: (`class_id`, `student_id`) - Một học sinh chỉ join 1 lần
- CASCADE DELETE: Xóa class → xóa tất cả memberships

---

### 4. `assignments`

Bài tập teacher giao cho class.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Assignment ID |
| `teacher_id` | INT FK(users.id) | Teacher tạo assignment |
| `class_id` | INT FK(teacher_classes.id) | Class được giao |
| `title` | VARCHAR(200) | Tiêu đề (VD: "Weekly Writing Task") |
| `description` | TEXT | Hướng dẫn cho học sinh |
| **Polymorphic Content** | | |
| `content_type` | VARCHAR(50) | 'writing_task1', 'writing_task2', 'reading', 'listening', 'speaking' |
| `content_id` | INT | ID của content (không FK, polymorphic) |
| **Settings** | | |
| `due_date` | DATETIME NULL | Deadline (NULL = no deadline) |
| `max_attempts` | INT NULL | Số lần làm tối đa (NULL = unlimited) |
| `time_limit_minutes` | INT NULL | Giới hạn thời gian (minutes) |
| `published` | BOOLEAN DEFAULT TRUE | Published? |
| `created_at` | DATETIME | Ngày tạo |
| `updated_at` | DATETIME | Ngày cập nhật |

**Indexes:**
- PRIMARY KEY: `id`
- INDEX: `teacher_id`, `class_id`, `content_type`

**Polymorphic Design:**
```sql
-- Example: Assignment cho Writing Task
content_type = 'writing_task2'
content_id = 5  -- FK to writing_tasks(id)=5

-- Example: Assignment cho Reading Passage
content_type = 'reading'
content_id = 12  -- FK to reading_passages(id)=12
```

---

### 5. `transactions`

Lịch sử tất cả biến động credits.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Transaction ID |
| `user_id` | INT FK(users.id) | User (teacher hoặc admin) |
| `type` | VARCHAR(20) | 'topup', 'usage', 'refund', 'bonus' |
| `amount` | INT | Số credits (+/- ) |
| `balance_after` | INT | Credits sau transaction |
| **Reference** | | |
| `reference_type` | VARCHAR(50) | 'payment', 'writing', 'speaking', etc. |
| `reference_id` | INT | ID của payment/submission |
| `note` | VARCHAR(200) | Ghi chú |
| `created_at` | DATETIME | Timestamp |

**Indexes:**
- PRIMARY KEY: `id`
- INDEX: `user_id`, `type`, `created_at`

**Example Transactions:**

```sql
-- Teacher mua 500 credits
type='topup', amount=+500, reference_type='payment', reference_id=123

-- Student làm writing task (teacher's credits -1)
type='usage', amount=-1, reference_type='writing', reference_id=456, note='Student: John Doe'

-- Admin refund
type='refund', amount=+50, note='Technical issue'
```

---

### 6. `gemini_usage`

Tracking API costs để monitoring.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Usage ID |
| `user_id` | INT FK(users.id) | User thực hiện (student) |
| `model_name` | VARCHAR(50) | 'gemini-2.0-flash-exp' |
| `input_tokens` | INT | Input tokens count |
| `output_tokens` | INT | Output tokens count |
| `estimated_cost_usd` | DECIMAL(10,6) | Chi phí ước tính ($) |
| `task_type` | VARCHAR(50) | 'writing', 'speaking' |
| `reference_id` | INT | ID của submission |
| `created_at` | DATETIME | Timestamp |

**Cost Calculation:**
```python
# Gemini 2.0 Flash pricing (as of 2024)
INPUT_COST = $0.00001875 / 1K tokens
OUTPUT_COST = $0.000075 / 1K tokens

cost = (input_tokens * INPUT_COST) + (output_tokens * OUTPUT_COST)
```

---

## Content Tables

### 7. `writing_tasks`

Đề Writing Task 1 và Task 2.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Task ID |
| `task_type` | INT | 1 (Task 1) hoặc 2 (Task 2) |
| `question_text` | TEXT | Đề bài |
| `sample_answer` | TEXT NULL | Bài mẫu (optional) |
| `min_words` | INT | Số từ tối thiểu (150/250) |
| `topic` | VARCHAR(100) | Chủ đề (education, environment, ...) |
| `difficulty` | VARCHAR(20) | 'easy', 'intermediate', 'hard' |
| **Ownership** | | |
| `created_by` | INT FK(users.id) | Admin hoặc Teacher |
| `is_public` | BOOLEAN | TRUE = Admin (public), FALSE = Teacher (private) |
| `created_at` | DATETIME | Ngày tạo |

**Indexes:**
- PRIMARY KEY: `id`
- INDEX: `created_by`, `is_public`, `task_type`

---

### 8. `reading_passages`

Bài đọc IELTS với questions.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Passage ID |
| `title` | VARCHAR(200) | Tiêu đề |
| `passage` | TEXT | Nội dung bài đọc |
| `topic` | VARCHAR(100) | Chủ đề |
| `difficulty` | VARCHAR(20) | 'easy', 'intermediate', 'hard' |
| `created_by` | INT FK(users.id) | Admin/Teacher |
| `is_public` | BOOLEAN | Public? |
| `created_at` | DATETIME | Ngày tạo |

---

### 9. `reading_questions`

Câu hỏi cho reading passages.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Question ID |
| `passage_id` | INT FK(reading_passages.id) | Passage |
| `question_number` | INT | Số thứ tự (1, 2, 3, ...) |
| `question_type` | VARCHAR(50) | 'multiple_choice', 'true_false', 'fill_blank' |
| `question_text` | TEXT | Câu hỏi |
| `options` | JSON | Các lựa chọn (MCQ) |
| `correct_answer` | VARCHAR(200) | Đáp án đúng |
| `explanation` | TEXT NULL | Giải thích |

**Example `options` JSON:**
```json
{
  "A": "First option",
  "B": "Second option",
  "C": "Third option",
  "D": "Fourth option"
}
```

---

### 10. `listening_sections`

Audio IELTS Listening.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Section ID |
| `title` | VARCHAR(200) | Tiêu đề |
| `audio_url` | VARCHAR(500) | URL file audio (uploaded) |
| `transcript` | TEXT NULL | Bản transcript |
| `section_number` | INT | Part 1/2/3/4 |
| `difficulty` | VARCHAR(20) | Độ khó |
| `created_by` | INT FK(users.id) | Admin/Teacher |
| `is_public` | BOOLEAN | Public? |
| `is_active` | BOOLEAN | Active? |
| `created_at` | DATETIME | Ngày tạo |

---

### 11. `listening_questions`

Câu hỏi cho listening.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Question ID |
| `section_id` | INT FK(listening_sections.id) | Section |
| `question_number` | INT | Số thứ tự |
| `question_type` | VARCHAR(50) | 'multiple_choice', 'fill_blank' |
| `question_text` | TEXT | Câu hỏi |
| `options` | JSON NULL | Lựa chọn (MCQ) |
| `correct_answer` | VARCHAR(200) | Đáp án |
| `timestamp` | VARCHAR(20) NULL | Thời điểm trong audio (VD: "01:25") |

---

### 12. `speaking_topics`

Chủ đề Speaking.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Topic ID |
| `part` | INT | Part 1/2/3 |
| `topic` | VARCHAR(200) | Chủ đề |
| `question` | TEXT | Câu hỏi |
| `follow_up_questions` | JSON NULL | Câu hỏi follow-up |
| `time_limit_seconds` | INT | Giới hạn thời gian (seconds) |
| `difficulty` | VARCHAR(20) | Độ khó |
| `created_by` | INT FK(users.id) | Admin/Teacher |
| `is_public` | BOOLEAN | Public? |
| `is_active` | BOOLEAN | Active? |
| `created_at` | DATETIME | Ngày tạo |

---

### 13. `vocabulary_topics`

Chủ đề từ vựng.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Topic ID |
| `name` | VARCHAR(200) | Tên chủ đề (VD: "Business English") |
| `description` | TEXT | Mô tả |
| `level` | VARCHAR(20) | 'beginner', 'intermediate', 'advanced' |
| `is_active` | BOOLEAN | Active? |
| `created_at` | DATETIME | Ngày tạo |

---

## Submission Tables

### 14. `writing_submissions`

Bài làm Writing của học sinh.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Submission ID |
| `user_id` | INT FK(users.id) | Student |
| `task_id` | INT FK(writing_tasks.id) | Writing task |
| `assignment_id` | INT FK(assignments.id) NULL | Assignment (nếu là từ assignment) |
| `answer_text` | TEXT | Bài làm của học sinh |
| **AI Grading** | | |
| `band_score` | DECIMAL(2,1) NULL | Overall band (0.0-9.0) |
| `task_achievement` | DECIMAL(2,1) NULL | Task Achievement score |
| `coherence_cohesion` | DECIMAL(2,1) NULL | Coherence & Cohesion |
| `lexical_resource` | DECIMAL(2,1) NULL | Lexical Resource |
| `grammar_accuracy` | DECIMAL(2,1) NULL | Grammar Accuracy |
| `feedback` | TEXT NULL | AI feedback chi tiết |
| `graded_at` | DATETIME NULL | Thời điểm AI chấm xong |
| **Teacher Override** | | |
| `teacher_score` | DECIMAL(2,1) NULL | Điểm teacher chấm (override AI) |
| `teacher_comment` | TEXT NULL | Comment của teacher |
| `created_at` | DATETIME | Ngày submit |

**Indexes:**
- PRIMARY KEY: `id`
- INDEX: `user_id`, `task_id`, `assignment_id`, `created_at`

---

### 15. `reading_attempts`

Lượt làm Reading.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Attempt ID |
| `user_id` | INT FK(users.id) | Student |
| `passage_id` | INT FK(reading_passages.id) | Passage |
| `answers` | JSON | Câu trả lời {question_id: answer} |
| `correct_count` | INT | Số câu đúng |
| `total_questions` | INT | Tổng số câu |
| `band_score` | DECIMAL(2,1) NULL | Band score (auto-calculated) |
| `time_taken_seconds` | INT NULL | Thời gian làm (seconds) |
| `completed_at` | DATETIME | Ngày hoàn thành |

**Example `answers` JSON:**
```json
{
  "1": "A",
  "2": "TRUE",
  "3": "accommodation",
  "4": "FALSE"
}
```

---

### 16. `listening_attempts`

Lượt làm Listening (tương tự reading_attempts).

---

### 17. `speaking_submissions`

Bài làm Speaking (audio recording).

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Submission ID |
| `user_id` | INT FK(users.id) | Student |
| `topic_id` | INT FK(speaking_topics.id) | Topic |
| `assignment_id` | INT FK(assignments.id) NULL | Assignment |
| `audio_url` | VARCHAR(500) | URL file audio đã upload |
| `transcription` | TEXT NULL | Google STT transcription |
| **AI Grading** | | |
| `overall_band` | DECIMAL(2,1) NULL | Overall band |
| `fluency` | DECIMAL(2,1) NULL | Fluency & Coherence |
| `lexical_resource` | DECIMAL(2,1) NULL | Vocabulary |
| `grammar` | DECIMAL(2,1) NULL | Grammar |
| `pronunciation` | DECIMAL(2,1) NULL | Pronunciation |
| `feedback` | TEXT NULL | AI feedback |
| `graded_at` | DATETIME NULL | Ngày chấm |
| `created_at` | DATETIME | Ngày submit |

---

## Payment Tables

### 18. `payment_requests`

Yêu cầu thanh toán từ teachers.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT PRIMARY KEY | Request ID |
| `user_id` | INT FK(users.id) | Teacher |
| `package` | VARCHAR(50) | 'starter', 'pro', 'enterprise' |
| `amount_usd` | DECIMAL(10,2) | Số tiền USD |
| `amount_vnd` | INT | Số tiền VND |
| `credits` | INT | Số credits sẽ nhận |
| `payment_method` | VARCHAR(50) | 'bank_transfer', 'momo' |
| `proof_image_url` | VARCHAR(500) | URL ảnh chứng từ |
| `notes` | TEXT NULL | Ghi chú từ teacher |
| **Admin Processing** | | |
| `status` | VARCHAR(20) | 'pending', 'approved', 'rejected' |
| `admin_id` | INT FK(users.id) NULL | Admin xử lý |
| `admin_note` | TEXT NULL | Ghi chú từ admin |
| `processed_at` | DATETIME NULL | Ngày xử lý |
| `created_at` | DATETIME | Ngày tạo request |

**Status Flow:**
```
pending → (admin review) → approved/rejected
```

---

## Relationships

### User Relationships

```sql
-- Teacher → Students (1:N)
User (teacher) ───< User (students via teacher_id)

-- Teacher → Classes (1:N)
User (teacher) ───< TeacherClass

-- Teacher → Assignments (1:N)
User (teacher) ───< Assignment

-- Student → Submissions (1:N)
User (student) ───< WritingSubmission
User (student) ───< ReadingAttempt
User (student) ───< ListeningAttempt
User (student) ───< SpeakingSubmission

-- User → Transactions (1:N)
User ───< Transaction
```

### Class Relationships

```sql
-- TeacherClass → Students (M:N via ClassStudent)
TeacherClass ───< ClassStudent >─── User (student)

-- TeacherClass → Assignments (1:N)
TeacherClass ───< Assignment
```

### Content → Submissions

```sql
-- Polymorphic relationship via assignment
Assignment (content_type, content_id) → WritingTask/ReadingPassage/...

-- Direct relationships
WritingTask ───< WritingSubmission
ReadingPassage ───< ReadingAttempt
ListeningSection ───< ListeningAttempt
SpeakingTopic ───< SpeakingSubmission
```

---

## Indexes

### Performance Critical Indexes

```sql
-- Users
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_teacher_id ON users(teacher_id);
CREATE INDEX idx_users_email ON users(email);  -- Already UNIQUE

-- TeacherClasses
CREATE INDEX idx_classes_teacher ON teacher_classes(teacher_id);
CREATE INDEX idx_classes_status ON teacher_classes(status);

-- Assignments
CREATE INDEX idx_assignments_class ON assignments(class_id);
CREATE INDEX idx_assignments_teacher ON assignments(teacher_id);
CREATE INDEX idx_assignments_content ON assignments(content_type, content_id);

-- Submissions
CREATE INDEX idx_writing_user_created ON writing_submissions(user_id, created_at);
CREATE INDEX idx_writing_task ON writing_submissions(task_id);
CREATE INDEX idx_reading_user_completed ON reading_attempts(user_id, completed_at);

-- Transactions
CREATE INDEX idx_transactions_user_created ON transactions(user_id, created_at);
CREATE INDEX idx_transactions_type ON transactions(type);
```

---

## Sample Queries

### 1. Lấy tất cả students của một teacher

```sql
SELECT u.*
FROM users u
WHERE u.teacher_id = 123  -- Teacher ID
  AND u.role = 'student'
  AND u.is_active = TRUE;
```

### 2. Lấy tất cả classes và số học sinh

```sql
SELECT
    tc.id,
    tc.name,
    tc.code,
    COUNT(DISTINCT cs.student_id) as student_count
FROM teacher_classes tc
LEFT JOIN class_students cs ON tc.id = cs.class_id AND cs.status = 'active'
WHERE tc.teacher_id = 123
  AND tc.status = 'active'
GROUP BY tc.id;
```

### 3. Lấy assignments chưa làm của student

```sql
SELECT
    a.id,
    a.title,
    a.due_date,
    tc.name as class_name,
    a.content_type
FROM assignments a
JOIN teacher_classes tc ON a.class_id = tc.id
JOIN class_students cs ON cs.class_id = tc.id
WHERE cs.student_id = 456  -- Student ID
  AND cs.status = 'active'
  AND a.published = TRUE
  AND NOT EXISTS (
      SELECT 1 FROM writing_submissions ws
      WHERE ws.assignment_id = a.id AND ws.user_id = 456
  )
ORDER BY a.due_date ASC;
```

### 4. Tính tổng credits usage của teacher trong tháng

```sql
SELECT
    SUM(ABS(amount)) as total_credits_used
FROM transactions
WHERE user_id = 123  -- Teacher ID
  AND type = 'usage'
  AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY);
```

### 5. Lấy top 10 students theo điểm writing

```sql
SELECT
    u.id,
    u.full_name,
    AVG(ws.band_score) as avg_band,
    COUNT(ws.id) as submission_count
FROM users u
JOIN writing_submissions ws ON u.id = ws.user_id
WHERE u.teacher_id = 123
  AND ws.graded_at IS NOT NULL
GROUP BY u.id
ORDER BY avg_band DESC
LIMIT 10;
```

### 6. Lấy transaction history với user info

```sql
SELECT
    t.id,
    t.type,
    t.amount,
    t.balance_after,
    t.note,
    t.created_at,
    CASE t.reference_type
        WHEN 'writing' THEN (SELECT question_text FROM writing_tasks wt JOIN writing_submissions ws ON ws.task_id = wt.id WHERE ws.id = t.reference_id LIMIT 1)
        WHEN 'payment' THEN (SELECT CONCAT('Payment #', id) FROM payment_requests WHERE id = t.reference_id)
        ELSE t.reference_type
    END as reference_detail
FROM transactions t
WHERE t.user_id = 123
ORDER BY t.created_at DESC
LIMIT 50;
```

### 7. Tính Gemini API costs trong tháng

```sql
SELECT
    DATE(created_at) as date,
    COUNT(*) as api_calls,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    SUM(estimated_cost_usd) as daily_cost
FROM gemini_usage
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### 8. Lấy leaderboard học sinh trong class

```sql
SELECT
    u.id,
    u.full_name,
    COUNT(DISTINCT ws.id) as writing_count,
    AVG(ws.band_score) as avg_writing,
    COUNT(DISTINCT ra.id) as reading_count,
    AVG(ra.band_score) as avg_reading,
    (AVG(ws.band_score) + AVG(ra.band_score)) / 2 as overall_avg
FROM users u
JOIN class_students cs ON u.id = cs.student_id
LEFT JOIN writing_submissions ws ON u.id = ws.user_id AND ws.graded_at IS NOT NULL
LEFT JOIN reading_attempts ra ON u.id = ra.user_id
WHERE cs.class_id = 789  -- Class ID
  AND cs.status = 'active'
GROUP BY u.id
ORDER BY overall_avg DESC;
```

---

## Migration Scripts

### Initial Setup

```sql
-- Create database
CREATE DATABASE ielts_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ielts_platform;

-- Grant permissions
GRANT ALL PRIVILEGES ON ielts_platform.* TO 'ielts_user'@'localhost';
FLUSH PRIVILEGES;
```

### Sample Data Script

```sql
-- Insert admin
INSERT INTO users (email, password_hash, full_name, role, credits, is_active)
VALUES ('admin@test.com', '$2b$12$...', 'Admin User', 'admin', 10000, TRUE);

-- Insert teacher
INSERT INTO users (email, password_hash, full_name, role, center_name, phone, credits, is_active, approved_at)
VALUES ('teacher@test.com', '$2b$12$...', 'Test Teacher', 'teacher', 'ABC IELTS Center', '0123456789', 50, TRUE, NOW());

-- Insert student
INSERT INTO users (email, password_hash, full_name, role, teacher_id, credits, is_active)
VALUES ('student@test.com', '$2b$12$...', 'Test Student', 'student', 2, 0, TRUE);

-- Insert class
INSERT INTO teacher_classes (teacher_id, name, code, status)
VALUES (2, 'IELTS Foundation - June 2024', 'ABC123', 'active');

-- Enroll student
INSERT INTO class_students (class_id, student_id, status)
VALUES (1, 3, 'active');
```

---

## Database Maintenance

### Backup

```bash
# Full backup
mysqldump -u root -p ielts_platform > backup_$(date +%Y%m%d).sql

# Backup with compression
mysqldump -u root -p ielts_platform | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore

```bash
# Restore from backup
mysql -u root -p ielts_platform < backup_20240115.sql

# Restore from compressed backup
gunzip < backup_20240115.sql.gz | mysql -u root -p ielts_platform
```

### Optimize Tables

```sql
-- Analyze tables
ANALYZE TABLE users, teacher_classes, assignments, writing_submissions;

-- Optimize tables
OPTIMIZE TABLE users, transactions, gemini_usage;
```

---

## Performance Tips

1. **Index Coverage**: Đảm bảo queries sử dụng indexes
```sql
EXPLAIN SELECT * FROM writing_submissions WHERE user_id = 123 ORDER BY created_at DESC;
```

2. **Query Cache**: Enable query cache cho repeated queries
```sql
SET GLOBAL query_cache_size = 67108864;  -- 64MB
SET GLOBAL query_cache_type = 1;
```

3. **Connection Pooling**: Sử dụng SQLAlchemy pool
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_pre_ping': True
}
```

4. **Partitioning**: Partition lớn tables theo date
```sql
-- Partition transactions by month
ALTER TABLE transactions
PARTITION BY RANGE (TO_DAYS(created_at)) (
    PARTITION p202401 VALUES LESS THAN (TO_DAYS('2024-02-01')),
    PARTITION p202402 VALUES LESS THAN (TO_DAYS('2024-03-01')),
    ...
);
```

---

Completed! 🎉
