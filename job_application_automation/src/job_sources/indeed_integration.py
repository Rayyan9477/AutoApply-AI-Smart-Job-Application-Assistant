"""
Indeed job source integration.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
import logging
from urllib.parse import urlencode

from .base import JobSourceBase, JobListing

logger = logging.getLogger(__name__)

class IndeedIntegration(JobSourceBase):
    """Indeed job source integration."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Indeed integration.
        
        Args:
            config: Configuration dictionary for Indeed
        """
        super().__init__(config)
        self.api_key = config['api_key']
        self.publisher_id = config['publisher_id']
        self.base_url = "https://api.indeed.com/ads"
        self.session = None

    async def authenticate(self) -> bool:
        """Authenticate with Indeed API.
        
        Returns:
            bool: True if authentication was successful
        """
        if not self._validate_config(['api_key', 'publisher_id']):
            logger.error("Missing required Indeed configuration")
            return False

        try:
            self.session = aiohttp.ClientSession()
            # Test authentication by making a simple search
            test_params = {
                'publisher': self.publisher_id,
                'v': '2',
                'format': 'json',
                'q': 'software',
                'l': 'remote',
                'limit': '1'
            }
            
            async with self.session.get(
                f"{self.base_url}/apisearch?{urlencode(test_params)}",
                headers={'Authorization': f'Bearer {self.api_key}'}
            ) as response:
                if response.status == 200:
                    return True
                logger.error(f"Indeed authentication failed: {response.status}")
                return False
        except Exception as e:
            logger.error(f"Indeed authentication error: {str(e)}")
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
        """Search for jobs on Indeed.
        
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
            'publisher': self.publisher_id,
            'v': '2',
            'format': 'json',
            'q': ' '.join(keywords),
            'l': location or 'remote' if remote else '',
            'limit': str(results_per_page),
            'start': str((page - 1) * results_per_page)
        }

        if job_type:
            params['jt'] = job_type.lower()  # full-time, part-time, contract, etc.

        if salary_min:
            params['salary'] = f"${salary_min}"

        if posted_within_days:
            params['fromage'] = str(posted_within_days)

        try:
            async with self.session.get(
                f"{self.base_url}/apisearch?{urlencode(params)}",
                headers={'Authorization': f'Bearer {self.api_key}'}
            ) as response:
                if response.status != 200:
                    logger.error(f"Indeed search failed: {response.status}")
                    return []
                
                data = await response.json()
                results = []
                
                for job in data.get('results', []):
                    try:
                        job_listing = self._format_job_listing(job)
                        if job_listing:
                            results.append(job_listing)
                    except Exception as e:
                        logger.error(f"Error formatting Indeed job: {str(e)}")
                        continue
                
                return results
        except Exception as e:
            logger.error(f"Indeed search error: {str(e)}")
            return []

    async def get_job_details(self, job_id: str) -> Optional[JobListing]:
        """Get detailed information about a specific Indeed job.
        
        Args:
            job_id: ID of the job to get details for
            
        Returns:
            Optional[JobListing]: Job listing with full details if found
        """
        if not self.session:
            if not await self.authenticate():
                return None

        params = {
            'publisher': self.publisher_id,
            'v': '2',
            'format': 'json',
            'jobkeys': job_id
        }

        try:
            async with self.session.get(
                f"{self.base_url}/apigetjobs?{urlencode(params)}",
                headers={'Authorization': f'Bearer {self.api_key}'}
            ) as response:
                if response.status != 200:
                    logger.error(f"Indeed job details failed: {response.status}")
                    return None
                
                data = await response.json()
                jobs = data.get('results', [])
                
                if not jobs:
                    return None
                
                return self._format_job_listing(jobs[0])
        except Exception as e:
            logger.error(f"Indeed get job details error: {str(e)}")
            return None

    async def apply_to_job(self,
                        job_id: str,
                        resume_path: str,
                        cover_letter_path: Optional[str] = None,
                        answers: Optional[Dict[str, str]] = None) -> bool:
        """Apply to a job on Indeed.
        
        Args:
            job_id: ID of the job to apply to
            resume_path: Path to resume file
            cover_letter_path: Optional path to cover letter
            answers: Optional dictionary of answers to application questions
            
        Returns:
            bool: True if application was successful
        """
        # Indeed's API doesn't support direct job applications
        # Return the application URL instead
        logger.info("Indeed does not support direct applications via API. "
                   "Please apply through the job URL.")
        return False

    def _format_job_listing(self, raw_data: Dict[str, Any]) -> Optional[JobListing]:
        """Format raw Indeed job data into a JobListing object.
        
        Args:
            raw_data: Raw job data from the Indeed API
            
        Returns:
            Optional[JobListing]: Formatted job listing
        """
        try:
            # Parse the posting date
            posted_date = None
            if 'date' in raw_data:
                try:
                    posted_date = datetime.fromtimestamp(int(raw_data['date']))
                except (ValueError, TypeError):
                    pass

            # Extract salary range
            salary_range = None
            if 'salary' in raw_data:
                salary_range = raw_data['salary']

            # Determine remote type
            remote_type = None
            if raw_data.get('remote', False):
                remote_type = 'remote'
            elif 'location' in raw_data and 'hybrid' in raw_data['location'].lower():
                remote_type = 'hybrid'
            else:
                remote_type = 'on-site'

            return JobListing(
                job_id=raw_data['jobkey'],
                title=raw_data['jobtitle'],
                company=raw_data['company'],
                location=raw_data['formattedLocation'],
                description=raw_data.get('snippet', ''),
                url=raw_data['url'],
                salary_range=salary_range,
                job_type=raw_data.get('jobType'),
                posted_date=posted_date,
                remote_type=remote_type,
                source='indeed',
                raw_data=raw_data
            )
        except KeyError as e:
            logger.error(f"Missing required field in Indeed job data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error formatting Indeed job data: {str(e)}")
            return None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close() 