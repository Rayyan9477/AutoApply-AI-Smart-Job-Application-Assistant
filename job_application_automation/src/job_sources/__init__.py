"""
Job sources package for AutoApply AI.

This package provides integrations with various job boards and platforms.
"""

from .base import JobListing, JobSourceBase
from .indeed_integration import IndeedIntegration
from .glassdoor_integration import GlassdoorIntegration
from .job_search_manager import JobSearchManager

__all__ = [
    'JobListing',
    'JobSourceBase',
    'IndeedIntegration',
    'GlassdoorIntegration',
    'JobSearchManager',
] 