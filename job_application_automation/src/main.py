"""
Main module for job application automation.
This module orchestrates the entire job application process, from searching for jobs
to applying with personalized resumes and cover letters.
"""

import os
import json
import asyncio
import logging
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
import random

# Import project modules
from browser_automation import JobSearchBrowser
from web_scraping import JobDetailsScraper
from linkedin_integration import LinkedInIntegration
from resume_cover_letter_generator import ResumeGenerator
from application_tracker import ApplicationTracker

# Import configuration
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.browser_config import BrowserConfig
from config.crawl4ai_config import Crawl4AIConfig
from config.linkedin_mcp_config import LinkedInMCPConfig
from config.llama_config import LlamaConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../data/main.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class JobApplicationAutomation:
    """
    Main class for job application automation.
    This class orchestrates the entire job application process.
    """

    def __init__(self,
            browser_config: Optional[BrowserConfig] = None,
            crawl4ai_config: Optional[Crawl4AIConfig] = None,
            linkedin_config: Optional[LinkedInMCPConfig] = None,
            llama_config: Optional[LlamaConfig] = None):
        """
        Initialize the JobApplicationAutomation with configuration settings.
        
        Args:
            browser_config: Configuration for browser automation.
            crawl4ai_config: Configuration for web scraping.
            linkedin_config: Configuration for LinkedIn integration.
            llama_config: Configuration for LLM integration.
        """
        # Initialize configurations
        self.browser_config = browser_config or BrowserConfig()
        self.crawl4ai_config = crawl4ai_config or Crawl4AIConfig()
        self.linkedin_config = linkedin_config or LinkedInMCPConfig()
        self.llama_config = llama_config or LlamaConfig()
        
        # Initialize components
        self.job_search_browser = JobSearchBrowser(self.browser_config)
        self.job_details_scraper = JobDetailsScraper(self.crawl4ai_config)
        self.linkedin_integration = LinkedInIntegration(self.linkedin_config)
        self.resume_generator = ResumeGenerator(self.llama_config)
        
        # Application state
        self.job_listings = []
        self.job_details = []
        self.candidate_profile = {}
        self.applications_submitted = 0
        
        # Create necessary directories
        os.makedirs("../data", exist_ok=True)
        os.makedirs("../data/generated_cover_letters", exist_ok=True)
        
        # Initialize application tracker
        self.application_tracker = ApplicationTracker()
        
        logger.info("Job Application Automation initialized")
        
    async def setup(self) -> bool:
        """
        Set up the job application automation by loading the candidate profile
        and authenticating with LinkedIn.
        
        Returns:
            True if setup was successful, False otherwise.
        """
        # Load candidate profile
        success = self._load_candidate_profile()
        if not success:
            logger.error("Failed to load candidate profile")
            return False
            
        # Authenticate with LinkedIn if needed
        authenticated = await self.linkedin_integration.authenticate()
        if not authenticated:
            logger.warning("LinkedIn authentication failed, some features may not be available")
            # Continue anyway, as we can still use web scraping for job search
            
        return True
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def search_jobs(self, 
                   keywords: List[str], 
                   location: str, 
                   use_linkedin: bool = True,
                   use_browser: bool = True,
                   job_site: str = "linkedin") -> List[Dict[str, Any]]:
        """
        Search for jobs using the specified keywords and location.
        
        Args:
            keywords: List of job keywords to search for.
            location: Location to search for jobs.
            use_linkedin: Whether to use LinkedIn API for job search.
            use_browser: Whether to use browser automation for job search.
            job_site: Job search website to use for browser automation.
            
        Returns:
            A list of job listings.
        """
        combined_job_listings = []
        
        # Search using LinkedIn API if requested
        if use_linkedin:
            try:
                logger.info(f"Searching for jobs on LinkedIn with keywords {keywords} in {location}")
                linkedin_jobs = await self.linkedin_integration.search_jobs(keywords, location)
                combined_job_listings.extend(linkedin_jobs)
                logger.info(f"Found {len(linkedin_jobs)} jobs on LinkedIn")
            except Exception as e:
                logger.error(f"Error searching jobs on LinkedIn: {e}")
                
        # Search using browser automation if requested
        if use_browser:
            try:
                logger.info(f"Searching for jobs on {job_site} with keywords {keywords} in {location}")
                browser_jobs = await self.job_search_browser.search_for_jobs(keywords, location, job_site)
                combined_job_listings.extend(browser_jobs)
                logger.info(f"Found {len(browser_jobs)} jobs through browser automation")
            except Exception as e:
                logger.error(f"Error searching jobs with browser automation: {e}")
                
        # Save all job listings
        self.job_listings = combined_job_listings
        
        # Save combined job listings to file
        try:
            with open("../data/combined_job_listings.json", "w") as f:
                json.dump(combined_job_listings, f, indent=2)
            logger.info(f"Saved {len(combined_job_listings)} combined job listings")
        except Exception as e:
            logger.error(f"Error saving combined job listings: {e}")
            
        return combined_job_listings
        
    async def scrape_job_details(self, max_jobs: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape detailed information for the jobs found during search.
        
        Args:
            max_jobs: Maximum number of jobs to scrape details for.
            
        Returns:
            A list of job details.
        """
        if not self.job_listings:
            logger.warning("No job listings available for scraping")
            return []
            
        # Limit the number of jobs to scrape
        jobs_to_scrape = self.job_listings[:max_jobs]
        
        try:
            logger.info(f"Scraping details for {len(jobs_to_scrape)} jobs")
            job_details = await self.job_details_scraper.scrape_job_details(jobs_to_scrape)
            self.job_details = job_details
            logger.info(f"Scraped details for {len(job_details)} jobs")
            return job_details
        except Exception as e:
            logger.error(f"Error scraping job details: {e}")
            return []
            
    async def filter_jobs(self, 
                   min_match_score: float = 0.7,
                   required_skills: Optional[List[str]] = None,
                   excluded_keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Filter jobs based on matching score with candidate profile and other criteria.
        
        Args:
            min_match_score: Minimum matching score between job and candidate profile.
            required_skills: List of skills that must be included in the job.
            excluded_keywords: Keywords that should not appear in the job description.
            
        Returns:
            A list of filtered job details.
        """
        if not self.job_details:
            logger.warning("No job details available for filtering")
            return []
            
        filtered_jobs = []
        
        for job in self.job_details:
            # Skip jobs without job description
            if "job_description" not in job:
                continue
                
            # Check for excluded keywords
            if excluded_keywords and any(kw.lower() in job["job_description"].lower() for kw in excluded_keywords):
                logger.debug(f"Skipping job {job.get('job_title', 'Unknown')} due to excluded keywords")
                continue
                
            # Check for required skills
            if required_skills:
                job_description = job["job_description"].lower()
                missing_skills = [skill for skill in required_skills 
                                 if skill.lower() not in job_description]
                if missing_skills:
                    logger.debug(f"Skipping job {job.get('job_title', 'Unknown')} due to missing skills: {missing_skills}")
                    continue
                    
            # Calculate match score
            match_score = self._calculate_match_score(job)
            job["match_score"] = match_score
            
            # Filter by match score
            if match_score >= min_match_score:
                filtered_jobs.append(job)
                
        # Sort filtered jobs by match score (descending)
        filtered_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        logger.info(f"Filtered {len(filtered_jobs)} jobs from {len(self.job_details)} job details")
        
        # Save filtered jobs to file
        try:
            with open("../data/filtered_jobs.json", "w") as f:
                json.dump(filtered_jobs, f, indent=2)
            logger.info(f"Saved {len(filtered_jobs)} filtered jobs")
        except Exception as e:
            logger.error(f"Error saving filtered jobs: {e}")
            
        return filtered_jobs
        
    async def generate_and_apply(self, 
                          filtered_jobs: List[Dict[str, Any]],
                          max_applications: int = 5,
                          auto_apply: bool = False) -> int:
        """
        Generate personalized resumes and cover letters for filtered jobs and apply.
        
        Args:
            filtered_jobs: List of filtered job details.
            max_applications: Maximum number of applications to submit.
            auto_apply: Whether to automatically submit applications.
            
        Returns:
            Number of applications submitted.
        """
        if not filtered_jobs:
            logger.warning("No filtered jobs available for application")
            return 0
            
        applications_submitted = 0
        
        # Process each job up to max_applications
        for i, job in enumerate(filtered_jobs):
            if i >= max_applications:
                logger.info(f"Reached maximum number of applications ({max_applications})")
                break
                
            try:
                # Extract job description
                job_description = job.get("job_description", "")
                if not job_description:
                    logger.warning(f"Skipping job {i+1} due to missing job description")
                    continue
                    
                # Extract company information
                company_name = job.get("company", "")
                company_info = f"Company: {company_name}\n"
                
                # Generate personalized resume
                logger.info(f"Generating resume for job {i+1}: {job.get('job_title', 'Unknown')} at {company_name}")
                resume_path, resume_content = self.resume_generator.generate_resume(
                    job_description=job_description,
                    candidate_profile=self.candidate_profile
                )
                
                if not resume_path or not resume_content:
                    logger.warning(f"Failed to generate resume for job {i+1}")
                    continue
                    
                # Generate personalized cover letter
                logger.info(f"Generating cover letter for job {i+1}: {job.get('job_title', 'Unknown')} at {company_name}")
                cover_letter_path, cover_letter_content = self.resume_generator.generate_cover_letter(
                    job_description=job_description,
                    candidate_resume=resume_content,
                    company_info=company_info
                )
                
                if not cover_letter_path or not cover_letter_content:
                    logger.warning(f"Failed to generate cover letter for job {i+1}")
                    continue
                    
                # Track the application
                self.application_tracker.add_application(
                    job_id=job.get("job_id", ""),
                    job_title=job.get("job_title", "Unknown"),
                    company=job.get("company", "Unknown"),
                    source=job.get("source", "unknown"),
                    match_score=job.get("match_score", 0.0),
                    resume_path=resume_path,
                    cover_letter_path=cover_letter_path,
                    notes=f"Auto-applied: {auto_apply}"
                )
                
                # Apply to the job if auto-apply is enabled
                if auto_apply:
                    if "job_id" in job and job["job_id"]:
                        # Apply through LinkedIn
                        logger.info(f"Applying to job {i+1} on LinkedIn")
                        success = await self.linkedin_integration.apply_to_job(
                            job_id=job["job_id"],
                            resume_path=resume_path,
                            cover_letter_path=cover_letter_path
                        )
                        
                        if success:
                            applications_submitted += 1
                            logger.info(f"Successfully applied to job {i+1}")
                            self.application_tracker.update_application_status(
                                job_id=job["job_id"],
                                status="applied",
                                notes="Successfully submitted application"
                            )
                        else:
                            logger.warning(f"Failed to apply to job {i+1}")
                            self.application_tracker.update_application_status(
                                job_id=job["job_id"],
                                status="failed",
                                notes="Failed to submit application"
                            )
                    else:
                        # For non-LinkedIn jobs, just log the output paths
                        logger.info(f"Auto-apply not available for job {i+1} (no LinkedIn job ID)")
                        logger.info(f"Resume: {resume_path}")
                        logger.info(f"Cover Letter: {cover_letter_path}")
                        self.application_tracker.update_application_status(
                            job_id=job.get("job_id", ""),
                            status="pending",
                            notes="Manual application required"
                        )
                else:
                    # Just log the output paths if auto-apply is disabled
                    logger.info(f"Generated application materials for job {i+1}")
                    logger.info(f"Resume: {resume_path}")
                    logger.info(f"Cover Letter: {cover_letter_path}")
                    self.application_tracker.update_application_status(
                        job_id=job.get("job_id", ""),
                        status="pending",
                        notes="Manual application required"
                    )
                    
                # Add a short delay between applications
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing job {i+1}: {e}")
                if "job_id" in job:
                    self.application_tracker.update_application_status(
                        job_id=job["job_id"],
                        status="error",
                        notes=f"Error during application: {str(e)}"
                    )
                
        self.applications_submitted = applications_submitted
        
        # Generate application statistics
        stats = self.application_tracker.get_application_stats()
        logger.info(f"Application Statistics: {json.dumps(stats, indent=2)}")
        
        # Get recommendations for future applications
        recommendations = self.application_tracker.get_recommendations()
        logger.info(f"Recommendations: {json.dumps(recommendations, indent=2)}")
        
        return applications_submitted
        
    def _load_candidate_profile(self) -> bool:
        """
        Load the candidate profile from file or create a default one.
        
        Returns:
            True if loading was successful, False otherwise.
        """
        profile_path = "../data/candidate_profile.json"
        
        try:
            # Check if profile file exists
            if os.path.exists(profile_path):
                with open(profile_path, "r") as f:
                    self.candidate_profile = json.load(f)
                logger.info("Loaded candidate profile from file")
                return True
                
            # If not, create a default profile
            self.candidate_profile = {
                "name": "Your Name",
                "email": "your.email@example.com",
                "phone": "555-123-4567",
                "location": "New York, NY",
                "linkedin": "https://www.linkedin.com/in/yourprofile/",
                "summary": "Experienced professional with a passion for technology.",
                "skills": [
                    "Python", "JavaScript", "SQL", "Data Analysis", 
                    "Machine Learning", "Cloud Computing", "Project Management"
                ],
                "experience": [
                    {
                        "title": "Senior Developer",
                        "company": "Tech Company",
                        "location": "New York, NY",
                        "dates": "January 2020 - Present",
                        "description": "Led development of key features for the company's flagship product."
                    },
                    {
                        "title": "Junior Developer",
                        "company": "Startup Inc.",
                        "location": "New York, NY",
                        "dates": "January 2018 - December 2019",
                        "description": "Assisted in building and maintaining web applications."
                    }
                ],
                "education": [
                    {
                        "degree": "M.S. Computer Science",
                        "institution": "University of Example",
                        "location": "Example City, State",
                        "dates": "2016 - 2018"
                    },
                    {
                        "degree": "B.S. Computer Science",
                        "institution": "Example College",
                        "location": "Example City, State",
                        "dates": "2012 - 2016"
                    }
                ],
                "certifications": [
                    "AWS Certified Developer",
                    "Google Cloud Professional Data Engineer"
                ]
            }
            
            # Save default profile
            with open(profile_path, "w") as f:
                json.dump(self.candidate_profile, f, indent=2)
                
            logger.info("Created default candidate profile (please edit before using)")
            logger.info(f"Profile saved to {profile_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading/creating candidate profile: {e}")
            return False
            
    def _calculate_match_score(self, job: Dict[str, Any]) -> float:
        """
        Calculate a matching score between the job and the candidate profile.
        
        Args:
            job: Job details dictionary.
            
        Returns:
            A matching score between 0 and 1.
        """
        # This is a simple implementation that can be improved
        if not self.candidate_profile or "skills" not in self.candidate_profile:
            return 0.5  # Default score if we can't calculate
            
        try:
            job_description = job.get("job_description", "").lower()
            
            if not job_description:
                return 0.5  # Default score if no job description
                
            # Calculate skills match
            candidate_skills = [skill.lower() for skill in self.candidate_profile["skills"]]
            skills_mentioned = sum(1 for skill in candidate_skills if skill in job_description)
            skills_score = min(skills_mentioned / max(len(candidate_skills), 1), 1.0)
            
            # Calculate experience match
            experience_score = 0.5  # Default experience score
            
            if "experience" in self.candidate_profile:
                # Extract job titles from candidate's experience
                candidate_titles = [exp["title"].lower() for exp in self.candidate_profile["experience"]]
                
                # Check if any of the candidate's job titles are mentioned in the job description
                titles_mentioned = sum(1 for title in candidate_titles if title in job_description)
                experience_score = min(titles_mentioned / max(len(candidate_titles), 1), 1.0)
                
            # Combine scores with weights
            match_score = (0.7 * skills_score) + (0.3 * experience_score)
            
            return match_score
            
        except Exception as e:
            logger.error(f"Error calculating match score: {e}")
            return 0.5  # Default score on error


async def run_job_application_process(args):
    """
    Run the job application process with the specified arguments.
    
    Args:
        args: Command-line arguments.
    """
    # Initialize the automation system
    automation = JobApplicationAutomation()
    
    # Setup
    setup_success = await automation.setup()
    if not setup_success:
        logger.error("Failed to set up job application automation")
        return
        
    # Search for jobs
    job_listings = await automation.search_jobs(
        keywords=args.keywords,
        location=args.location,
        use_linkedin=not args.no_linkedin,
        use_browser=not args.no_browser,
        job_site=args.job_site
    )
    
    if not job_listings:
        logger.error("No job listings found")
        return
        
    # Scrape job details
    job_details = await automation.scrape_job_details(max_jobs=args.max_jobs)
    
    if not job_details:
        logger.error("No job details found")
        return
        
    # Filter jobs
    required_skills = args.required_skills.split(",") if args.required_skills else None
    excluded_keywords = args.excluded_keywords.split(",") if args.excluded_keywords else None
    
    filtered_jobs = await automation.filter_jobs(
        min_match_score=args.min_match_score,
        required_skills=required_skills,
        excluded_keywords=excluded_keywords
    )
    
    if not filtered_jobs:
        logger.error("No jobs passed the filtering criteria")
        return
        
    # Generate resumes/cover letters and apply
    applications = await automation.generate_and_apply(
        filtered_jobs=filtered_jobs,
        max_applications=args.max_applications,
        auto_apply=args.auto_apply
    )
    
    logger.info(f"Job application process completed. Applications submitted: {applications}")


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Automated job application tool")
    
    # Job search parameters
    parser.add_argument("--keywords", type=str, nargs="+", default=["software engineer", "python"],
                      help="Keywords for job search")
    parser.add_argument("--location", type=str, default="Remote",
                      help="Location for job search")
    parser.add_argument("--job-site", type=str, default="linkedin", 
                      choices=["linkedin", "indeed", "glassdoor"],
                      help="Job site to search on with browser automation")
    
    # Component selection
    parser.add_argument("--no-linkedin", action="store_true",
                      help="Disable LinkedIn API search")
    parser.add_argument("--no-browser", action="store_true",
                      help="Disable browser automation search")
    
    # Job filtering parameters
    parser.add_argument("--max-jobs", type=int, default=10,
                      help="Maximum number of jobs to scrape details for")
    parser.add_argument("--min-match-score", type=float, default=0.7,
                      help="Minimum match score (0-1) for job filtering")
    parser.add_argument("--required-skills", type=str,
                      help="Comma-separated list of required skills")
    parser.add_argument("--excluded-keywords", type=str,
                      help="Comma-separated list of keywords to exclude")
    
    # Application parameters
    parser.add_argument("--max-applications", type=int, default=5,
                      help="Maximum number of applications to submit")
    parser.add_argument("--auto-apply", action="store_true",
                      help="Enable automatic application submission")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    asyncio.run(run_job_application_process(args))