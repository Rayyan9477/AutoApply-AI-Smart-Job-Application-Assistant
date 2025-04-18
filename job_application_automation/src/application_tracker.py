"""
Application tracking system with error handling and retries.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from .database import get_db, execute_with_retry
from .models import JobApplication, ApplicationInteraction, JobSkill, SearchHistory
from config.logging_config import AuditLogger
from .database_errors import handle_db_errors, with_retry, safe_commit, DatabaseError

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
                    url=url
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