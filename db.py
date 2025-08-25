from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import streamlit as st
import pandas as pd
from sqlalchemy import func

# =============================================================
# Database setup
# =============================================================
DATABASE_URL = st.secrets["db"]["url"]
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# =============================================================
# ORM Models
# =============================================================
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    class_code = Column(String(20))

    responses = relationship("Response", back_populates="student", cascade="all, delete-orphan")


class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"))
    subject = Column(String(100), index=True)
    subtopic = Column(String(100), index=True)
    question_no = Column(String(50))   # keep as string to allow "Q1", "1a", etc
    student_answer = Column(String(255))
    correct_answer = Column(String(255))
    is_correct = Column(Boolean)

    # NEW — optional quiz identifier to group responses as one "main quiz"
    quiz_id = Column(String(100), index=True, nullable=True)

    student = relationship("Student", back_populates="responses")


class DashboardNotify(Base):
    __tablename__ = "dashboard_notify"
    id = Column(Integer, primary_key=True, index=True)
    batch_code = Column(String(20), index=True)
    subject = Column(String(100), index=True)
    subtopic = Column(String(100), index=True)
    notified = Column(Boolean, default=False)


# NOTE: create_all() will create missing tables, but it WILL NOT add new columns
# to existing tables. If you are adding quiz_id to an existing database, run a
# migration (Alembic) or execute an ALTER TABLE manually (examples below).
Base.metadata.create_all(bind=engine)

# PostgreSQL example:
#   ALTER TABLE responses ADD COLUMN IF NOT EXISTS quiz_id VARCHAR(100);
#   CREATE INDEX IF NOT EXISTS ix_responses_quiz_id ON responses (quiz_id);
# MySQL example:
#   ALTER TABLE responses ADD COLUMN quiz_id VARCHAR(100);
#   CREATE INDEX ix_responses_quiz_id ON responses (quiz_id);
# SQLite (dev-only): use a migration tool (Alembic) or recreate table.


# =============================================================
# Persistence helpers
# =============================================================

def save_bulk_responses(rows):
    """
    Save multiple responses.

    Backward-compatible input formats:
      - 8-tuple: (student_name, email, class_code, subject, subtopic, qno, s_ans, c_ans)
      - 9-tuple: (student_name, email, class_code, subject, subtopic, qno, s_ans, c_ans, quiz_id)
    """
    db = SessionLocal()
    try:
        responses = []
        for row in rows:
            if len(row) == 8:
                student_name, email, class_code, subject, subtopic, qno, s_ans, c_ans = row
                quiz_id = None
            elif len(row) == 9:
                student_name, email, class_code, subject, subtopic, qno, s_ans, c_ans, quiz_id = row
            else:
                raise ValueError("Each row must be an 8- or 9-tuple. Got length=" + str(len(row)))

            # normalize strings a bit
            subject = (subject or "").strip()
            subtopic = (subtopic or "").strip()
            class_code = (class_code or "").strip()
            quiz_id = (quiz_id or "").strip() or None

            student = db.query(Student).filter_by(email=email).first()
            if not student:
                student = Student(name=student_name, email=email, class_code=class_code)
                db.add(student)
                db.commit()
                db.refresh(student)

            responses.append(Response(
                student_id=student.id,
                subject=subject,
                subtopic=subtopic,
                question_no=qno,
                student_answer=s_ans,
                correct_answer=c_ans,
                is_correct=(s_ans == c_ans),
                quiz_id=quiz_id,
            ))
        if responses:
            db.bulk_save_objects(responses)
            db.commit()
    finally:
        db.close()


# =============================================================
# Query helpers for dashboard (Subtopic-based)
# =============================================================

def get_batch_performance(batch_code: str, subject: str, subtopic: str = None) -> pd.DataFrame:
    """
    Return a DataFrame of per-student performance (Correct/Incorrect counts)
    for a given batch + subject, and optionally a specific subtopic.

    Columns:
      Student_Name, Student_Email, Tuition_Code, Subject, Subtopic, Correct, Incorrect
    """
    db = SessionLocal()
    try:
        q = (
            db.query(
                Student.name.label("Student_Name"),
                Student.email.label("Student_Email"),
                Student.class_code.label("Tuition_Code"),
                Response.subject.label("Subject"),
                Response.subtopic.label("Subtopic"),
                Response.is_correct.label("is_correct"),
            )
            .join(Response, Student.id == Response.student_id)
            .filter(
                Student.class_code == batch_code.strip(),
                func.lower(Response.subject) == func.lower(subject.strip())
            )
        )
        if subtopic:
            q = q.filter(func.lower(Response.subtopic) == func.lower(subtopic.strip()))

        rows = q.all()
        if not rows:
            return pd.DataFrame(columns=[
                "Student_Name","Student_Email","Tuition_Code","Subject","Subtopic","Correct","Incorrect"
            ])

        df = pd.DataFrame(rows, columns=[
            "Student_Name","Student_Email","Tuition_Code","Subject","Subtopic","is_correct"
        ])

        perf = (
            df.groupby(["Student_Name","Student_Email","Tuition_Code","Subject","Subtopic"], as_index=False)
              .agg(Correct=("is_correct", lambda x: int(x.sum())),
                   Incorrect=("is_correct", lambda x: int((~x).sum())))
        )
        return perf
    finally:
        db.close()


