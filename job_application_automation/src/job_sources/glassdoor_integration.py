"""
Glassdoor job source integration.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
import logging
from urllib.parse import urlencode
import json

from .base import JobSourceBase, JobListing

logger = logging.getLogger(__name__)

class GlassdoorIntegration(JobSourceBase):
    """Glassdoor job source integration."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Glassdoor integration.
        
        Args:
            config: Configuration dictionary for Glassdoor
        """
        super().__init__(config)
        self.partner_id = config['partner_id']
        self.api_key = config['api_key']
        self.base_url = "https://api.glassdoor.com/v1"
        self.session = None

    async def authenticate(self) -> bool:
        """Authenticate with Glassdoor API.
        
        Returns:
            bool: True if authentication was successful
        """
        if not self._validate_config(['partner_id', 'api_key']):
            logger.error("Missing required Glassdoor configuration")
            return False

        try:
            self.session = aiohttp.ClientSession()
            # Test authentication by making a simple search
            test_params = {
                'v': '1',
                'format': 'json',
                'q': 'software engineer',
                'l': 'remote',
                'limit': '1',
                'userip': '0.0.0.0',  # Required by Glassdoor API
                'useragent': 'AutoApplyAI',  # Required by Glassdoor API
                'action': 'jobs-prog',
                'returnStates': 'true',
                'admLevelRequested': '1',
                't.p': self.partner_id,
                't.k': self.api_key
            }
            
            async with self.session.get(
                f"{self.base_url}/jobs-stats/jobs.htm?{urlencode(test_params)}"
            ) as response:
                if response.status == 200:
                    return True
                logger.error(f"Glassdoor authentication failed: {response.status}")
                return False
        except Exception as e:
            logger.error(f"Glassdoor authentication error: {str(e)}")
            return False

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
        """Search for jobs on Glassdoor.
        
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
        if not self.session:
            if not await self.authenticate():
                return []

        # Build search parameters
        params = {
            'v': '1',
            'format': 'json',
            'q': ' '.join(keywords),
            'l': location or 'remote' if remote else '',
            'pn': str(page),
            'limit': str(results_per_page),
            'userip': '0.0.0.0',  # Required by Glassdoor API
            'useragent': 'AutoApplyAI',  # Required by Glassdoor API
            'action': 'jobs-prog',
            'returnStates': 'true',
            'admLevelRequested': '1',
            't.p': self.partner_id,
            't.k': self.api_key
        }

        if job_type:
            params['jt'] = job_type.lower()

        if salary_min:
            params['minSalary'] = str(salary_min)

        if posted_within_days:
            params['fromAge'] = str(posted_within_days)

        try:
            async with self.session.get(
                f"{self.base_url}/jobs-stats/jobs.htm?{urlencode(params)}"
            ) as response:
                if response.status != 200:
                    logger.error(f"Glassdoor search failed: {response.status}")
                    return []
                
                data = await response.json()
                results = []
                
                for job in data.get('response', {}).get('jobListings', []):
                    try:
                        job_listing = self._format_job_listing(job)
                        if job_listing:
                            results.append(job_listing)
                    except Exception as e:
                        logger.error(f"Error formatting Glassdoor job: {str(e)}")
                        continue
                
                return results
        except Exception as e:
            logger.error(f"Glassdoor search error: {str(e)}")
            return []

    async def get_job_details(self, job_id: str) -> Optional[JobListing]:
        """Get detailed information about a specific Glassdoor job.
        
        Args:
            job_id: ID of the job to get details for
            
        Returns:
            Optional[JobListing]: Job listing with full details if found
        """
        if not self.session:
            if not await self.authenticate():
                return None

        params = {
            'v': '1',
            'format': 'json',
            'jobId': job_id,
            'userip': '0.0.0.0',
            'useragent': 'AutoApplyAI',
            'action': 'job-detail',
            't.p': self.partner_id,
            't.k': self.api_key
        }

        try:
            async with self.session.get(
                f"{self.base_url}/job-detail/job-detail.htm?{urlencode(params)}"
            ) as response:
                if response.status != 200:
                    logger.error(f"Glassdoor job details failed: {response.status}")
                    return None
                
                data = await response.json()
                job = data.get('response', {}).get('jobDetail')
                
                if not job:
                    return None
                
                return self._format_job_listing(job)
        except Exception as e:
            logger.error(f"Glassdoor get job details error: {str(e)}")
            return None

    async def apply_to_job(self,
                        job_id: str,
                        resume_path: str,
                        cover_letter_path: Optional[str] = None,
                        answers: Optional[Dict[str, str]] = None) -> bool:
        """Apply to a job on Glassdoor.
        
        Args:
            job_id: ID of the job to apply to
            resume_path: Path to resume file
            cover_letter_path: Optional path to cover letter
            answers: Optional dictionary of answers to application questions
            
        Returns:
            bool: True if application was successful
        """
        # Glassdoor's API doesn't support direct job applications
        # Return the application URL instead
        logger.info("Glassdoor does not support direct applications via API. "
                   "Please apply through the job URL.")
        return False

    def _format_job_listing(self, raw_data: Dict[str, Any]) -> Optional[JobListing]:
        """Format raw Glassdoor job data into a JobListing object.
        
        Args:
            raw_data: Raw job data from the Glassdoor API
            
        Returns:
            Optional[JobListing]: Formatted job listing
        """
        try:
            # Parse the posting date
            posted_date = None
            if 'listingDate' in raw_data:
                try:
                    posted_date = datetime.strptime(raw_data['listingDate'], '%Y-%m-%d')
                except (ValueError, TypeError):
                    pass

            # Extract salary range
            salary_range = None
            if 'salaryLow' in raw_data and 'salaryHigh' in raw_data:
                salary_range = f"${raw_data['salaryLow']:,} - ${raw_data['salaryHigh']:,}"
            elif 'salaryEstimate' in raw_data:
                salary_range = raw_data['salaryEstimate']

            # Determine remote type
            remote_type = None
            if raw_data.get('isRemote', False):
                remote_type = 'remote'
            elif raw_data.get('isHybrid', False):
                remote_type = 'hybrid'
            else:
                remote_type = 'on-site'

            # Extract skills
            required_skills = []
            preferred_skills = []
            if 'jobReqs' in raw_data:
                for req in raw_data['jobReqs']:
                    if req.get('isRequired', True):
                        required_skills.append(req['name'])
                    else:
                        preferred_skills.append(req['name'])

            return JobListing(
                job_id=str(raw_data['jobId']),
                title=raw_data['jobTitle'],
                company=raw_data['employer']['name'],
                location=raw_data.get('location', ''),
                description=raw_data.get('jobDescription', ''),
                url=raw_data.get('jobLink', ''),
                salary_range=salary_range,
                job_type=raw_data.get('jobType'),
                experience_level=raw_data.get('experienceLevel'),
                posted_date=posted_date,
                required_skills=required_skills,
                preferred_skills=preferred_skills,
                remote_type=remote_type,
                source='glassdoor',
                raw_data=raw_data
            )
        except KeyError as e:
            logger.error(f"Missing required field in Glassdoor job data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error formatting Glassdoor job data: {str(e)}")
            return None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close() 