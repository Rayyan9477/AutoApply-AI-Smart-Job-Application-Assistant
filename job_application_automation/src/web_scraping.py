"""
Web scraping module using Crawl4AI for job details extraction.
This module provides functionality to scrape job details from job listings.
"""

import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union

# Import HTTPX and BeautifulSoup
import httpx
from bs4 import BeautifulSoup

# Import configuration
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.crawl4ai_config import Crawl4AIConfig

# Set up logging with absolute path for the log file
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_file_path = os.path.join(project_root, "data", "web_scraping.log")

# Ensure log directory exists
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class JobDetailsScraper:
    """
    Class for scraping job details using Crawl4AI.
    This class provides methods to scrape job details from job listings.
    """

    def __init__(self, config: Optional[Crawl4AIConfig] = None):
        """
        Initialize the JobDetailsScraper with configuration settings.
        
        Args:
            config: Configuration settings for web scraping.
                   If None, default settings will be used.
        """
        self.config = config or Crawl4AIConfig()
        
    async def scrape_job_details(self, job_listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scrape job descriptions using HTTPX and BeautifulSoup.
        """
        if not job_listings:
            logger.warning("No job listings provided for scraping")
            return []
        job_details = []
        async with httpx.AsyncClient() as client:
            for listing in job_listings:
                url = listing.get("url")
                if not url:
                    continue
                try:
                    resp = await client.get(url, timeout=self.config.request_timeout)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, 'lxml')
                    text = ' '.join(p.get_text(separator=' ', strip=True) for p in soup.find_all('p'))
                    detail = {**listing, "job_description": text}
                    job_details.append(detail)
                    logger.info(f"Scraped job description from {url}")
                except Exception as e:
                    logger.error(f"Error scraping {url}: {e}")
        return job_details


# Example usage
async def main():
    # Load job listings from a file
    try:
        with open("../data/job_listings.json", "r") as f:
            job_listings = json.load(f)
    except Exception as e:
        logger.error(f"Error loading job listings: {e}")
        job_listings = []
    
    if job_listings:
        job_details_scraper = JobDetailsScraper()
        job_details = await job_details_scraper.scrape_job_details(job_listings)
        print(f"Scraped details for {len(job_details)} jobs")
    else:
        print("No job listings found to scrape")


if __name__ == "__main__":
    asyncio.run(main())