"""
Configuration settings for browser automation using browser-use.
"""
import os
from pydantic import BaseModel
from typing import Optional, Dict, List, Union
from dotenv import load_dotenv
import browser_use

# Load environment variables
load_dotenv()


class BrowserConfig(BaseModel):
    """
    Configuration settings for browser automation using browser-use.
    """
    # Browser settings
    browser_type: str = "chromium"  # Options: chromium, firefox, webkit
    headless: bool = False  # Set to True for production, False for debugging
    slow_mo: int = 100  # Slow down browser automation for debugging (milliseconds)
    
    # User profiles for browser sessions
    user_profile_path: Optional[str] = None
    
    # Proxy settings
    proxy: Optional[Dict[str, str]] = None
    
    # API keys and authentication
    browser_use_api_key: str = os.getenv("BROWSER_USE_API_KEY", "")
    
    # Default timeout settings - increased to prevent timeouts with slow websites
    default_navigation_timeout: int = 60000  # milliseconds (60 seconds)
    default_timeout: int = 60000  # milliseconds (60 seconds)
    page_load_timeout: int = 90000  # milliseconds (90 seconds)
    
    # User agent settings
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # WebGL vendor
    webgl_vendor: str = "Google Inc. (NVIDIA)"
    
    # Platform
    platform: str = "Win32"
    
    # Stealth mode
    stealth_mode: bool = True  # Enable anti-detection measures
    
    # Screenshot and recording settings
    screenshots_dir: str = "../data/screenshots"
    videos_dir: str = "../data/videos"
    record_video: bool = False
    
    # Job search settings
    search_keywords: List[str] = ["software engineer", "data scientist", "machine learning engineer"]
    search_locations: List[str] = ["remote", "united states", "new york"]
    experience_levels: List[str] = ["entry", "mid", "senior"]
    
    # Job search sites
    job_sites: Dict[str, str] = {
        "linkedin": "https://www.linkedin.com/jobs/",
        "indeed": "https://www.indeed.com/",
        "glassdoor": "https://www.glassdoor.com/Job/",
    }
    
    # Browser session settings
    cookies_dir: str = "../data/cookies"
    
    # LinkedIn Easy Apply settings
    firefox_profile_path: Optional[str] = None
    easy_apply_enabled: bool = True
    answer_questions: bool = True
    max_questions_to_answer: int = 20
    question_timeout: int = 30
    
    # Enhanced browser settings 
    random_delays: bool = True
    min_delay: float = 1.0
    max_delay: float = 3.0
    
    # Default answers for common questions
    default_answers: Dict[str, str] = {
        "years_of_experience": "5",
        "expected_salary": "Competitive / Market Rate",
        "notice_period": "2 weeks",
        "willing_to_relocate": "Yes",
        "authorized_to_work": "Yes",
        "require_sponsorship": "No",
        "work_remotely": "Yes",
        "start_date": "2 weeks",
        "linkedin_profile": "",  # Will be filled from candidate profile
        "website": "",  # Will be filled from candidate profile
        "github": ""  # Will be filled from candidate profile
    }
    
    @classmethod
    def from_env(cls) -> "BrowserConfig":
        """
        Create a BrowserConfig instance from environment variables.
        """
        return cls(
            browser_type=os.getenv("BROWSER_TYPE", "chromium"),
            headless=os.getenv("BROWSER_HEADLESS", "False").lower() == "true",
            browser_use_api_key=os.getenv("BROWSER_USE_API_KEY", ""),
            user_profile_path=os.getenv("BROWSER_USER_PROFILE", None),
            default_navigation_timeout=int(os.getenv("BROWSER_NAVIGATION_TIMEOUT", "30000")),
            default_timeout=int(os.getenv("BROWSER_TIMEOUT", "30000")),
            stealth_mode=os.getenv("STEALTH_MODE", "True").lower() == "true",
            user_agent=os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
            webgl_vendor=os.getenv("WEBGL_VENDOR", "Google Inc. (NVIDIA)"),
            platform=os.getenv("PLATFORM", "Win32"),
        )