def get_student_summary(batch_code: str, subject: str, student_email: str) -> pd.DataFrame:
    """
    Return per-subtopic summary for a student in a subject within a batch.

    Columns: Subtopic, Correct, Incorrect, Total
    """
    perf = get_batch_performance(batch_code, subject, subtopic=None)
    if perf.empty:
        return pd.DataFrame(columns=["Subtopic","Correct","Incorrect","Total"])

    sdf = perf[perf["Student_Email"] == student_email]
    if sdf.empty:
        return pd.DataFrame(columns=["Subtopic","Correct","Incorrect","Total"])

    summary = (
        sdf.groupby("Subtopic", as_index=False)
           .agg(Correct=("Correct","sum"), Incorrect=("Incorrect","sum"))
    )
    summary["Total"] = summary["Correct"] + summary["Incorrect"]
    return summary


def get_student_responses(student_email: str, subject: str, subtopic: str) -> pd.DataFrame:
    """
    Return all question-level responses for a specific student in a subject & subtopic.

    Columns: Question_No, Student_Answer, Correct_Answer, Is_Correct
    """
    db = SessionLocal()
    try:
        q = (
            db.query(
                Response.question_no,
                Response.student_answer,
                Response.correct_answer,
                Response.is_correct,
            )
            .join(Student, Student.id == Response.student_id)
            .filter(
                Student.email == student_email,
                Response.subject.ilike(subject),
                Response.subtopic == subtopic,
            )
        )
        rows = q.all()
        return pd.DataFrame(rows, columns=["Question_No","Student_Answer","Correct_Answer","Is_Correct"])
    finally:
        db.close()


# =============================================================
# Quiz-based helpers (for per-main-quiz charts)
# =============================================================

def get_student_quiz_summary(batch_code: str, subject: str, student_email: str) -> pd.DataFrame:
    """
    Per-quiz summary for a student.
    Columns: Quiz_ID, Correct, Incorrect, Total
    """
    db = SessionLocal()
    try:
        q = (
            db.query(Response.quiz_id, Response.is_correct)
              .join(Student, Student.id == Response.student_id)
              .filter(
                  Student.class_code == batch_code,
                  Student.email == student_email,
                  Response.subject.ilike(subject),
                  Response.quiz_id.isnot(None),
              )
        )
        rows = q.all()
        df = pd.DataFrame(rows, columns=["Quiz_ID", "is_correct"]) if rows else pd.DataFrame(columns=["Quiz_ID","is_correct"])
        if df.empty:
            return pd.DataFrame(columns=["Quiz_ID","Correct","Incorrect","Total"])
        out = (
            df.groupby("Quiz_ID", as_index=False)
              .agg(Correct=("is_correct", lambda x: int(x.sum())),
                   Incorrect=("is_correct", lambda x: int((~x).sum())))
        )
        out["Total"] = out["Correct"] + out["Incorrect"]
        return out
    finally:
        db.close()


def get_class_quiz_summary(batch_code: str, subject: str) -> pd.DataFrame:
    """
    Class-wide per-quiz totals.
    Columns: Quiz_ID, Class_Correct, Class_Incorrect, Class_Total, Class_AccuracyPct
    """
    db = SessionLocal()
    try:
        q = (
            db.query(Response.quiz_id, Response.is_correct)
              .join(Student, Student.id == Response.student_id)
              .filter(
                  Student.class_code == batch_code,
                  Response.subject.ilike(subject),
                  Response.quiz_id.isnot(None),
              )
        )
        rows = q.all()
        df = pd.DataFrame(rows, columns=["Quiz_ID", "is_correct"]) if rows else pd.DataFrame(columns=["Quiz_ID","is_correct"])
        if df.empty:
            return pd.DataFrame(columns=["Quiz_ID","Class_Correct","Class_Incorrect","Class_Total","Class_AccuracyPct"])
        out = (
            df.groupby("Quiz_ID", as_index=False)
              .agg(Class_Correct=("is_correct", lambda x: int(x.sum())),
                   Class_Incorrect=("is_correct", lambda x: int((~x).sum())))
        )
        out["Class_Total"] = out["Class_Correct"] + out["Class_Incorrect"]
        out["Class_AccuracyPct"] = out.apply(
            lambda r: (r.Class_Correct / r.Class_Total * 100) if r.Class_Total > 0 else float("nan"), axis=1
        )
        return out
    finally:
        db.close()


def get_student_quiz_responses(student_email: str, subject: str, quiz_id: str) -> pd.DataFrame:
    """
    Per-question detail for a specific student's quiz attempt.
    Columns: Question_No, Student_Answer, Correct_Answer, Is_Correct
    """
    db = SessionLocal()
    try:
        q = (
            db.query(
                Response.question_no,
                Response.student_answer,
                Response.correct_answer,
                Response.is_correct,
            )
            .join(Student, Student.id == Response.student_id)
            .filter(
                Student.email == student_email,
                Response.subject.ilike(subject),
                Response.quiz_id == quiz_id,
            )
        )
        rows = q.all()
        return pd.DataFrame(rows, columns=["Question_No","Student_Answer","Correct_Answer","Is_Correct"])
    finally:
        db.close()


# =============================================================
# Teacher notification flag
# =============================================================

def mark_and_check_teacher_notified(batch_code: str, subject: str, subtopic: str) -> bool:
    """
    Returns True if this is the first submission (we just marked as notified).
    Returns False if teacher was already notified before.
    """
    db = SessionLocal()
    try:
        entry = (
            db.query(DashboardNotify)
              .filter_by(batch_code=batch_code, subject=subject, subtopic=subtopic)
              .first()
        )
        if entry:
            return False
        db.add(DashboardNotify(batch_code=batch_code, subject=subject, subtopic=subtopic, notified=True))
        db.commit()
        return True
    finally:
        db.close()
