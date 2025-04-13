"""
Database models for job application automation system.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class JobApplication(Base):
    """Model for tracking job applications."""
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True)
    job_id = Column(String(100), unique=True, nullable=False)
    job_title = Column(String(200), nullable=False)
    company = Column(String(200), nullable=False)
    application_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="submitted")
    source = Column(String(50))  # linkedin, indeed, glassdoor, etc.
    match_score = Column(Float)
    resume_path = Column(String(500))
    cover_letter_path = Column(String(500))
    response_received = Column(Boolean, default=False)
    response_date = Column(DateTime)
    notes = Column(Text)
    url = Column(String(500))

    # Relationships
    interactions = relationship("ApplicationInteraction", back_populates="application")
    skills = relationship("JobSkill", back_populates="application")

class ApplicationInteraction(Base):
    """Model for tracking interactions with applications."""
    __tablename__ = "application_interactions"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("job_applications.id"))
    interaction_type = Column(String(50))  # email, phone, interview, etc.
    interaction_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    next_steps = Column(Text)
    outcome = Column(String(50))

    # Relationship
    application = relationship("JobApplication", back_populates="interactions")

class JobSkill(Base):
    """Model for tracking skills required/matched for jobs."""
    __tablename__ = "job_skills"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("job_applications.id"))
    skill_name = Column(String(100))
    skill_category = Column(String(50))  # technical, soft, certification, etc.
    required = Column(Boolean, default=True)
    candidate_has = Column(Boolean)
    match_score = Column(Float)

    # Relationship
    application = relationship("JobApplication", back_populates="skills")

class SearchHistory(Base):
    """Model for tracking job search history."""
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True)
    search_date = Column(DateTime, default=datetime.utcnow)
    keywords = Column(String(500))
    location = Column(String(200))
    source = Column(String(50))
    results_count = Column(Integer)
    filtered_count = Column(Integer)
    search_params = Column(Text)  # JSON string of additional parameters