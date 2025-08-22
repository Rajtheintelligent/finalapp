from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import streamlit as st

DATABASE_URL = st.secrets["db"]["url"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    class_code = Column(String)
    responses = relationship("Response", back_populates="student")

class Response(Base):
    __tablename__ = "responses"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    subject = Column(String)
    subtopic = Column(String)
    question_no = Column(String)
    student_answer = Column(String)
    correct_answer = Column(String)
    is_correct = Column(Boolean)
    student = relationship("Student", back_populates="responses")

# --- create tables once at startup ---
Base.metadata.create_all(bind=engine)

def save_response(student_name, email, class_code, subject, subtopic, qno, s_ans, c_ans):
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(email=email).first()
        if not student:
            student = Student(name=student_name, email=email, class_code=class_code)
            db.add(student)
            db.commit()
            db.refresh(student)

        response = Response(
            student_id=student.id,
            subject=subject,
            subtopic=subtopic,
            question_no=qno,
            student_answer=s_ans,
            correct_answer=c_ans,
            is_correct=(s_ans == c_ans)
        )
        db.add(response)
        db.commit()
    finally:
        db.close()
