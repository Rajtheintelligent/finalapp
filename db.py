# db.py
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Text, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import streamlit as st

# ✅ Use secrets.toml to hide DB credentials
DATABASE_URL = st.secrets["db"]["url"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    class_code = Column(String)
    registered_at = Column(TIMESTAMP, server_default=func.now())
    responses = relationship("Response", back_populates="student")

class Response(Base):
    __tablename__ = "responses"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    subject = Column(Text, nullable=False)
    subtopic = Column(Text, nullable=False)
    question_no = Column(Integer)
    student_answer = Column(Text)
    correct_answer = Column(Text)
    is_correct = Column(Boolean)
    attempted_at = Column(TIMESTAMP, server_default=func.now())
    student = relationship("Student", back_populates="responses")

# ✅ Run once to create tables
Base.metadata.create_all(bind=engine)
