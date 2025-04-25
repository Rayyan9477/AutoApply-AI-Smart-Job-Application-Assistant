"""
Configuration settings for browser automation using browser-use.
"""
import os
from pydantic import BaseModel
from typing import Optional, Dict, List, Union, Literal
from dotenv import load_dotenv
import browser_use

# Load environment variables
load_dotenv()


class BrowserConfig(BaseModel):
    """Configuration for browser automation."""
    
    # Browser settings
    browser_type: Literal["chromium", "firefox", "webkit"] = "chromium"
    headless: bool = True  # Set to False for manual login when needed
    slow_mo: int = 50  # Milliseconds between actions
    
    # API settings
    browser_use_api_key: Optional[str] = None
    
    # Paths
    screenshots_dir: str = "../data/screenshots"
    videos_dir: str = "../data/videos"
    cookies_dir: str = "../data/cookies"
    
    # Session handling
    save_cookies: bool = True
    cookie_expiry_days: int = 30  # How long to consider cookies valid
    
    # LinkedIn specific settings
    linkedin_cookies_file: str = "../data/sessions/linkedin_cookies.json"
    linkedin_auth_required: bool = True  # Whether LinkedIn login is required
    linkedin_manual_login: bool = False  # Whether to use manual login flow
    
    # Timeouts
    default_timeout: int = 30000  # 30 seconds
    default_navigation_timeout: int = 60000  # 60 seconds
    page_load_timeout: int = 60000  # 60 seconds
    
    # Search settings
    job_sites: Dict[str, str] = {
        "linkedin": "https://www.linkedin.com/jobs/",
        "indeed": "https://www.indeed.com/",
        "glassdoor": "https://www.glassdoor.com/Job/index.htm"
    }
    search_keywords: List[str] = ["python", "software engineer"]
    search_locations: List[str] = ["Remote", "New York"]
    
    # Application settings
    answer_questions: bool = True
    max_questions_to_answer: int = 20
    random_delays: bool = True
    min_delay: float = 0.5
    max_delay: float = 2.0
    stealth_mode: bool = False  # If True, don't actually submit applications
    
    # Default phone number to use in applications
    default_phone_number: Optional[str] = None
    
    # Rate limiting for application submission
    rate_limit_applications: int = 5  # Max applications per hour
    max_applications_per_day: int = 20  # Max applications per day
    min_application_delay: int = 5  # Minimum seconds between applications
    max_application_delay: int = 15  # Maximum seconds between applications
    
    @classmethod
    def from_env(cls) -> "BrowserConfig":
        """Create configuration from environment variables."""
        return cls(
            browser_type=os.getenv("BROWSER_TYPE", "chromium"),
            headless=os.getenv("BROWSER_HEADLESS", "True").lower() == "true",
            browser_use_api_key=os.getenv("BROWSER_USE_API_KEY"),
            default_phone_number=os.getenv("DEFAULT_PHONE_NUMBER"),
            stealth_mode=os.getenv("STEALTH_MODE", "False").lower() == "true"
        )