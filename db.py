# db.py
#import psycopg2
#from psycopg2.extras import execute_values
#from .connection import get_connection  # however you currently connect
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import streamlit as st
import pandas as pd

DATABASE_URL = st.secrets["db"]["url"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    class_code = Column(String(20))
    
    responses = relationship("Response", back_populates="student")

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    subject = Column(String(100))
    subtopic = Column(String(100))
    question_no = Column(String(50))   # ✅ FIXED from Integer → String
    student_answer = Column(String(255))
    correct_answer = Column(String(255))
    is_correct = Column(Boolean)

    student = relationship("Student", back_populates="responses")  # ✅ put it here

class DashboardNotify(Base):
    __tablename__ = "dashboard_notify"
    id = Column(Integer, primary_key=True, index=True)
    batch_code = Column(String(20))
    subject = Column(String(100))
    subtopic = Column(String(100))
    notified = Column(Boolean, default=False)

# --- create tables once at startup ---
Base.metadata.create_all(bind=engine)

def save_bulk_responses(rows):
    """
    rows = list of dicts or tuples with student info and answers
    """
    db = SessionLocal()
    try:
        # ORM-friendly: we must link responses to a Student
        responses = []
        for (student_name, email, class_code, subject, subtopic, qno, s_ans, c_ans) in rows:
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
                is_correct=(s_ans == c_ans)
            ))
        db.bulk_save_objects(responses)
        db.commit()
    finally:
        db.close()

# --- Dashboard query function ---
def get_batch_performance(batch_code: str, subject: str, subtopic: str):
    """
    Returns a DataFrame with each student's performance (correct/incorrect counts).
    """
    db = SessionLocal()
    try:
        # join students + responses
        query = (
            db.query(
                Student.name.label("Student_Name"),
                Student.email.label("Student_Email"),
                Student.class_code.label("Tuition_Code"),
                Response.subject,
                Response.subtopic,
                Response.is_correct
            )
            .join(Response, Student.id == Response.student_id)
            .filter(
                Student.class_code == batch_code,
                Response.subject == subject,
                Response.subtopic == subtopic
            )
        )
        rows = query.all()

        if not rows:
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=[
            "Student_Name", "Student_Email", "Tuition_Code", "Subject", "Subtopic", "is_correct"
        ])

        # Aggregate correct vs incorrect
        perf = (
            df.groupby(["Student_Name", "Student_Email"])
              .agg(Correct=("is_correct", lambda x: x.sum()),
                   Incorrect=("is_correct", lambda x: (~x).sum()))
              .reset_index()
        )
        return perf

    finally:
        db.close()
        
def get_student_responses(student_email: str, subject: str, subtopic: str):
    """
    Returns all responses for a specific student in a given subject & subtopic.
    """
    db = SessionLocal()
    try:
        query = (
            db.query(
                Response.question_no,
                Response.student_answer,
                Response.correct_answer,
                Response.is_correct
            )
            .join(Student, Student.id == Response.student_id)
            .filter(
                Student.email == student_email,
                Response.subject == subject,
                Response.subtopic == subtopic
            )
        )
        rows = query.all()
        return pd.DataFrame(rows, columns=["Question_No", "Student_Answer", "Correct_Answer", "Is_Correct"])
    finally:
        db.close()

def mark_and_check_teacher_notified(batch_code, subject, subtopic):
    """
    Returns True if this is the first submission (notified just now).
    Returns False if teacher was already notified.
    """
    db = SessionLocal()
    try:
        entry = db.query(DashboardNotify).filter_by(
            batch_code=batch_code,
            subject=subject,
            subtopic=subtopic
        ).first()
        
        if entry:
            return False  # already notified
            
        new_entry = DashboardNotify(
            batch_code=batch_code,
            subject=subject,
            subtopic=subtopic,
            notified=True
        )
        db.add(new_entry)
        db.commit()
        return True
    finally:
        db.close()






