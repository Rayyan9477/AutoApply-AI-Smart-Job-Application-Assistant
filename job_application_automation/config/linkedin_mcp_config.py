"""
Configuration settings for LinkedIn API integration and MCP functionality.
"""
import os
from pydantic import BaseModel, SecretStr, HttpUrl
from typing import Optional, Dict, List, Literal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LinkedInMCPConfig(BaseModel):
    """Configuration settings for LinkedIn API and Model Context Protocol."""
    
    # API Authentication
    client_id: str = os.getenv("LINKEDIN_CLIENT_ID", "")
    client_secret: str = os.getenv("LINKEDIN_CLIENT_SECRET", "")
    redirect_uri: str = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/callback")
    
    # API Endpoints
    auth_url: str = "https://www.linkedin.com/oauth/v2/authorization"
    token_url: str = "https://www.linkedin.com/oauth/v2/accessToken"
    job_search_url: str = "https://api.linkedin.com/v2/jobSearch"
    profile_url: str = "https://api.linkedin.com/v2/me"
    
    # OAuth Scopes
    scopes: List[str] = [
        "r_liteprofile",
        "r_emailaddress",
        "w_member_social",
        "r_organization_social",
        "rw_organization_admin",
        "w_organization_social"
    ]
    
    # API Rate Limiting
    max_requests_per_min: int = 50
    retry_delay: int = 60
    max_retries: int = 3
    
    # Job Search Settings
    search_params: Dict[str, any] = {
        "keywords": [],
        "location": "",
        "distance": 25,  # miles
        "experience_levels": ["ENTRY_LEVEL", "ASSOCIATE", "MID_SENIOR"],
        "job_types": ["FULL_TIME", "CONTRACT", "PART_TIME"],
        "remote": True,
        "sort_by": "RELEVANT",
        "limit": 25
    }
    
    # MCP Integration
    mcp_enabled: bool = True
    mcp_model_path: str = "../models/linkedin_mcp"
    mcp_batch_size: int = 10
    use_cached_responses: bool = True
    cache_ttl: int = 3600  # seconds
    
    # Resume Enhancement
    enhance_resume: bool = True
    keyword_extraction: bool = True
    skill_matching: bool = True
    experience_matching: bool = True
    
    # Job Application Settings
    auto_apply_enabled: bool = False  # Disabled by default for safety
    max_daily_applications: int = 50
    application_delay: int = 5  # seconds between applications
    save_failed_attempts: bool = True
    
    # AI Integration
    ai_settings: Dict[str, any] = {
        "model": "gpt-4",  # or any other supported model
        "temperature": 0.7,
        "max_tokens": 1000,
        "resume_prompt_template": """
        Analyze this job description and optimize the resume:
        Job Description: {job_description}
        Current Resume: {current_resume}
        Key Requirements: {requirements}
        """,
        "cover_letter_prompt_template": """
        Generate a personalized cover letter:
        Job Description: {job_description}
        Company Info: {company_info}
        Candidate Profile: {candidate_profile}
        Key Achievements: {achievements}
        """
    }
    
    # Monitoring and Analytics
    enable_analytics: bool = True
    analytics_settings: Dict[str, any] = {
        "track_success_rate": True,
        "track_response_times": True,
        "track_error_rates": True,
        "store_application_history": True
    }
    
    @classmethod
    def from_env(cls) -> "LinkedInMCPConfig":
        """Create config from environment variables."""
        return cls(
            client_id=os.getenv("LINKEDIN_CLIENT_ID", ""),
            client_secret=os.getenv("LINKEDIN_CLIENT_SECRET", ""),
            redirect_uri=os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/callback"),
            mcp_enabled=os.getenv("LINKEDIN_MCP_ENABLED", "True").lower() == "true",
            auto_apply_enabled=os.getenv("LINKEDIN_AUTO_APPLY", "False").lower() == "true"
        )