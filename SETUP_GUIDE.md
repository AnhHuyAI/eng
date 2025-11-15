# 🎓 IELTS AI Platform - B2B Edition

Nền tảng luyện thi IELTS với AI chấm điểm tự động, dành cho **Trung tâm IELTS** và **Giáo viên**.

## 📋 Mục lục

- [Tổng quan](#-tổng-quan)
- [Kiến trúc hệ thống](#-kiến-trúc-hệ-thống)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Hướng dẫn cài đặt](#-hướng-dẫn-cài-đặt)
- [Khởi tạo Database](#-khởi-tạo-database)
- [Chạy ứng dụng](#-chạy-ứng-dụng)
- [Tài khoản Demo](#-tài-khoản-demo)
- [Cấu trúc Project](#-cấu-trúc-project)
- [Tính năng chính](#-tính-năng-chính)
- [API Routes](#-api-routes)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Tổng quan

### Mô hình B2B (Business-to-Business)

Nền tảng hoạt động theo mô hình **3 cấp**:

```
┌─────────────────────────────────────────────────────┐
│                      ADMIN                          │
│  - Quản lý toàn hệ thống                           │
│  - Tạo nội dung công khai (Writing/Reading/...)   │
│  - Duyệt thanh toán                                │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│                    TEACHERS                         │
│  - Mua credits (gói $50, $100, $200)              │
│  - Tạo lớp học (class) với mã code                │
│  - Thêm học sinh bằng email hoặc class code       │
│  - Upload nội dung riêng (100% tự do)             │
│  - Xem submissions & chấm bài                      │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│                    STUDENTS                         │
│  - Join class bằng 6-ký tự code                   │
│  - Làm assignments từ giáo viên                    │
│  - MIỄN PHÍ - dùng credits của giáo viên          │
│  - Nhận điểm AI + feedback tự động                │
└─────────────────────────────────────────────────────┘
```

### Mô hình thanh toán

- **Giáo viên mua credits** (không phải học sinh)
- **Học sinh dùng credits của giáo viên** khi làm bài
- Thanh toán qua **chuyển khoản ngân hàng** (upload ảnh chứng từ)

### Chi phí sử dụng

| Loại bài tập | Credits | Lý do |
|--------------|---------|-------|
| **Writing Task 1/2** | 1 credit | AI chấm điểm Gemini |
| **Speaking** | 2 credits | Google STT + AI chấm |
| **Reading** | FREE | Auto-grading (không cần AI) |
| **Listening** | FREE | Auto-grading (không cần AI) |

### Gói credits cho giáo viên

| Gói | Giá | Credits | Bonus | Mô tả |
|-----|-----|---------|-------|-------|
| **Starter** | $50 | 500 | - | ~250 bài writing hoặc ~20-30 học sinh |
| **Pro** | $100 | 1,100 | +10% | ~550 bài writing hoặc ~50-100 học sinh |
| **Enterprise** | $200 | 2,400 | +20% | ~1,200 bài writing hoặc ~100+ học sinh |

---

## 🏗 Kiến trúc hệ thống

### Tech Stack

- **Backend:** Flask 3.0+ (Python)
- **Database:** MySQL 8.0+ với PyMySQL
- **ORM:** SQLAlchemy + Flask-Migrate
- **AI Services:**
  - Google Gemini 2.0 Flash (chấm Writing/Speaking)
  - Google Cloud Speech-to-Text (chuyển đổi audio)
- **Frontend:** Jinja2 Templates + Bootstrap 5
- **Authentication:** Flask-Login
- **File Upload:** Local storage với validation

### Database Schema

#### Core Tables

1. **users** - Quản lý 3 roles (admin/teacher/student)
   - Teachers: có `credits`, `center_name`, `approved_at`
   - Students: có `teacher_id` (FK đến teacher)

2. **teacher_classes** - Lớp học
   - Unique 6-character `code` (VD: ABC123)
   - `max_students` limit (nullable)

3. **class_students** - Quan hệ Student ↔ Class
   - Status: 'active', 'removed'
   - Unique constraint: (class_id, student_id)

4. **assignments** - Bài tập giao cho lớp
   - Polymorphic content: writing/reading/listening/speaking
   - `due_date`, `max_attempts`

5. **transactions** - Lịch sử credits
   - Type: 'topup', 'usage', 'refund', 'bonus'
   - Reference đến payment hoặc submission

6. **gemini_usage** - Tracking API costs
   - Token counts (input/output)
   - Estimated cost in USD

#### Content Tables

- **writing_tasks** - Đề Writing (Task 1/2)
- **reading_passages** - Bài đọc + câu hỏi
- **listening_sections** - Audio + câu hỏi
- **speaking_topics** - Chủ đề Speaking
- **vocabulary_topics** - Từ vựng theo chủ đề

Tất cả có field `is_public` (Admin content) và `created_by` (Teacher content).

---

## 💻 Yêu cầu hệ thống

### Software Requirements

```bash
Python 3.9+
MySQL 8.0+
pip (Python package manager)
```

### Python Packages (requirements.txt)

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-Migrate==4.0.5
PyMySQL==1.1.0
cryptography==41.0.7
Werkzeug==3.0.1
google-generativeai==0.3.1
google-cloud-speech==2.21.0
```

### API Keys cần thiết

```env
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_SPEECH_API_KEY=your_google_speech_key_here  # Optional
```

---

## 🚀 Hướng dẫn cài đặt

### Bước 1: Clone repository

```bash
git clone https://github.com/your-repo/ielts-platform.git
cd ielts-platform
```

### Bước 2: Tạo Virtual Environment

```bash
# Tạo venv
python -m venv venv

# Kích hoạt (Windows)
venv\Scripts\activate

# Kích hoạt (Linux/Mac)
source venv/bin/activate
```

### Bước 3: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Bước 4: Cấu hình MySQL

#### Tạo database

```sql
-- Đăng nhập MySQL
mysql -u root -p

-- Tạo database
CREATE DATABASE ielts_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Tạo user (optional)
CREATE USER 'ielts_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON ielts_platform.* TO 'ielts_user'@'localhost';
FLUSH PRIVILEGES;

EXIT;
```

#### Cập nhật connection string

Sửa file `app/config.py`:

```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:your_password@localhost/ielts_platform?charset=utf8mb4'
```

### Bước 5: Cấu hình API Keys

Tạo file `.env` (hoặc export trực tiếp):

```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
export SECRET_KEY="your-secret-key-here"
```

Hoặc sửa trực tiếp trong `app/config.py`:

```python
GEMINI_API_KEY = 'your_gemini_api_key_here'
SECRET_KEY = 'your-secret-key-here'
```

---

## 🗄 Khởi tạo Database

### Cách 1: Sử dụng Flask-Migrate (Production)

```bash
# Initialize migrations (lần đầu tiên)
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

### Cách 2: Tạo sample data với run.py (Recommended cho Demo)

File `run.py` có built-in command tạo database mẫu:

```bash
# Tạo database + sample data
flask init-db
```

Lệnh này sẽ tạo:

#### 1. Admin Account
```
Email: admin@test.com
Role: admin
Credits: 10000
```

#### 2. Teacher Account
```
Email: teacher@test.com
Full Name: Test Teacher
Center: ABC IELTS Center
Role: teacher
Credits: 50 (trial credits)
Status: Approved
```

#### 3. Student Account
```
Email: student@test.com
Full Name: Test Student
Role: student
Credits: 0
Teacher: Test Teacher (linked)
```

#### 4. Sample Class
```
Name: IELTS Foundation - June 2024
Code: [Random 6-char code - sẽ hiển thị khi chạy]
Teacher: Test Teacher
Student: Test Student (auto-enrolled)
```

#### 5. Sample Content

**Writing Task (Public - by Admin):**
- Task 2: "Some people think that..."
- Difficulty: intermediate
- Topic: education

**Reading Passage (Public - by Admin):**
- Title: "The History of Coffee"
- 5 questions
- Difficulty: intermediate

---

## ▶️ Chạy ứng dụng

### Development Mode

```bash
# Cách 1: Dùng flask run
export FLASK_APP=run.py
export FLASK_ENV=development
flask run

# Cách 2: Chạy trực tiếp Python
python run.py
```

App sẽ chạy tại: **http://127.0.0.1:5000**

### Production Mode

```bash
# Sử dụng Gunicorn
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:8000 "run:app"
```

---

## 👥 Tài khoản Demo

Sau khi chạy `flask init-db`, bạn có thể login với:

### Login Page: `/auth/login`

**Lưu ý:** Ở demo mode, chỉ cần chọn email, không cần password.

| Role | Email | Chức năng |
|------|-------|-----------|
| **Admin** | admin@test.com | Quản lý toàn hệ thống, tạo content công khai |
| **Teacher** | teacher@test.com | Quản lý lớp, tạo assignments, xem submissions |
| **Student** | student@test.com | Làm bài tập, xem điểm, join class |

### Hoặc đăng ký tài khoản mới:

- **Teacher Registration:** `/auth/teacher/register` (Nhận 50 credits miễn phí)
- **Student Registration:** `/auth/student/register` (Có thể join class ngay khi đăng ký)

---

## 📁 Cấu trúc Project

```
ielts-platform/
├── app/
│   ├── __init__.py              # App factory, blueprints registration
│   ├── config.py                # Configuration (DB, API keys, pricing)
│   │
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   ├── user.py              # User, Transaction
│   │   ├── class_management.py  # TeacherClass, ClassStudent
│   │   ├── assignment.py        # Assignment
│   │   ├── gemini_usage.py      # API tracking
│   │   ├── writing.py           # WritingTask, WritingSubmission
│   │   ├── reading.py           # ReadingPassage, ReadingAttempt
│   │   ├── listening.py         # ListeningSection, ListeningAttempt
│   │   ├── speaking.py          # SpeakingTopic, SpeakingSubmission
│   │   ├── vocabulary.py        # VocabularyTopic, VocabularyWord
│   │   └── payment.py           # PaymentRequest
│   │
│   ├── routes/                  # Blueprints (Controllers)
│   │   ├── auth.py              # Login, Logout, Teacher/Student Registration
│   │   ├── user.py              # User dashboard, progress
│   │   ├── admin.py             # Admin panel
│   │   ├── teacher.py           # Teacher dashboard, classes, assignments, credits
│   │   ├── student.py           # Student dashboard, classes, assignments, join
│   │   ├── writing.py           # Writing practice & submission
│   │   ├── reading.py           # Reading practice
│   │   ├── listening.py         # Listening practice
│   │   ├── speaking.py          # Speaking practice
│   │   ├── vocabulary.py        # Vocabulary practice
│   │   └── payment.py           # Payment processing
│   │
│   ├── services/                # Business logic
│   │   ├── gemini_service.py    # Gemini AI integration
│   │   ├── stt_service.py       # Speech-to-Text
│   │   ├── scoring_service.py   # Orchestrates AI scoring
│   │   └── email_service.py     # Email sending
│   │
│   ├── templates/               # Jinja2 HTML templates
│   │   ├── base.html            # Base layout
│   │   ├── auth/                # Login, Registration pages
│   │   ├── teacher/             # Teacher portal (8 templates)
│   │   │   ├── base_teacher.html
│   │   │   ├── dashboard.html
│   │   │   ├── classes.html
│   │   │   ├── create_class.html
│   │   │   ├── view_class.html
│   │   │   ├── content.html
│   │   │   ├── create_assignment.html
│   │   │   ├── submissions.html
│   │   │   └── credits.html
│   │   ├── student/             # Student portal (4 templates)
│   │   │   ├── base_student.html
│   │   │   ├── dashboard.html
│   │   │   ├── classes.html
│   │   │   ├── assignments.html
│   │   │   └── join_class.html
│   │   ├── user/                # User dashboard
│   │   ├── writing/             # Writing practice UI
│   │   ├── reading/             # Reading practice UI
│   │   ├── listening/           # Listening practice UI
│   │   └── speaking/            # Speaking practice UI
│   │
│   └── static/                  # CSS, JS, Images
│       └── uploads/             # User uploaded files
│
├── migrations/                  # Flask-Migrate files
├── config.py                    # Root config (imports from app/config.py)
├── run.py                       # Entry point + CLI commands
├── requirements.txt             # Python dependencies
├── README.md                    # This file
└── .env                         # Environment variables (gitignored)
```

---

## ✨ Tính năng chính

### 🎓 Teacher Features

1. **Dashboard**
   - Tổng số học sinh
   - Tổng số lớp
   - Credits balance
   - Recent submissions

2. **Class Management**
   - Tạo lớp với unique code (VD: ABC123)
   - Thêm học sinh bằng email
   - Xem danh sách học sinh
   - Archive lớp

3. **Assignment Management**
   - Tạo assignment từ content library
   - Set due date & max attempts
   - Assign cho specific class
   - Track completion status

4. **Content Library**
   - Browse admin's public content
   - Upload own private content (100%)
   - Filter by type, difficulty, topic

5. **Submissions Review**
   - Xem tất cả submissions từ học sinh
   - AI score + feedback
   - Add teacher comment & override score
   - Filter by student, class, type

6. **Credits Management**
   - View balance & transaction history
   - Purchase packages ($50/$100/$200)
   - Upload payment proof
   - Track usage per student

### 👨‍🎓 Student Features

1. **Dashboard**
   - My classes
   - Active assignments
   - Completed assignments
   - Average score

2. **Join Class**
   - Enter 6-character code
   - Instant enrollment
   - View current classes

3. **Assignments**
   - Filter: Active / Completed / All
   - Due date countdown
   - Attempts tracking
   - Practice directly

4. **Practice**
   - Writing (Task 1 & 2)
   - Reading (Multiple choice, True/False)
   - Listening (Fill blanks, MCQ)
   - Speaking (Record & submit)

5. **Results**
   - AI band score (0-9)
   - Detailed feedback
   - Teacher comments
   - Progress tracking

### 👑 Admin Features

1. **User Management**
   - Approve teachers
   - View all users
   - Manage credits

2. **Content Management**
   - Create public writing tasks
   - Create public reading passages
   - Create public listening sections
   - Create public speaking topics

3. **Payment Management**
   - Approve payment requests
   - Add credits to teachers
   - View transaction history

4. **System Monitoring**
   - Gemini API usage
   - Credits consumption
   - User statistics

---

## 🛣 API Routes

### Authentication

```
GET  /auth/login                    # Login page (select user)
POST /auth/login                    # Process login
GET  /auth/logout                   # Logout
GET  /auth/teacher/register         # Teacher registration form
POST /auth/teacher/register         # Create teacher account
GET  /auth/student/register         # Student registration form
POST /auth/student/register         # Create student account
```

### Teacher Portal

```
GET  /teacher/dashboard             # Teacher dashboard
GET  /teacher/classes               # List all classes
GET  /teacher/classes/create        # Create class form
POST /teacher/classes/create        # Process class creation
GET  /teacher/classes/<id>          # View class details
POST /teacher/classes/<id>/add_student  # Add student to class
GET  /teacher/content               # Browse content library
GET  /teacher/assignments/create    # Create assignment form
POST /teacher/assignments/create    # Process assignment creation
GET  /teacher/submissions           # View all submissions
POST /teacher/submissions/<id>/comment  # Add teacher comment
GET  /teacher/credits               # Credits management
```

### Student Portal

```
GET  /student/classes               # List enrolled classes
GET  /student/classes/<id>          # View class details
GET  /student/assignments           # List all assignments
GET  /student/join                  # Join class form
POST /student/join                  # Process class join
```

### Practice Routes

```
# Writing
GET  /writing                       # Writing tasks list
GET  /writing/practice/<task_id>    # Practice specific task
POST /writing/submit                # Submit writing

# Reading
GET  /reading                       # Reading passages list
GET  /reading/practice/<id>         # Practice reading
POST /reading/<id>/submit           # Submit answers
GET  /reading/result/<attempt_id>   # View result

# Listening (similar to reading)
GET  /listening
GET  /listening/practice/<id>
POST /listening/<id>/submit
GET  /listening/result/<attempt_id>

# Speaking
GET  /speaking
GET  /speaking/practice/<id>
POST /speaking/submit               # Submit audio recording
GET  /speaking/result/<id>
```

### Admin Panel

```
GET  /admin/dashboard               # Admin dashboard
GET  /admin/users                   # User management
GET  /admin/payments                # Payment requests
POST /admin/payments/<id>/approve   # Approve payment
GET  /admin/content                 # Content management
```

---

## 🐛 Troubleshooting

### Lỗi: ModuleNotFoundError: No module named 'flask'

```bash
# Đảm bảo đã activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install lại requirements
pip install -r requirements.txt
```

### Lỗi: Can't connect to MySQL server

```bash
# Kiểm tra MySQL đang chạy
sudo systemctl start mysql    # Linux
brew services start mysql     # Mac
# Windows: Mở Services.msc → Start MySQL

# Kiểm tra connection string trong app/config.py
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost/ielts_platform?charset=utf8mb4'
```

### Lỗi: RuntimeError: Working outside of application context

Đảm bảo các services sử dụng factory pattern:

```python
# ❌ WRONG
from app.services.gemini_service import gemini_service

# ✅ CORRECT
from app.services.gemini_service import get_gemini_service
gemini_service = get_gemini_service()
```

### Lỗi: Table doesn't exist

```bash
# Drop và tạo lại database
mysql -u root -p -e "DROP DATABASE ielts_platform; CREATE DATABASE ielts_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Chạy lại migrations
flask db upgrade

# Hoặc tạo sample data
flask init-db
```

### Lỗi: Gemini API quota exceeded

```python
# Kiểm tra usage trong database
SELECT SUM(input_tokens), SUM(output_tokens), SUM(estimated_cost_usd)
FROM gemini_usage
WHERE DATE(created_at) = CURDATE();

# Switch sang model rẻ hơn trong app/config.py
GEMINI_MODEL = 'gemini-1.5-flash'  # Thay vì gemini-2.0-flash-exp
```

---

## 📊 Database Sample Data

Sau khi chạy `flask init-db`, bạn sẽ có:

### Users (3)
- 1 Admin: admin@test.com (10,000 credits)
- 1 Teacher: teacher@test.com (50 credits)
- 1 Student: student@test.com (0 credits)

### Classes (1)
- "IELTS Foundation - June 2024" (Code: [Random])
- Teacher: Test Teacher
- Student: Test Student (enrolled)

### Content (2)
- 1 Writing Task (Task 2, public)
- 1 Reading Passage (5 questions, public)

### Transactions (2)
- Admin: +10,000 credits (bonus)
- Teacher: +50 credits (trial)

---

## 📝 Next Steps

Sau khi setup xong, bạn có thể:

1. **Login as Teacher** → Tạo lớp mới → Thêm học sinh
2. **Login as Admin** → Tạo content công khai → Duyệt payment
3. **Login as Student** → Join class → Làm assignment → Xem điểm

Hoặc tự đăng ký tài khoản mới:
- `/auth/teacher/register` (nhận 50 credits miễn phí)
- `/auth/student/register` (join class ngay khi đăng ký)

---

## 📞 Support

Nếu gặp vấn đề, kiểm tra:
1. MySQL service đang chạy
2. Virtual environment đã activate
3. API keys đã cấu hình đúng
4. Database đã được tạo và migrate

Good luck! 🚀
