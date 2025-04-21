"""
Application tracking system with error handling and retries.
"""

import os
import json
import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, case

# Fix relative imports by using absolute imports
from src.database import get_db, execute_with_retry
from src.models import JobApplication, ApplicationInteraction, JobSkill, SearchHistory, VectorIndex
from src.vector_database import vector_db, time_vector_operation
from config.logging_config import AuditLogger
from src.database_errors import handle_db_errors, with_retry, safe_commit, DatabaseError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../data/logs/application_tracker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Default index names
JOB_INDEX = "job_applications"
SKILLS_INDEX = "job_skills"

class ApplicationTracker:
    """Tracks and analyzes job applications using database storage with error handling."""
    
    def __init__(self):
        self.audit_logger = AuditLogger()
        
    @handle_db_errors
    @with_retry()
    def add_application(self, 
                       job_id: str,
                       job_title: str,
                       company: str,
                       source: str,
                       match_score: float,
                       resume_path: str,
                       cover_letter_path: Optional[str] = None,
                       notes: Optional[str] = None,
                       url: Optional[str] = None,
                       job_description: Optional[str] = None,
                       skills: Optional[List[Dict[str, Any]]] = None) -> JobApplication:
        """Add a new job application record with error handling and retries."""
        try:
            with get_db() as db:
                # Check for existing application
                existing = db.query(JobApplication).filter_by(job_id=job_id).first()
                if existing:
                    logger.warning(f"Application with job_id {job_id} already exists")
                    return existing
                    
                # Create application record
                application = JobApplication(
                    job_id=job_id,
                    job_title=job_title,
                    company=company,
                    source=source,
                    match_score=match_score,
                    resume_path=resume_path,
                    cover_letter_path=cover_letter_path,
                    notes=notes,
                    url=url,
                    job_description=job_description  # Store job description for vector search
                )
                db.add(application)
                
                # Add skills if provided
                if skills:
                    for skill_data in skills:
                        skill = JobSkill(
                            application=application,
                            skill_name=skill_data["name"],
                            skill_category=skill_data.get("category", "technical"),
                            required=skill_data.get("required", True),
                            candidate_has=skill_data.get("candidate_has", False),
                            match_score=skill_data.get("match_score", 0.0)
                        )
                        db.add(skill)
                
                # Use safe commit with retries
                safe_commit(db)
                db.refresh(application)
                
                # Add to vector index if job description is available
                if job_description:
                    self._index_application(application)
                
                # Index skills if provided
                if skills:
                    self._index_skills(application.skills)
                
                # Log the event
                self.audit_logger.log_application_event(
                    "application_created",
                    {
                        "job_id": job_id,
                        "company": company,
                        "source": source,
                        "match_score": match_score
                    }
                )
                
                return application
                
        except Exception as e:
            logger.error(f"Error adding application: {e}")
            raise
    
    @handle_db_errors
    @with_retry()
    def _index_application(self, application: JobApplication) -> bool:
        """
        Add a job application to the vector index.
        
        Args:
            application: JobApplication object to index
            
        Returns:
            True if indexing was successful
        """
        try:
            # Check if job index exists, create if not
            with get_db() as db:
                index_exists = db.query(VectorIndex).filter_by(index_name=JOB_INDEX).first() is not None
            
            if not index_exists:
                vector_db.create_index(JOB_INDEX)
                # Record index in database
                with get_db() as db:
                    index_record = VectorIndex(
                        index_name=JOB_INDEX,
                        entity_type="jobs",
                        dimension=384,  # Default dimension for the embedding model
                        index_type="Flat",
                        item_count=0,
                        index_path=str(vector_db.index_dir / f"{JOB_INDEX}.index")
                    )
                    db.add(index_record)
                    safe_commit(db)
            
            # Create text for embedding
            text = f"{application.job_title} {application.company} "
            if application.job_description:
                text += application.job_description
            
            # Add to vector index
            items = [{"id": application.id, "text": text}]
            
            # Add to vector index with monitoring
            result = self._timed_add_to_index(JOB_INDEX, items)
            
            # Store vector embedding in the application record
            if result:
                with get_db() as db:
                    # Generate embedding and store in database
                    embedding = vector_db.embed_text(text)
                    application = db.query(JobApplication).filter_by(id=application.id).first()
                    if application:
                        application.vector_embedding = embedding.tobytes()
                        safe_commit(db)
                    
                    # Update index count
                    index_record = db.query(VectorIndex).filter_by(index_name=JOB_INDEX).first()
                    if index_record:
                        index_record.item_count += 1
                        index_record.updated_at = datetime.utcnow()
                        safe_commit(db)
            
            return result
            
        except Exception as e:
            logger.error(f"Error indexing application: {e}")
            return False
    
    @handle_db_errors
    @with_retry()
    def _index_skills(self, skills: List[JobSkill]) -> bool:
        """
        Add job skills to the vector index.
        
        Args:
            skills: List of JobSkill objects to index
            
        Returns:
            True if indexing was successful
        """
        try:
            if not skills:
                return True
                
            # Check if skills index exists, create if not
            with get_db() as db:
                index_exists = db.query(VectorIndex).filter_by(index_name=SKILLS_INDEX).first() is not None
            
            if not index_exists:
                vector_db.create_index(SKILLS_INDEX)
                # Record index in database
                with get_db() as db:
                    index_record = VectorIndex(
                        index_name=SKILLS_INDEX,
                        entity_type="skills",
                        dimension=384,  # Default dimension for the embedding model
                        index_type="Flat",
                        item_count=0,
                        index_path=str(vector_db.index_dir / f"{SKILLS_INDEX}.index")
                    )
                    db.add(index_record)
                    safe_commit(db)
            
            # Prepare items for indexing
            items = []
            for skill in skills:
                text = f"{skill.skill_name} {skill.skill_category}"
                items.append({
                    "id": skill.id,
                    "text": text
                })
            
            # Add to vector index with monitoring
            result = self._timed_add_to_index(SKILLS_INDEX, items)
            
            # Store vector embeddings in the skill records
            if result:
                with get_db() as db:
                    # Generate embeddings and store in database
                    for skill in skills:
                        text = f"{skill.skill_name} {skill.skill_category}"
                        embedding = vector_db.embed_text(text)
                        
                        skill_record = db.query(JobSkill).filter_by(id=skill.id).first()
                        if skill_record:
                            skill_record.vector_embedding = embedding.tobytes()
                    
                    safe_commit(db)
                    
                    # Update index count
                    index_record = db.query(VectorIndex).filter_by(index_name=SKILLS_INDEX).first()
                    if index_record:
                        index_record.item_count += len(items)
                        index_record.updated_at = datetime.utcnow()
                        safe_commit(db)
            
            return result
            
        except Exception as e:
            logger.error(f"Error indexing skills: {e}")
            return False
    
    @time_vector_operation("add_items")
    def _timed_add_to_index(self, index_name: str, items: List[Dict[str, Any]]) -> bool:
        """Add items to vector index with performance monitoring."""
        return vector_db.add_items(index_name, items, text_field="text", id_field="id")
            
    @handle_db_errors
    @with_retry()
    def update_application_status(self,
                                job_id: str,
                                status: str,
                                response_received: bool = False,
                                notes: Optional[str] = None) -> Optional[JobApplication]:
        """Update application status with error handling and retries."""
        try:
            with get_db() as db:
                application = db.query(JobApplication).filter_by(job_id=job_id).first()
                if application:
                    application.status = status
                    if response_received:
                        application.response_received = True
                        application.response_date = datetime.utcnow()
                    if notes:
                        application.notes = notes if not application.notes else f"{application.notes}\n{notes}"
                    
                    # Add interaction record
                    interaction = ApplicationInteraction(
                        application=application,
                        interaction_type="status_update",
                        notes=f"Status updated to: {status}"
                    )
                    db.add(interaction)
                    
                    # Use safe commit with retries
                    safe_commit(db)
                    db.refresh(application)
                    
                    # Log the event
                    self.audit_logger.log_application_event(
                        "status_updated",
                        {
                            "job_id": job_id,
                            "status": status,
                            "response_received": response_received
                        }
                    )
                    
                    return application
                    
                logger.warning(f"Application with job_id {job_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error updating application status: {e}")
            raise
            
    @handle_db_errors
    @with_retry()
    def add_interaction(self,
                       job_id: str,
                       interaction_type: str,
                       notes: str,
                       next_steps: Optional[str] = None,
                       outcome: Optional[str] = None) -> Optional[ApplicationInteraction]:
        """Add an interaction record with error handling and retries."""
        try:
            with get_db() as db:
                application = db.query(JobApplication).filter_by(job_id=job_id).first()
                if application:
                    interaction = ApplicationInteraction(
                        application=application,
                        interaction_type=interaction_type,
                        notes=notes,
                        next_steps=next_steps,
                        outcome=outcome
                    )
                    db.add(interaction)
                    
                    # Use safe commit with retries
                    safe_commit(db)
                    db.refresh(interaction)
                    
                    # Log the event
                    self.audit_logger.log_application_event(
                        "interaction_added",
                        {
                            "job_id": job_id,
                            "type": interaction_type,
                            "outcome": outcome
                        }
                    )
                    
                    return interaction
                    
                logger.warning(f"Application with job_id {job_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error adding interaction: {e}")
            raise
            
    @handle_db_errors
    @with_retry()
    def get_application_stats(self) -> Dict[str, Any]:
        """Get application statistics with error handling and retries."""
        try:
            with get_db() as db:
                # Get basic counts using execute_with_retry
                total_applications = execute_with_retry(
                    db,
                    db.query(func.count(JobApplication.id))
                ).scalar()
                
                if total_applications == 0:
                    return {"error": "No applications found"}
                    
                stats = {
                    "total_applications": total_applications,
                    "applications_by_source": {},
                    "applications_by_status": {},
                    "response_rate": 0,
                    "average_match_score": 0,
                    "applications_by_date": {},
                }
                
                # Calculate source statistics with retry
                source_counts = execute_with_retry(
                    db,
                    db.query(
                        JobApplication.source,
                        func.count(JobApplication.id)
                    ).group_by(JobApplication.source)
                ).all()
                
                stats["applications_by_source"] = {
                    source: count for source, count in source_counts
                }
                
                # Calculate status statistics with retry
                status_counts = execute_with_retry(
                    db,
                    db.query(
                        JobApplication.status,
                        func.count(JobApplication.id)
                    ).group_by(JobApplication.status)
                ).all()
                
                stats["applications_by_status"] = {
                    status: count for status, count in status_counts
                }
                
                # Calculate response rate with retry
                responses = execute_with_retry(
                    db,
                    db.query(func.count(JobApplication.id))\
                    .filter(JobApplication.response_received == True)
                ).scalar()
                
                stats["response_rate"] = responses / total_applications
                
                # Calculate average match score with retry
                avg_score = execute_with_retry(
                    db,
                    db.query(func.avg(JobApplication.match_score))
                ).scalar()
                
                stats["average_match_score"] = float(avg_score) if avg_score else 0
                
                # Calculate date statistics with retry
                date_counts = execute_with_retry(
                    db,
                    db.query(
                        func.date(JobApplication.application_date),
                        func.count(JobApplication.id)
                    ).group_by(func.date(JobApplication.application_date))
                ).all()
                
                stats["applications_by_date"] = {
                    date.strftime("%Y-%m-%d"): count for date, count in date_counts
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting application stats: {e}")
            return {"error": str(e)}
            
    @handle_db_errors
    @with_retry()
    def get_application_history(self,
                              company: Optional[str] = None,
                              source: Optional[str] = None,
                              status: Optional[str] = None,
                              min_match_score: Optional[float] = None) -> List[JobApplication]:
        """Get application history with filters, error handling, and retries."""
        try:
            with get_db() as db:
                query = db.query(JobApplication)
                
                if company:
                    query = query.filter(JobApplication.company.ilike(f"%{company}%"))
                if source:
                    query = query.filter(JobApplication.source == source)
                if status:
                    query = query.filter(JobApplication.status == status)
                if min_match_score is not None:
                    query = query.filter(JobApplication.match_score >= min_match_score)
                    
                return execute_with_retry(db, query).all()
                
        except Exception as e:
            logger.error(f"Error getting application history: {e}")
            return []
            
    @handle_db_errors
    @with_retry()
    def get_recommendations(self) -> Dict[str, Any]:
        """Generate recommendations with error handling and retries."""
        try:
            stats = self.get_application_stats()
            
            recommendations = {
                "high_success_sources": [],
                "best_match_scores": [],
                "optimal_application_times": [],
                "improvement_areas": []
            }
            
            with get_db() as db:
                # Analyze successful sources with retry
                source_success = execute_with_retry(
                    db,
                    db.query(
                        JobApplication.source,
                        func.count(JobApplication.id).label('total'),
                        func.sum(case((JobApplication.response_received == True, 1), else_=0)).label('responses')
                    ).group_by(JobApplication.source)
                ).all()
                
                for source, total, responses in source_success:
                    if total > 0 and responses / total > 0.3:  # 30% threshold
                        recommendations["high_success_sources"].append({
                            "source": source,
                            "success_rate": responses / total
                        })
                        
                # Analyze match scores with retry
                successful_scores = execute_with_retry(
                    db,
                    db.query(JobApplication.match_score)\
                    .filter(JobApplication.response_received == True)
                ).all()
                
                if successful_scores:
                    avg_score = sum(score[0] for score in successful_scores) / len(successful_scores)
                    recommendations["best_match_scores"].append({
                        "threshold": avg_score,
                        "message": f"Applications with match scores above {avg_score:.2f} "
                                 f"have higher success rates"
                    })
                    
                # Analyze application timing with retry
                time_success = execute_with_retry(
                    db,
                    db.query(
                        func.extract('hour', JobApplication.application_date).label('hour'),
                        func.count(JobApplication.id).label('total'),
                        func.sum(case((JobApplication.response_received == True, 1), else_=0)).label('responses')
                    ).group_by('hour')
                ).all()
                
                best_hours = [(hour, responses/total) for hour, total, responses in time_success 
                             if total > 0 and responses/total > 0.3]
                if best_hours:
                    recommendations["optimal_application_times"].extend([
                        {
                            "hour": hour,
                            "success_rate": rate,
                            "message": f"Applications submitted around {hour:02d}:00 "
                                     f"have {rate*100:.1f}% success rate"
                        }
                        for hour, rate in best_hours
                    ])
                    
                return recommendations
                
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {"error": str(e)}
    
    @time_vector_operation("search")
    def _timed_vector_search(self, index_name: str, query: str, k: int = 10) -> List[Tuple[Any, float]]:
        """Search vector index with performance monitoring."""
        return vector_db.search(index_name, query, k=k)
    
    @handle_db_errors
    @with_retry()
    def semantic_search_jobs(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform semantic search on job applications using FAISS vector database.
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            
        Returns:
            List of job application dictionaries with similarity scores
        """
        try:
            # Check if index exists
            with get_db() as db:
                index_exists = db.query(VectorIndex).filter_by(index_name=JOB_INDEX).first() is not None
            
            if not index_exists:
                logger.warning(f"Job application index '{JOB_INDEX}' does not exist")
                return []
            
            # Search vector index
            results = self._timed_vector_search(JOB_INDEX, query, k=limit)
            
            if not results:
                return []
            
            # Get full job details
            job_results = []
            with get_db() as db:
                for job_id, score in results:
                    job = db.query(JobApplication).filter_by(id=job_id).first()
                    if job:
                        job_results.append({
                            "id": job.id,
                            "job_id": job.job_id,
                            "job_title": job.job_title,
                            "company": job.company,
                            "status": job.status,
                            "match_score": job.match_score,
                            "similarity_score": float(score),
                            "application_date": job.application_date.isoformat(),
                            "source": job.source
                        })
            
            return job_results
            
        except Exception as e:
            logger.error(f"Error performing semantic job search: {e}")
            return []
    
    @handle_db_errors
    @with_retry()
    def semantic_search_skills(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform semantic search on job skills using FAISS vector database.
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            
        Returns:
            List of job skill dictionaries with similarity scores
        """
        try:
            # Check if index exists
            with get_db() as db:
                index_exists = db.query(VectorIndex).filter_by(index_name=SKILLS_INDEX).first() is not None
            
            if not index_exists:
                logger.warning(f"Skills index '{SKILLS_INDEX}' does not exist")
                return []
            
            # Search vector index
            results = self._timed_vector_search(SKILLS_INDEX, query, k=limit)
            
            if not results:
                return []
            
            # Get full skill details
            skill_results = []
            with get_db() as db:
                for skill_id, score in results:
                    skill = db.query(JobSkill).filter_by(id=skill_id).first()
                    if skill:
                        # Get associated job
                        job = db.query(JobApplication).filter_by(id=skill.application_id).first()
                        job_info = {
                            "job_id": "unknown",
                            "job_title": "unknown",
                            "company": "unknown"
                        }
                        if job:
                            job_info = {
                                "job_id": job.job_id,
                                "job_title": job.job_title,
                                "company": job.company
                            }
                        
                        skill_results.append({
                            "id": skill.id,
                            "skill_name": skill.skill_name,
                            "skill_category": skill.skill_category,
                            "required": skill.required,
                            "candidate_has": skill.candidate_has,
                            "match_score": skill.match_score,
                            "similarity_score": float(score),
                            "job": job_info
                        })
            
            return skill_results
            
        except Exception as e:
            logger.error(f"Error performing semantic skill search: {e}")
            return []
    
    @handle_db_errors
    @with_retry()
    def find_similar_jobs(self, job_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find jobs similar to a specific job using vector similarity.
        
        Args:
            job_id: Job ID to find similar jobs for
            limit: Maximum number of results to return
            
        Returns:
            List of similar job application dictionaries with similarity scores
        """
        try:
            # Get job details
            with get_db() as db:
                job = db.query(JobApplication).filter_by(job_id=job_id).first()
                if not job:
                    logger.warning(f"Job with ID {job_id} not found")
                    return []
                
                # If job has vector embedding stored, use it directly
                if job.vector_embedding:
                    embedding = np.frombuffer(job.vector_embedding, dtype=np.float32)
                    
                    # Get all job embeddings for comparison
                    all_jobs = db.query(
                        JobApplication.id, 
                        JobApplication.job_id,
                        JobApplication.job_title,
                        JobApplication.company,
                        JobApplication.status,
                        JobApplication.match_score,
                        JobApplication.application_date,
                        JobApplication.source,
                        JobApplication.vector_embedding
                    ).filter(
                        JobApplication.vector_embedding.isnot(None),
                        JobApplication.id != job.id  # Exclude the query job
                    ).all()
                    
                    # Calculate similarities
                    similarities = []
                    for j in all_jobs:
                        if j.vector_embedding:
                            j_embedding = np.frombuffer(j.vector_embedding, dtype=np.float32)
                            # Calculate cosine similarity
                            similarity = np.dot(embedding, j_embedding) / (np.linalg.norm(embedding) * np.linalg.norm(j_embedding))
                            similarities.append((j, float(similarity)))
                    
                    # Sort by similarity (highest first)
                    similarities.sort(key=lambda x: x[1], reverse=True)
                    
                    # Convert to result format
                    results = [{
                        "id": j.id,
                        "job_id": j.job_id,
                        "job_title": j.job_title,
                        "company": j.company,
                        "status": j.status,
                        "match_score": j.match_score,
                        "similarity_score": score,
                        "application_date": j.application_date.isoformat(),
                        "source": j.source
                    } for j, score in similarities[:limit]]
                    
                    return results
                
                # If no embedding, try using job description + title for search
                if job.job_description:
                    query_text = f"{job.job_title} {job.company} {job.job_description}"
                else:
                    query_text = f"{job.job_title} {job.company}"
                    
                return self.semantic_search_jobs(query_text, limit)
                
        except Exception as e:
            logger.error(f"Error finding similar jobs: {e}")
            return []
    
    @handle_db_errors
    @with_retry()
    def rebuild_vector_indices(self, batch_size: int = 100) -> bool:
        """
        Rebuild all vector indices from scratch.
        
        Args:
            batch_size: Batch size for processing
            
        Returns:
            True if successful
        """
        try:
            logger.info("Rebuilding vector indices...")
            
            # Create job index if it doesn't exist
            vector_db.create_index(JOB_INDEX, 384, "Flat")
            with get_db() as db:
                job_index = db.query(VectorIndex).filter_by(index_name=JOB_INDEX).first()
                if not job_index:
                    job_index = VectorIndex(
                        index_name=JOB_INDEX,
                        entity_type="jobs",
                        dimension=384,
                        index_type="Flat",
                        index_path=str(vector_db.index_dir / f"{JOB_INDEX}.index")
                    )
                    db.add(job_index)
                    safe_commit(db)
            
            # Create skills index if it doesn't exist
            vector_db.create_index(SKILLS_INDEX, 384, "Flat")
            with get_db() as db:
                skill_index = db.query(VectorIndex).filter_by(index_name=SKILLS_INDEX).first()
                if not skill_index:
                    skill_index = VectorIndex(
                        index_name=SKILLS_INDEX,
                        entity_type="skills",
                        dimension=384,
                        index_type="Flat",
                        index_path=str(vector_db.index_dir / f"{SKILLS_INDEX}.index")
                    )
                    db.add(skill_index)
                    safe_commit(db)
            
            # Process jobs in batches
            offset = 0
            total_jobs = 0
            while True:
                with get_db() as db:
                    jobs = db.query(JobApplication).offset(offset).limit(batch_size).all()
                    if not jobs:
                        break
                        
                    # Process job batch
                    items = []
                    for job in jobs:
                        text = f"{job.job_title} {job.company}"
                        if job.job_description:
                            text += f" {job.job_description}"
                        
                        items.append({
                            "id": job.id,
                            "text": text
                        })
                        
                        # Generate and store embedding
                        embedding = vector_db.embed_text(text)
                        job.vector_embedding = embedding.tobytes()
                    
                    safe_commit(db)
                    
                    # Add batch to index
                    if items:
                        vector_db.add_items(JOB_INDEX, items, text_field="text", id_field="id")
                        
                    total_jobs += len(jobs)
                    offset += batch_size
            
            # Process skills in batches
            offset = 0
            total_skills = 0
            while True:
                with get_db() as db:
                    skills = db.query(JobSkill).offset(offset).limit(batch_size).all()
                    if not skills:
                        break
                        
                    # Process skill batch
                    items = []
                    for skill in skills:
                        text = f"{skill.skill_name} {skill.skill_category}"
                        
                        items.append({
                            "id": skill.id,
                            "text": text
                        })
                        
                        # Generate and store embedding
                        embedding = vector_db.embed_text(text)
                        skill.vector_embedding = embedding.tobytes()
                    
                    safe_commit(db)
                    
                    # Add batch to index
                    if items:
                        vector_db.add_items(SKILLS_INDEX, items, text_field="text", id_field="id")
                        
                    total_skills += len(skills)
                    offset += batch_size
            
            # Update index records
            with get_db() as db:
                job_index = db.query(VectorIndex).filter_by(index_name=JOB_INDEX).first()
                if job_index:
                    job_index.item_count = total_jobs
                    job_index.updated_at = datetime.utcnow()
                
                skill_index = db.query(VectorIndex).filter_by(index_name=SKILLS_INDEX).first()
                if skill_index:
                    skill_index.item_count = total_skills
                    skill_index.updated_at = datetime.utcnow()
                    
                safe_commit(db)
            
            logger.info(f"Vector indices rebuilt: {total_jobs} jobs and {total_skills} skills indexed")
            return True
            
        except Exception as e:
            logger.error(f"Error rebuilding vector indices: {e}")
            return False