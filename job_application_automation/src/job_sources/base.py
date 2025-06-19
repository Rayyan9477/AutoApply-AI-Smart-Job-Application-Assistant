"""
Base class for job source integrations.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class JobListing:
    """Data class for job listings."""
    job_id: str
    title: str
    company: str
    location: str
    description: str
    url: str
    salary_range: Optional[str] = None
    job_type: Optional[str] = None  # full-time, part-time, contract, etc.
    experience_level: Optional[str] = None
    posted_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    required_skills: List[str] = None
    preferred_skills: List[str] = None
    benefits: List[str] = None
    remote_type: Optional[str] = None  # remote, hybrid, on-site
    source: str = None  # linkedin, indeed, glassdoor
    raw_data: Dict[str, Any] = None  # Store the raw API response

    def __post_init__(self):
        """Initialize optional lists."""
        self.required_skills = self.required_skills or []
        self.preferred_skills = self.preferred_skills or []
        self.benefits = self.benefits or []
        self.raw_data = self.raw_data or {}

class JobSourceBase(ABC):
    """Base class for job source integrations."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the job source.
        
        Args:
            config: Configuration dictionary for the job source
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        self.rate_limit = config.get('rate_limit', 60)  # requests per minute
        self._last_request_time = None
        self._request_count = 0

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the job source API.
        
        Returns:
            bool: True if authentication was successful
        """
        pass

    @abstractmethod
    async def search_jobs(self,
                       keywords: List[str],
                       location: Optional[str] = None,
                       job_type: Optional[str] = None,
                       experience_level: Optional[str] = None,
                       remote: Optional[bool] = None,
                       posted_within_days: Optional[int] = None,
                       salary_min: Optional[int] = None,
                       page: int = 1,
                       results_per_page: int = 25) -> List[JobListing]:
        """Search for jobs with the given criteria.
        
        Args:
            keywords: List of keywords to search for
            location: Location to search in
            job_type: Type of job (full-time, part-time, contract)
            experience_level: Required experience level
            remote: Whether to search for remote jobs
            posted_within_days: Only show jobs posted within this many days
            salary_min: Minimum salary requirement
            page: Page number for pagination
            results_per_page: Number of results per page
            
        Returns:
            List[JobListing]: List of job listings matching the criteria
        """
        pass

    @abstractmethod
    async def get_job_details(self, job_id: str) -> Optional[JobListing]:
        """Get detailed information about a specific job.
        
        Args:
            job_id: ID of the job to get details for
            
        Returns:
            Optional[JobListing]: Job listing with full details if found
        """
        pass

    @abstractmethod
    async def apply_to_job(self,
                        job_id: str,
                        resume_path: str,
                        cover_letter_path: Optional[str] = None,
                        answers: Optional[Dict[str, str]] = None) -> bool:
        """Apply to a job.
        
        Args:
            job_id: ID of the job to apply to
            resume_path: Path to resume file
            cover_letter_path: Optional path to cover letter
            answers: Optional dictionary of answers to application questions
            
        Returns:
            bool: True if application was successful
        """
        pass

    async def check_application_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of an application.
        
        Args:
            job_id: ID of the job to check status for
            
        Returns:
            Dict with application status information
        """
        raise NotImplementedError("This job source does not support checking application status")

    def _validate_config(self, required_keys: List[str]) -> bool:
        """Validate that all required configuration keys are present.
        
        Args:
            required_keys: List of required configuration keys
            
        Returns:
            bool: True if all required keys are present
        """
        return all(key in self.config for key in required_keys)

    def _format_job_listing(self, raw_data: Dict[str, Any]) -> JobListing:
        """Format raw job data into a JobListing object.
        
        Args:
            raw_data: Raw job data from the API
            
        Returns:
            JobListing: Formatted job listing
        """
        raise NotImplementedError("Each job source must implement its own _format_job_listing method") 