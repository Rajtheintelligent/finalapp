-- 0. choose DB (if not already)
CREATE DATABASE IF NOT EXISTS schoolapp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE schoolapp;

-- 1. Head teachers / Schools / Classes
CREATE TABLE head_teachers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,       -- store hash, not plain password
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE classes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  class_name VARCHAR(255) NOT NULL,          -- e.g. "Ten A" or "ClassesName"
  grade VARCHAR(100),
  head_teacher_id INT,
  logo_url TEXT,
  batch VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (head_teacher_id) REFERENCES head_teachers(id) ON DELETE SET NULL
);

-- 2. Students
CREATE TABLE students (
  id INT AUTO_INCREMENT PRIMARY KEY,
  class_id INT,
  student_name VARCHAR(255) NOT NULL,
  student_email VARCHAR(255) NOT NULL,
  student_password_hash VARCHAR(255) NOT NULL, -- store hash
  student_identifier VARCHAR(100) DEFAULT NULL, -- optional student id if you want separate
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_student_email_class (student_email, class_id),
  FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL
);

-- 3. Question bank (fields matched to your JSON)
CREATE TABLE questions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  grade VARCHAR(100),
  subject VARCHAR(255),
  chapter_number VARCHAR(100),
  chapter_name VARCHAR(255),
  subtopic VARCHAR(255),
  question_number VARCHAR(100),   -- e.g. "HE01"
  question_text TEXT,
  option_a TEXT,
  option_b TEXT,
  option_c TEXT,
  option_d TEXT,
  option_e TEXT,
  option_f TEXT,
  answers VARCHAR(100),           -- correct option keys like "A" or "A,C"
  marks INT DEFAULT 1,
  image_url TEXT,
  hint TEXT,
  level VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_subject_subtopic (subject, subtopic),
  INDEX idx_grade_subject (grade, subject)
);

-- 4. Student attempts / submissions (one row per attempt)
CREATE TABLE student_attempts (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  submitted_at TIMESTAMP NULL,
  total_score DECIMAL(6,2) DEFAULT 0,
  max_score DECIMAL(6,2) DEFAULT 0,
  duration_seconds INT NULL,
  attempt_meta JSON NULL,         -- optional metadata (device, IP, etc.)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  INDEX (student_id),
  INDEX (submitted_at)
);

-- 5. Student answers (per question answered)
CREATE TABLE student_answers (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  attempt_id BIGINT NOT NULL,
  question_id INT NOT NULL,
  selected VARCHAR(100),           -- student's selected options e.g. "A" or "A,C"
  is_correct BOOLEAN,
  marks_awarded DECIMAL(6,2) DEFAULT 0,
  answer_meta JSON NULL,           -- optional: time spent per question, etc.
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (attempt_id) REFERENCES student_attempts(id) ON DELETE CASCADE,
  FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE RESTRICT,
  INDEX (attempt_id),
  INDEX (question_id)
);

-- 6. Payments (monthly record per class or per head teacher paying for students)
CREATE TABLE payments (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  head_teacher_id INT NOT NULL,
  class_id INT NOT NULL,
  month_year CHAR(7) NOT NULL,     -- format 'YYYY-MM', e.g. '2025-11'
  amount_paid DECIMAL(8,2) NOT NULL DEFAULT 10.00,
  paid_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  payer VARCHAR(255) NULL,         -- optional
  notes TEXT,
  UNIQUE KEY uk_payment_class_month (class_id, month_year),
  FOREIGN KEY (head_teacher_id) REFERENCES head_teachers(id) ON DELETE CASCADE,
  FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
);

-- 7. Optional: keep an audit log for CSV uploads
CREATE TABLE csv_uploads (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  uploaded_by INT,
  filename VARCHAR(512),
  rows_processed INT,
  errors JSON NULL,
  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
