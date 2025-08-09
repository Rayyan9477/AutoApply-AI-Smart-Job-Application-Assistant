"""
Command-line argument parsing for job application automation.
"""

import argparse
from typing import Any


def parse_arguments() -> Any:
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
    parser.add_argument("--min-ats-score", type=float, default=0.7,
                      help="Minimum ATS score (0-1) required for application")
    parser.add_argument("--auto-optimize-resume", action="store_true",
                      help="Automatically optimize resumes that don't meet ATS threshold")
    
    # Debug and demonstration options
    parser.add_argument("--demo-mode", action="store_true",
                      help="Run in demonstration mode with sample data when no results are found")
    parser.add_argument("--create-samples", action="store_true",
                      help="Create sample job listings if none are found")
    
    return parser.parse_args()
