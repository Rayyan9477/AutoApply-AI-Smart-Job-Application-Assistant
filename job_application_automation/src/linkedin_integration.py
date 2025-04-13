"""
LinkedIn integration module using LinkedIn MCP.
This module provides functionality to interact with LinkedIn for job searching
and application submission.
"""

import os
import time
import json
import logging
import asyncio
import requests
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta

# Import configuration
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.linkedin_mcp_config import LinkedInMCPConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../data/linkedin_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LinkedInIntegration:
    """
    Class for LinkedIn integration using LinkedIn MCP.
    This class provides methods to interact with LinkedIn for job searching
    and application submission.
    """

    def __init__(self, config: Optional[LinkedInMCPConfig] = None):
        """
        Initialize the LinkedInIntegration with configuration settings.
        
        Args:
            config: Configuration settings for LinkedIn integration.
                   If None, default settings will be used.
        """
        self.config = config or LinkedInMCPConfig()
        self._setup_mcp_server()
        self.access_token = None
        self.token_expiry = None
        
    def _setup_mcp_server(self) -> None:
        """Set up the MCP server for LinkedIn integration."""
        # Ensure session storage directory exists
        os.makedirs(self.config.session_storage_path, exist_ok=True)
        
        # Import required modules only when used
        try:
            # Using a relative import for the linkedin_mcp module
            from linkedin_mcp import LinkedInMCPServer
            
            # Initialize the MCP server
            self.mcp_server = LinkedInMCPServer(
                host=self.config.mcp_server_host,
                port=self.config.mcp_server_port,
                debug=self.config.mcp_server_debug
            )
            logger.info(f"LinkedIn MCP server initialized at {self.config.mcp_server_host}:{self.config.mcp_server_port}")
        except ImportError as e:
            logger.error(f"Failed to import linkedin_mcp: {e}")
            logger.error("Please ensure the linkedin_mcp package is installed.")
            self.mcp_server = None
            
    async def authenticate(self) -> bool:
        """
        Authenticate with LinkedIn using OAuth 2.0.
        
        Returns:
            True if authentication was successful, False otherwise.
        """
        # Check if we already have a valid token
        if self._is_token_valid():
            logger.info("Using existing LinkedIn access token")
            return True
            
        # Import required modules only when used
        try:
            from linkedin_mcp.auth import LinkedInOAuth2
            
            # Initialize OAuth2 handler
            oauth = LinkedInOAuth2(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret.get_secret_value(),
                redirect_uri=self.config.redirect_uri,
                scopes=self.config.scopes
            )
            
            # Start authentication flow
            auth_url = oauth.get_authorization_url()
            logger.info(f"Please open this URL to authenticate with LinkedIn: {auth_url}")
            
            # In a real application, this would redirect the user to auth_url
            # and then capture the authorization code from the callback
            # For this example, we'll simulate manual input of the authorization code
            print(f"Please open this URL in your browser:")
            print(auth_url)
            print("After authenticating, you will be redirected. Copy the 'code' parameter from the URL and enter it here:")
            auth_code = input("Enter authorization code: ")
            
            # Exchange the authorization code for an access token
            token_info = oauth.get_access_token(auth_code)
            
            if token_info and "access_token" in token_info:
                self.access_token = token_info["access_token"]
                # Set token expiry (default to 1 hour if not provided)
                expires_in = token_info.get("expires_in", 3600)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                # Save token to session
                self._save_token(token_info)
                
                logger.info("LinkedIn authentication successful")
                return True
            else:
                logger.error("Failed to obtain LinkedIn access token")
                return False
                
        except Exception as e:
            logger.error(f"LinkedIn authentication error: {e}")
            return False
            
    def _is_token_valid(self) -> bool:
        """
        Check if the current access token is valid.
        
        Returns:
            True if the token is valid, False otherwise.
        """
        if not self.access_token or not self.token_expiry:
            # Try to load from session
            token_info = self._load_token()
            if token_info:
                self.access_token = token_info.get("access_token")
                expires_at = token_info.get("expires_at")
                if expires_at:
                    self.token_expiry = datetime.fromisoformat(expires_at)
            else:
                return False
                
        # Check if token is still valid
        if self.token_expiry and datetime.now() < self.token_expiry - timedelta(minutes=5):  # 5-minute buffer
            return True
            
        return False
        
    def _save_token(self, token_info: Dict[str, Any]) -> None:
        """
        Save the token information to a file.
        
        Args:
            token_info: Token information to save.
        """
        try:
            # Add expiry timestamp
            if "expires_in" in token_info:
                expires_at = datetime.now() + timedelta(seconds=token_info["expires_in"])
                token_info["expires_at"] = expires_at.isoformat()
                
            session_file = os.path.join(self.config.session_storage_path, "linkedin_session.json")
            with open(session_file, "w") as f:
                json.dump(token_info, f, indent=2)
                
            logger.info(f"LinkedIn session saved to {session_file}")
            
        except Exception as e:
            logger.error(f"Error saving LinkedIn session: {e}")
            
    def _load_token(self) -> Dict[str, Any]:
        """
        Load token information from a file.
        
        Returns:
            Token information if available, empty dictionary otherwise.
        """
        try:
            session_file = os.path.join(self.config.session_storage_path, "linkedin_session.json")
            if not os.path.exists(session_file):
                return {}
                
            with open(session_file, "r") as f:
                token_info = json.load(f)
                
            logger.info(f"LinkedIn session loaded from {session_file}")
            return token_info
            
        except Exception as e:
            logger.error(f"Error loading LinkedIn session: {e}")
            return {}
            
    async def search_jobs(self, 
                   keywords: Optional[List[str]] = None,
                   location: Optional[str] = None,
                   count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for jobs on LinkedIn.
        
        Args:
            keywords: List of job keywords to search for.
            location: Location to search for jobs.
            count: Number of job results to return.
            
        Returns:
            A list of job listings from LinkedIn.
        """
        if not self._is_token_valid():
            success = await self.authenticate()
            if not success:
                logger.error("LinkedIn authentication required")
                return []
                
        keywords_str = " ".join(keywords) if keywords else ""
        count = count or self.config.default_job_search_count
        
        try:
            # Use LinkedIn MCP to search for jobs
            from linkedin_mcp.jobs import JobSearch
            
            job_search = JobSearch(
                access_token=self.access_token,
                base_url=str(self.config.api_base_url)
            )
            
            # Convert filter parameters to LinkedIn API format
            filters = {}
            if self.config.job_search_filters.get("locations"):
                filters["location"] = self.config.job_search_filters["locations"]
                
            if location:
                # Override with specified location if provided
                filters["location"] = [location]
                
            if self.config.job_search_filters.get("industries"):
                filters["industry"] = self.config.job_search_filters["industries"]
                
            if self.config.job_search_filters.get("experience"):
                filters["experience"] = self.config.job_search_filters["experience"]
                
            if self.config.job_search_filters.get("job_types"):
                filters["job_type"] = self.config.job_search_filters["job_types"]
                
            # Perform job search
            results = await job_search.search(
                keywords=keywords_str,
                count=count,
                filters=filters
            )
            
            # Process search results
            job_listings = []
            if results and "elements" in results:
                for job in results["elements"]:
                    job_listing = self._parse_linkedin_job(job)
                    if job_listing:
                        job_listings.append(job_listing)
                        
            logger.info(f"Found {len(job_listings)} jobs on LinkedIn")
            
            # Save job listings to a file
            self._save_job_listings(job_listings)
            
            return job_listings
            
        except Exception as e:
            logger.error(f"LinkedIn job search error: {e}")
            return []
            
    def _parse_linkedin_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse LinkedIn job data into a standardized format.
        
        Args:
            job_data: Job data from LinkedIn API.
            
        Returns:
            A standardized job listing dictionary.
        """
        try:
            job_listing = {}
            
            # Extract basic job information
            if "title" in job_data:
                job_listing["job_title"] = job_data["title"]
                
            if "company" in job_data and "name" in job_data["company"]:
                job_listing["company"] = job_data["company"]["name"]
                
            if "location" in job_data:
                job_listing["location"] = job_data["location"]
                
            # Extract job URL
            if "job_id" in job_data:
                job_listing["url"] = f"https://www.linkedin.com/jobs/view/{job_data['job_id']}/"
                job_listing["job_id"] = job_data["job_id"]
                
            # Extract posting date
            if "posted_at" in job_data:
                job_listing["posted_date"] = job_data["posted_at"]
                
            # Extract application URL if available
            if "application_url" in job_data:
                job_listing["application_url"] = job_data["application_url"]
                
            return job_listing
            
        except Exception as e:
            logger.error(f"Error parsing LinkedIn job: {e}")
            return {}
            
    def _save_job_listings(self, job_listings: List[Dict[str, Any]]) -> None:
        """
        Save LinkedIn job listings to a JSON file.
        
        Args:
            job_listings: List of job listings to save.
        """
        try:
            output_file = "../data/linkedin_job_listings.json"
            with open(output_file, "w") as f:
                json.dump(job_listings, f, indent=2)
                
            logger.info(f"Saved {len(job_listings)} LinkedIn job listings to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving LinkedIn job listings: {e}")
            
    async def get_job_description(self, job_id: str) -> Dict[str, Any]:
        """
        Get detailed job description for a specific job.
        
        Args:
            job_id: LinkedIn job ID.
            
        Returns:
            Job description as a dictionary.
        """
        if not self._is_token_valid():
            success = await self.authenticate()
            if not success:
                logger.error("LinkedIn authentication required")
                return {}
                
        try:
            # Use LinkedIn MCP to get job details
            from linkedin_mcp.jobs import JobDetails
            
            job_details = JobDetails(
                access_token=self.access_token,
                base_url=str(self.config.api_base_url)
            )
            
            # Get job description
            description = await job_details.get_job_description(job_id)
            
            return description or {}
            
        except Exception as e:
            logger.error(f"Error getting LinkedIn job description: {e}")
            return {}
            
    async def get_user_profile(self) -> Dict[str, Any]:
        """
        Get the user's LinkedIn profile.
        
        Returns:
            User profile as a dictionary.
        """
        if not self._is_token_valid():
            success = await self.authenticate()
            if not success:
                logger.error("LinkedIn authentication required")
                return {}
                
        try:
            # Use LinkedIn MCP to get user profile
            from linkedin_mcp.profile import UserProfile
            
            user_profile = UserProfile(
                access_token=self.access_token,
                base_url=str(self.config.api_base_url)
            )
            
            # Get basic profile information
            profile = await user_profile.get_profile()
            
            # Get additional profile details if available
            if profile and "id" in profile:
                try:
                    # Get work experience
                    experience = await user_profile.get_experience()
                    if experience:
                        profile["experience"] = experience
                        
                    # Get education
                    education = await user_profile.get_education()
                    if education:
                        profile["education"] = education
                        
                    # Get skills
                    skills = await user_profile.get_skills()
                    if skills:
                        profile["skills"] = skills
                        
                except Exception as e:
                    logger.warning(f"Error getting additional profile details: {e}")
                    
            return profile or {}
            
        except Exception as e:
            logger.error(f"Error getting LinkedIn user profile: {e}")
            return {}
            
    async def apply_to_job(self, 
                     job_id: str,
                     resume_path: Optional[str] = None,
                     cover_letter_path: Optional[str] = None) -> bool:
        """
        Apply to a job on LinkedIn.
        
        Args:
            job_id: LinkedIn job ID.
            resume_path: Path to resume file.
            cover_letter_path: Path to cover letter file.
            
        Returns:
            True if application was successful, False otherwise.
        """
        if not self.config.auto_apply_enabled:
            logger.warning("Auto-apply is disabled in configuration")
            return False
            
        # Check if we've exceeded the application rate limit
        if not self._check_rate_limit_applications():
            logger.warning("Application rate limit exceeded")
            return False
            
        if not self._is_token_valid():
            success = await self.authenticate()
            if not success:
                logger.error("LinkedIn authentication required")
                return False
                
        # Use default resume path if not provided
        resume_path = resume_path or self.config.resume_path
        
        if not os.path.exists(resume_path):
            logger.error(f"Resume file not found at {resume_path}")
            return False
            
        try:
            # Use LinkedIn MCP to apply for the job
            from linkedin_mcp.jobs import JobApplication
            
            job_application = JobApplication(
                access_token=self.access_token,
                base_url=str(self.config.api_base_url)
            )
            
            # Prepare application files
            files = {"resume": open(resume_path, "rb")}
            
            if cover_letter_path and os.path.exists(cover_letter_path):
                files["cover_letter"] = open(cover_letter_path, "rb")
                
            # Submit application
            result = await job_application.apply(
                job_id=job_id,
                files=files
            )
            
            # Close file handles
            for f in files.values():
                f.close()
                
            if result and result.get("status") == "success":
                logger.info(f"Successfully applied to job {job_id}")
                self._update_application_history(job_id)
                return True
            else:
                logger.error(f"Failed to apply to job {job_id}: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error applying to LinkedIn job: {e}")
            return False
            
    def _check_rate_limit_applications(self) -> bool:
        """
        Check if we've exceeded the application rate limit.
        
        Returns:
            True if we can proceed with the application, False otherwise.
        """
        try:
            # Load application history
            history_file = os.path.join(self.config.session_storage_path, "application_history.json")
            history = []
            
            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    history = json.load(f)
                    
            # Count applications in the last hour
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_applications = [
                app for app in history 
                if datetime.fromisoformat(app["timestamp"]) > one_hour_ago
            ]
            
            # Count applications today
            today = datetime.now().date()
            today_applications = [
                app for app in history 
                if datetime.fromisoformat(app["timestamp"]).date() == today
            ]
            
            # Check rate limits
            if len(recent_applications) >= self.config.rate_limit_applications:
                logger.warning(f"Application rate limit exceeded: {len(recent_applications)} applications in the last hour")
                return False
                
            if len(today_applications) >= self.config.max_applications_per_day:
                logger.warning(f"Daily application limit exceeded: {len(today_applications)} applications today")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking application rate limit: {e}")
            # Default to allowing the application if we can't check the rate limit
            return True
            
    def _update_application_history(self, job_id: str) -> None:
        """
        Update the application history after applying to a job.
        
        Args:
            job_id: LinkedIn job ID that was applied to.
        """
        try:
            # Load application history
            history_file = os.path.join(self.config.session_storage_path, "application_history.json")
            history = []
            
            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    history = json.load(f)
                    
            # Add new application to history
            history.append({
                "job_id": job_id,
                "timestamp": datetime.now().isoformat()
            })
            
            # Save updated history
            with open(history_file, "w") as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating application history: {e}")

    async def generate_application_materials(self, 
                              job_id: str,
                              cover_letter_type: Optional[str] = None) -> Dict[str, str]:
        """
        Generate resume and cover letter for a specific job.
        
        Args:
            job_id: LinkedIn job ID.
            cover_letter_type: Type of cover letter to generate (standard, creative, technical, 
                               executive, career_change, referral). If None, will auto-select.
            
        Returns:
            Dictionary with paths to generated resume and cover letter.
        """
        result = {
            "resume_path": "",
            "cover_letter_path": "",
            "job_title": "",
            "company": ""
        }
        
        try:
            # Get job description
            job_details = await self.get_job_description(job_id)
            
            if not job_details:
                logger.error(f"Failed to get job description for job ID: {job_id}")
                return result
                
            job_title = job_details.get("title", "Unknown Position")
            company_name = job_details.get("company", {}).get("name", "Unknown Company")
            
            # Get full job description text
            job_description_text = job_details.get("description", "")
            if not job_description_text:
                logger.error(f"Job description text not found for job ID: {job_id}")
                return result
                
            # Get user profile to use as candidate profile
            user_profile = await self.get_user_profile()
            if not user_profile:
                logger.error("Failed to get user profile")
                return result
                
            # Transform LinkedIn profile into candidate profile
            candidate_profile = self._transform_profile_to_candidate(user_profile)
            
            # Get company information
            company_info = job_details.get("company", {}).get("description", "")
            if not company_info:
                company_info = f"{company_name} is a company hiring for a {job_title} position."
            
            # Import the resume generator dynamically to avoid circular imports
            from src.resume_cover_letter_generator import ResumeGenerator, CoverLetterTemplate
            
            # Create resume generator
            resume_generator = ResumeGenerator()
            
            # Generate resume
            resume_path, resume_content = resume_generator.generate_resume(
                job_description=job_description_text,
                candidate_profile=candidate_profile
            )
            
            # Determine cover letter type
            template_type = None
            if cover_letter_type:
                try:
                    template_type = CoverLetterTemplate[cover_letter_type.upper()]
                except (KeyError, AttributeError):
                    logger.warning(f"Invalid cover letter type: {cover_letter_type}. Auto-selecting type.")
            
            # Generate cover letter
            cover_letter_path, _ = resume_generator.generate_cover_letter(
                job_description=job_description_text,
                candidate_resume=resume_content,
                company_info=company_info,
                template_type=template_type
            )
            
            result["resume_path"] = resume_path
            result["cover_letter_path"] = cover_letter_path
            result["job_title"] = job_title
            result["company"] = company_name
            
            logger.info(f"Generated application materials for {job_title} at {company_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating application materials: {e}")
            return result
            
    def _transform_profile_to_candidate(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform LinkedIn profile into candidate profile format for resume generation.
        
        Args:
            profile: LinkedIn profile data.
            
        Returns:
            Candidate profile dictionary.
        """
        candidate = {}
        
        try:
            # Basic information
            candidate["name"] = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
            
            if "email" in profile:
                candidate["email"] = profile["email"]
                
            if "phone_numbers" in profile and profile["phone_numbers"]:
                candidate["phone"] = profile["phone_numbers"][0]
                
            # Location
            if "location" in profile:
                location_parts = []
                if "city" in profile["location"]:
                    location_parts.append(profile["location"]["city"])
                if "state" in profile["location"]:
                    location_parts.append(profile["location"]["state"])
                if "country" in profile["location"]:
                    location_parts.append(profile["location"]["country"])
                    
                candidate["location"] = ", ".join(location_parts)
                
            # Summary/Headline
            if "headline" in profile:
                candidate["summary"] = profile["headline"]
                
            # Experience
            if "experience" in profile and profile["experience"]:
                experiences = []
                for exp in profile["experience"]:
                    experience = {}
                    
                    if "title" in exp:
                        experience["title"] = exp["title"]
                        
                    if "company" in exp:
                        experience["company"] = exp["company"]["name"] if isinstance(exp["company"], dict) else exp["company"]
                        
                    # Format dates
                    if "start_date" in exp:
                        start_year = exp["start_date"].get("year", "")
                        experience["start"] = str(start_year)
                        
                    if "end_date" in exp:
                        end_year = exp["end_date"].get("year", "Present")
                        experience["end"] = str(end_year)
                        
                    experience["duration"] = f"{experience.get('start', '')} - {experience.get('end', 'Present')}"
                    
                    if "description" in exp:
                        experience["description"] = exp["description"]
                        
                    experiences.append(experience)
                    
                candidate["experience"] = experiences
                
            # Education
            if "education" in profile and profile["education"]:
                education = []
                for edu in profile["education"]:
                    edu_item = {}
                    
                    if "school" in edu:
                        edu_item["institution"] = edu["school"]["name"] if isinstance(edu["school"], dict) else edu["school"]
                        
                    if "degree" in edu:
                        edu_item["degree"] = edu["degree"]["name"] if isinstance(edu["degree"], dict) else edu["degree"]
                        
                    if "field_of_study" in edu:
                        edu_item["field"] = edu["field_of_study"]
                        
                    if "end_date" in edu and "year" in edu["end_date"]:
                        edu_item["year"] = str(edu["end_date"]["year"])
                        
                    education.append(edu_item)
                    
                candidate["education"] = education
                
            # Skills
            if "skills" in profile and profile["skills"]:
                skills = []
                for skill in profile["skills"]:
                    if isinstance(skill, dict):
                        skills.append(skill.get("name", ""))
                    else:
                        skills.append(skill)
                        
                candidate["skills"] = skills
                
        except Exception as e:
            logger.error(f"Error transforming profile to candidate: {e}")
            
        return candidate
    
    
    async def full_application_workflow(self, 
                                 keywords: List[str], 
                                 location: str,
                                 count: int = 5,
                                 auto_apply: bool = False) -> List[Dict[str, Any]]:
        """
        Execute full job application workflow: search, generate materials, and optionally apply.
        
        Args:
            keywords: List of job keywords to search for.
            location: Location to search for jobs.
            count: Number of job results to process.
            auto_apply: Whether to automatically apply to jobs.
            
        Returns:
            List of dictionaries with job and application information.
        """
        results = []
        
        try:
            # 1. Search for jobs
            jobs = await self.search_jobs(keywords=keywords, location=location, count=count)
            
            if not jobs:
                logger.info("No jobs found")
                return results
                
            logger.info(f"Processing {len(jobs)} jobs for application workflow")
            
            # 2. For each job, generate application materials
            for job in jobs:
                job_id = job.get("job_id")
                if not job_id:
                    logger.warning(f"Job ID not found: {job}")
                    continue
                    
                logger.info(f"Processing job: {job.get('job_title')} at {job.get('company')}")
                
                # Generate application materials
                materials = await self.generate_application_materials(job_id)
                
                result = {
                    "job": job,
                    "materials": materials
                }
                
                # 3. Apply to job if auto-apply is enabled
                if auto_apply and self.config.auto_apply_enabled:
                    if materials["resume_path"] and materials["cover_letter_path"]:
                        # Wait a random time to appear more human-like
                        wait_time = self.config.min_application_delay + (
                            self.config.max_application_delay - self.config.min_application_delay
                        ) * random.random()
                        
                        logger.info(f"Waiting {wait_time:.1f} seconds before applying...")
                        await asyncio.sleep(wait_time)
                        
                        # Apply to job
                        success = await self.apply_to_job(
                            job_id=job_id,
                            resume_path=materials["resume_path"],
                            cover_letter_path=materials["cover_letter_path"]
                        )
                        
                        result["applied"] = success
                        
                results.append(result)
                
            return results
            
        except Exception as e:
            logger.error(f"Error in full application workflow: {e}")
            return results


# Example usage
async def main():
    linkedin = LinkedInIntegration()
    authenticated = await linkedin.authenticate()
    
    if authenticated:
        jobs = await linkedin.search_jobs(
            keywords=["software engineer", "python"],
            location="New York"
        )
        
        print(f"Found {len(jobs)} jobs on LinkedIn")
        
        # Get the user's profile
        profile = await linkedin.get_user_profile()
        print(f"User profile: {profile.get('first_name', '')} {profile.get('last_name', '')}")
        
        # Get job details for the first job
        if jobs:
            job_id = jobs[0].get("job_id")
            if job_id:
                job_details = await linkedin.get_job_description(job_id)
                print(f"Job details: {job_details}")


if __name__ == "__main__":
    asyncio.run(main())