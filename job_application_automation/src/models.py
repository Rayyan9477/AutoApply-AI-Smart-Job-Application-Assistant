"""
Database models for job application automation system.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, LargeBinary
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
    # Added field for job description - useful for vector search
    job_description = Column(Text)
    # Added field for storing vector embedding
    vector_embedding = Column(LargeBinary, nullable=True)

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
    # Added field for storing vector embedding
    vector_embedding = Column(LargeBinary, nullable=True)

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
    # Added field for storing vector embedding of search query
    vector_embedding = Column(LargeBinary, nullable=True)

# New model for semantic search
class VectorIndex(Base):
    """Model for tracking FAISS vector indices."""
    __tablename__ = "vector_indices"
    
    id = Column(Integer, primary_key=True)
    index_name = Column(String(100), unique=True, nullable=False)
    entity_type = Column(String(50), nullable=False)  # jobs, skills, searches, etc.
    dimension = Column(Integer, nullable=False)
    index_type = Column(String(20), nullable=False)  # Flat, HNSW, IVF, etc.
    item_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    index_path = Column(String(500))
    meta_data = Column(Text)  # JSON string of additional metadata - renamed from 'metadata'