"""
Web scraping module using Crawl4AI for job details extraction.
This module provides functionality to scrape job details from job listings.
"""

import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Union

# Import Crawl4AI
from crawl4ai.api import Crawler
from crawl4ai.dispatcher import MemoryAdaptiveDispatcher
from crawl4ai.strategies import BestFirstCrawlerStrategy, BFSCrawlerStrategy, DFSCrawlerStrategy
from crawl4ai.extractors import ContentExtractor

# Import configuration
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.crawl4ai_config import Crawl4AIConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../data/web_scraping.log"),
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
        self._setup_crawler()
        
    def _setup_crawler(self) -> None:
        """Set up the crawler using the configuration settings."""
        # Set up the crawler strategy based on configuration
        if self.config.crawling_strategy == "bestfirst":
            self.strategy = BestFirstCrawlerStrategy(
                content_relevance_keywords=self.config.content_relevance_keywords
            )
        elif self.config.crawling_strategy == "bfs":
            self.strategy = BFSCrawlerStrategy()
        elif self.config.crawling_strategy == "dfs":
            self.strategy = DFSCrawlerStrategy()
        else:
            self.strategy = BestFirstCrawlerStrategy(
                content_relevance_keywords=self.config.content_relevance_keywords
            )
        
        # Create a memory-adaptive dispatcher if enabled
        if self.config.memory_adaptive_dispatcher:
            self.dispatcher = MemoryAdaptiveDispatcher(
                max_memory_percent=self.config.max_memory_percent
            )
        else:
            self.dispatcher = None
            
        # Create the content extractor
        self.content_extractor = ContentExtractor()
        
        logger.info(f"Crawler initialized with {self.config.crawling_strategy} strategy")
        
    async def scrape_job_details(self, job_listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scrape job details from the provided job listings.
        
        Args:
            job_listings: List of job listings to scrape details from.
                         Each listing should have a 'url' field.
                         
        Returns:
            A list of job details, each represented as a dictionary.
        """
        if not job_listings:
            logger.warning("No job listings provided for scraping")
            return []
            
        job_details = []
        
        # Create a crawler instance
        crawler = Crawler(
            strategy=self.strategy,
            dispatcher=self.dispatcher,
            rate_limit=self.config.rate_limit,
            respect_robots_txt=self.config.respect_robots_txt,
            timeout=self.config.request_timeout
        )
        
        # Extract URLs from job listings
        urls = [listing.get("url") for listing in job_listings if listing.get("url")]
        
        if not urls:
            logger.warning("No valid URLs found in job listings")
            return []
            
        logger.info(f"Starting to scrape {len(urls)} job listings")
        
        # Process each URL and extract job details
        for i, url in enumerate(urls):
            if i >= self.config.max_pages:
                logger.info(f"Reached maximum number of pages ({self.config.max_pages})")
                break
                
            try:
                # Crawl the job listing URL
                result = await crawler.crawl(
                    url,
                    max_depth=self.config.max_depth if self.config.deep_crawling_enabled else 1
                )
                
                # Extract job details from the crawled content
                job_detail = await self._extract_job_details(result, job_listings[i])
                
                if job_detail:
                    job_details.append(job_detail)
                    logger.info(f"Successfully scraped job details from {url}")
                else:
                    logger.warning(f"Failed to extract job details from {url}")
                    
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                
        # Save job details to a file
        self._save_job_details(job_details)
        
        return job_details
        
    async def _extract_job_details(self, 
                             crawl_result: Dict[str, Any], 
                             job_listing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract job details from the crawled content.
        
        Args:
            crawl_result: Result of crawling a job listing URL.
            job_listing: Original job listing dictionary.
            
        Returns:
            A dictionary containing detailed job information.
        """
        if not crawl_result or "content" not in crawl_result:
            logger.warning(f"No content found in crawl result for {job_listing.get('url', 'unknown URL')}")
            return {}
            
        # Start with the basic job information from the listing
        job_detail = {
            "job_title": job_listing.get("job_title", ""),
            "company": job_listing.get("company", ""),
            "location": job_listing.get("location", ""),
            "url": job_listing.get("url", ""),
            "posted_date": job_listing.get("posted_date", ""),
        }
        
        content = crawl_result["content"]
        
        # Use the content extractor to extract structured information
        extracted_data = await self.content_extractor.extract(content)
        
        # Extract job description
        if self.config.extract_job_description and "main_content" in extracted_data:
            job_detail["job_description"] = extracted_data["main_content"]
            
        # Extract qualifications
        if self.config.extract_qualifications:
            qualifications = await self._extract_qualifications(content)
            if qualifications:
                job_detail["qualifications"] = qualifications
                
        # Extract responsibilities
        if self.config.extract_responsibilities:
            responsibilities = await self._extract_responsibilities(content)
            if responsibilities:
                job_detail["responsibilities"] = responsibilities
                
        # Extract salary information
        if self.config.extract_salary and "salary" not in job_detail:
            salary = await self._extract_salary(content)
            if salary:
                job_detail["salary"] = salary
                
        # Extract application URL if different from listing URL
        if self.config.extract_application_url:
            application_url = await self._extract_application_url(content, job_listing.get("url", ""))
            if application_url and application_url != job_listing.get("url", ""):
                job_detail["application_url"] = application_url
                
        # Extract job type
        if self.config.extract_job_type:
            job_type = await self._extract_job_type(content)
            if job_type:
                job_detail["job_type"] = job_type
                
        return job_detail
        
    async def _extract_qualifications(self, content: str) -> List[str]:
        """
        Extract job qualifications from the content.
        
        Args:
            content: HTML content of the job posting.
            
        Returns:
            A list of qualifications.
        """
        qualifications = []
        
        # Use Crawl4AI's content extractor with custom parameters
        try:
            # Look for sections with keywords related to qualifications
            sections = await self.content_extractor.extract_sections(
                content,
                ["qualifications", "requirements", "skills", "what you'll need", "what we're looking for"]
            )
            
            for section in sections:
                if "items" in section and section["items"]:
                    qualifications.extend(section["items"])
                elif "content" in section and section["content"]:
                    # If no list items found, use the paragraph text
                    qualifications.append(section["content"])
                    
        except Exception as e:
            logger.error(f"Error extracting qualifications: {e}")
            
        return qualifications
        
    async def _extract_responsibilities(self, content: str) -> List[str]:
        """
        Extract job responsibilities from the content.
        
        Args:
            content: HTML content of the job posting.
            
        Returns:
            A list of responsibilities.
        """
        responsibilities = []
        
        # Use Crawl4AI's content extractor with custom parameters
        try:
            # Look for sections with keywords related to responsibilities
            sections = await self.content_extractor.extract_sections(
                content,
                ["responsibilities", "duties", "what you'll do", "job description", "the role"]
            )
            
            for section in sections:
                if "items" in section and section["items"]:
                    responsibilities.extend(section["items"])
                elif "content" in section and section["content"]:
                    # If no list items found, use the paragraph text
                    responsibilities.append(section["content"])
                    
        except Exception as e:
            logger.error(f"Error extracting responsibilities: {e}")
            
        return responsibilities
        
    async def _extract_salary(self, content: str) -> str:
        """
        Extract salary information from the content.
        
        Args:
            content: HTML content of the job posting.
            
        Returns:
            A string representing salary information.
        """
        try:
            # Use Crawl4AI's content extractor to find salary information
            salary_patterns = [
                r'\$\d+,\d+(?:\s*-\s*\$\d+,\d+)?(?:\s*(?:per|\/)\s*(?:year|yr|annual|annually))?',
                r'\d+k(?:\s*-\s*\d+k)?(?:\s*(?:per|\/)\s*(?:year|yr|annual|annually))?'
            ]
            
            salary_info = await self.content_extractor.extract_pattern(content, salary_patterns)
            
            if salary_info:
                return salary_info[0]  # Return the first match
                
        except Exception as e:
            logger.error(f"Error extracting salary: {e}")
            
        return ""
        
    async def _extract_application_url(self, content: str, listing_url: str) -> str:
        """
        Extract application URL from the content.
        
        Args:
            content: HTML content of the job posting.
            listing_url: URL of the job listing.
            
        Returns:
            Application URL if found, empty string otherwise.
        """
        try:
            # Use Crawl4AI's content extractor to find application links
            application_link_patterns = [
                r'href=[\'"]([^\'"]+(?:apply|application|submit)[^\'"]*)[\'"]',
                r'href=[\'"]([^\'"]+(?:job|career|position)[^\'"]*)[\'"]'
            ]
            
            links = await self.content_extractor.extract_links(content, application_link_patterns)
            
            if links:
                # Return the first link that looks like an application link
                for link in links:
                    if "apply" in link.lower() or "application" in link.lower() or "submit" in link.lower():
                        return link
                        
        except Exception as e:
            logger.error(f"Error extracting application URL: {e}")
            
        return ""
        
    async def _extract_job_type(self, content: str) -> str:
        """
        Extract job type from the content.
        
        Args:
            content: HTML content of the job posting.
            
        Returns:
            Job type if found, empty string otherwise.
        """
        job_types = [
            "full-time", "full time",
            "part-time", "part time",
            "contract", "freelance",
            "temporary", "internship",
            "remote", "hybrid", "on-site", "on site"
        ]
        
        try:
            # Convert content to lowercase for case-insensitive matching
            content_lower = content.lower()
            
            # Check each job type
            for job_type in job_types:
                if job_type in content_lower:
                    # Capitalize the first letter of each word
                    return " ".join(word.capitalize() for word in job_type.split())
                    
        except Exception as e:
            logger.error(f"Error extracting job type: {e}")
            
        return ""
    
    def _save_job_details(self, job_details: List[Dict[str, Any]]) -> None:
        """
        Save job details to a JSON file.
        
        Args:
            job_details: List of job details to save.
        """
        try:
            with open(self.config.scraped_job_details_file, "w") as f:
                json.dump(job_details, f, indent=2)
            logger.info(f"Saved {len(job_details)} job details to {self.config.scraped_job_details_file}")
        except Exception as e:
            logger.error(f"Error saving job details: {e}")


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