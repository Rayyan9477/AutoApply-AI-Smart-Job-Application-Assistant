"""
Browser automation module using browser-use for job searching.
This module provides functionality to automate browser interactions
for searching job postings on various job search websites.
"""

import os
import time
import json
import logging
import random
from typing import List, Dict, Optional, Any, Union

# Import browser-use
from browser_use import Agent, Browser, Page, ElementHandle

# ...existing code...

# Import configuration
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.browser_config import BrowserConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../data/browser_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class JobSearchBrowser:
    """
    Class for automating job searches using browser-use.
    This class provides methods to search for jobs on various job search websites
    and extract job listings.
    """

    def __init__(self, config: Optional[BrowserConfig] = None):
        """
        Initialize the JobSearchBrowser with configuration settings.
        
        Args:
            config: Configuration settings for browser automation.
                   If None, default settings will be used.
        """
        self.config = config or BrowserConfig()
        self._setup_browser()
        self.agent = None
        
    def _setup_browser(self) -> None:
        """Set up the browser using the configuration settings."""
        os.environ["BROWSER_USE_API_KEY"] = self.config.browser_use_api_key
        
        # Ensure directories exist
        os.makedirs(self.config.screenshots_dir, exist_ok=True)
        os.makedirs(self.config.videos_dir, exist_ok=True)
        os.makedirs(self.config.cookies_dir, exist_ok=True)
        
        # Initialize Agent for browser-use
        self.agent = Agent()
        logger.info(f"Browser initialized with {self.config.browser_type}")
        
    async def search_for_jobs(self, 
                        keywords: Optional[List[str]] = None, 
                        location: Optional[str] = None, 
                        job_site: str = "linkedin") -> List[Dict[str, Any]]:
        """
        Search for jobs using the specified keywords, location, and job site.
        
        Args:
            keywords: List of job keywords to search for (e.g., "software engineer").
            location: Location to search for jobs (e.g., "New York").
            job_site: Job search website to use (default: "linkedin").
                      Options: "linkedin", "indeed", "glassdoor".
                      
        Returns:
            A list of job listings, each represented as a dictionary.
        """
        keywords = keywords or self.config.search_keywords
        location = location or self.config.search_locations[0]
        
        # Get the URL for the specified job site
        job_site_url = self.config.job_sites.get(job_site.lower())
        if not job_site_url:
            logger.error(f"Unsupported job site: {job_site}")
            return []
        
        # Construct the search query
        search_keywords = " ".join(keywords)
        
        try:
            # Navigate to the job search website
            browser = await Browser.create(
                headless=self.config.headless,
                slow_mo=self.config.slow_mo
            )
            
            # Open a new page
            page = await browser.new_page()
            
            # Navigate to the job search website
            await page.goto(job_site_url)
            logger.info(f"Navigated to {job_site_url}")
            
            # Execute job site-specific search logic
            job_listings = await self._execute_job_site_search(
                page, job_site, search_keywords, location
            )
            
            # Close the browser
            await browser.close()
            
            # Save job listings to a file
            self._save_job_listings(job_listings)
            
            return job_listings
            
        except Exception as e:
            logger.error(f"Error during job search: {e}")
            return []
            
    async def _execute_job_site_search(self, 
                                 page: Page, 
                                 job_site: str, 
                                 keywords: str, 
                                 location: str) -> List[Dict[str, Any]]:
        """
        Execute job search on a specific job site.
        
        Args:
            page: The browser page.
            job_site: The job site to search on.
            keywords: Keywords to search for.
            location: Location to search in.
            
        Returns:
            A list of job listings.
        """
        if job_site.lower() == "linkedin":
            return await self._search_linkedin(page, keywords, location)
        elif job_site.lower() == "indeed":
            return await self._search_indeed(page, keywords, location)
        elif job_site.lower() == "glassdoor":
            return await self._search_glassdoor(page, keywords, location)
        else:
            logger.warning(f"No search implementation for job site: {job_site}")
            return []
            
    async def _search_linkedin(self, 
                         page: Page, 
                         keywords: str, 
                         location: str) -> List[Dict[str, Any]]:
        """
        Search for jobs on LinkedIn.
        
        Args:
            page: The browser page.
            keywords: Keywords to search for.
            location: Location to search in.
            
        Returns:
            A list of job listings.
        """
        try:
            # Use browser-use Agent for high-level interactions
            results = await self.agent.run(
                f"""
                1. Find the search fields on the LinkedIn Jobs page
                2. Enter "{keywords}" in the job title field
                3. Enter "{location}" in the location field
                4. Click the search button
                5. Wait for the search results to load
                6. Extract the following information for each job listing (up to 10):
                   - Job title
                   - Company name
                   - Location
                   - Job posting URL
                   - Posted date (if available)
                7. Return the extracted information as a list of job listings
                """,
                page=page
            )
            
            # Process the agent's results
            job_listings = []
            if isinstance(results, str):
                # Parse the agent's response to extract job listings
                # This is a simplified approach; in a real implementation,
                # you might use more structured data from the agent
                lines = results.strip().split("\n")
                current_job = {}
                
                for line in lines:
                    if line.startswith("Job title:"):
                        if current_job:
                            job_listings.append(current_job)
                            current_job = {}
                        current_job["job_title"] = line.replace("Job title:", "").strip()
                    elif line.startswith("Company:"):
                        current_job["company"] = line.replace("Company:", "").strip()
                    elif line.startswith("Location:"):
                        current_job["location"] = line.replace("Location:", "").strip()
                    elif line.startswith("URL:"):
                        current_job["url"] = line.replace("URL:", "").strip()
                    elif line.startswith("Posted:"):
                        current_job["posted_date"] = line.replace("Posted:", "").strip()
                
                if current_job:
                    job_listings.append(current_job)
            
            # Log the number of job listings found
            logger.info(f"Found {len(job_listings)} job listings on LinkedIn")
            return job_listings
            
        except Exception as e:
            logger.error(f"Error searching LinkedIn: {e}")
            return []
            
    async def _search_indeed(self, 
                       page: Page, 
                       keywords: str, 
                       location: str) -> List[Dict[str, Any]]:
        """
        Search for jobs on Indeed.
        
        Args:
            page: The browser page.
            keywords: Keywords to search for.
            location: Location to search in.
            
        Returns:
            A list of job listings.
        """
        try:
            # Use browser-use Agent for high-level interactions
            results = await self.agent.run(
                f"""
                1. Find the search fields on the Indeed Jobs page
                2. Enter "{keywords}" in the what field
                3. Enter "{location}" in the where field
                4. Click the search button
                5. Wait for the search results to load
                6. Extract the following information for each job listing (up to 10):
                   - Job title
                   - Company name
                   - Location
                   - Job posting URL
                   - Posted date (if available)
                   - Salary information (if available)
                7. Return the extracted information as a list of job listings
                """,
                page=page
            )
            
            # Process the agent's results (similar to LinkedIn)
            # This is a simplified approach; adjust based on the agent's actual response format
            job_listings = []
            if isinstance(results, str):
                # Parse the agent's response to extract job listings
                lines = results.strip().split("\n")
                current_job = {}
                
                for line in lines:
                    if line.startswith("Job title:"):
                        if current_job:
                            job_listings.append(current_job)
                            current_job = {}
                        current_job["job_title"] = line.replace("Job title:", "").strip()
                    elif line.startswith("Company:"):
                        current_job["company"] = line.replace("Company:", "").strip()
                    elif line.startswith("Location:"):
                        current_job["location"] = line.replace("Location:", "").strip()
                    elif line.startswith("URL:"):
                        current_job["url"] = line.replace("URL:", "").strip()
                    elif line.startswith("Posted:"):
                        current_job["posted_date"] = line.replace("Posted:", "").strip()
                    elif line.startswith("Salary:"):
                        current_job["salary"] = line.replace("Salary:", "").strip()
                
                if current_job:
                    job_listings.append(current_job)
            
            # Log the number of job listings found
            logger.info(f"Found {len(job_listings)} job listings on Indeed")
            return job_listings
            
        except Exception as e:
            logger.error(f"Error searching Indeed: {e}")
            return []
        
    async def _search_glassdoor(self, 
                          page: Page, 
                          keywords: str, 
                          location: str) -> List[Dict[str, Any]]:
        """
        Search for jobs on Glassdoor.
        
        Args:
            page: The browser page.
            keywords: Keywords to search for.
            location: Location to search in.
            
        Returns:
            A list of job listings.
        """
        try:
            # Use browser-use Agent for high-level interactions
            results = await self.agent.run(
                f"""
                1. Find the search fields on the Glassdoor Jobs page
                2. Enter "{keywords}" in the job title field
                3. Enter "{location}" in the location field
                4. Click the search button
                5. Wait for the search results to load
                6. Handle any login/signup popups (close them if possible)
                7. Extract the following information for each job listing (up to 10):
                   - Job title
                   - Company name
                   - Location
                   - Job posting URL
                   - Posted date (if available)
                   - Salary information (if available)
                   - Company rating (if available)
                8. Return the extracted information as a list of job listings
                """,
                page=page
            )
            
            # Process the agent's results (similar to LinkedIn and Indeed)
            job_listings = []
            if isinstance(results, str):
                # Parse the agent's response to extract job listings
                lines = results.strip().split("\n")
                current_job = {}
                
                for line in lines:
                    if line.startswith("Job title:"):
                        if current_job:
                            job_listings.append(current_job)
                            current_job = {}
                        current_job["job_title"] = line.replace("Job title:", "").strip()
                    elif line.startswith("Company:"):
                        current_job["company"] = line.replace("Company:", "").strip()
                    elif line.startswith("Location:"):
                        current_job["location"] = line.replace("Location:", "").strip()
                    elif line.startswith("URL:"):
                        current_job["url"] = line.replace("URL:", "").strip()
                    elif line.startswith("Posted:"):
                        current_job["posted_date"] = line.replace("Posted:", "").strip()
                    elif line.startswith("Salary:"):
                        current_job["salary"] = line.replace("Salary:", "").strip()
                    elif line.startswith("Rating:"):
                        current_job["rating"] = line.replace("Rating:", "").strip()
                
                if current_job:
                    job_listings.append(current_job)
            
            # Log the number of job listings found
            logger.info(f"Found {len(job_listings)} job listings on Glassdoor")
            return job_listings
            
        except Exception as e:
            logger.error(f"Error searching Glassdoor: {e}")
            return []
        
    def _save_job_listings(self, job_listings: List[Dict[str, Any]]) -> None:
        """
        Save job listings to a JSON file.
        
        Args:
            job_listings: List of job listings to save.
        """
        try:
            with open(self.config.job_sites["job_listings_file"], "w") as f:
                json.dump(job_listings, f, indent=2)
            logger.info(f"Saved {len(job_listings)} job listings to {self.config.job_sites['job_listings_file']}")
        except Exception as e:
            logger.error(f"Error saving job listings: {e}")

    async def take_screenshot(self, page: Page, filename: str) -> None:
        """
        Take a screenshot of the current page.
        
        Args:
            page: The browser page.
            filename: Name of the screenshot file.
        """
        screenshot_path = os.path.join(self.config.screenshots_dir, filename)
        await page.screenshot(path=screenshot_path)
        logger.info(f"Screenshot saved to {screenshot_path}")

    async def easy_apply_linkedin(self, job_id: str, resume_path: str, cover_letter_path: Optional[str] = None) -> bool:
        """Apply to a LinkedIn job using Easy Apply."""
        try:
            browser = await Browser.create(
                headless=self.config.headless,
                slow_mo=self.config.slow_mo,
                firefox_profile=self.config.firefox_profile_path
            )
            
            page = await browser.new_page()
            
            # Navigate to job page
            job_url = f"https://www.linkedin.com/jobs/view/{job_id}"
            await page.goto(job_url)
            logger.info(f"Navigated to job {job_id}")
            
            # Find and click Easy Apply button
            apply_button = await page.query_selector("button[data-control-name='jobdetails_topcard_inapply']")
            if not apply_button:
                logger.warning("Easy Apply button not found")
                return False
                
            await apply_button.click()
            logger.info("Clicked Easy Apply button")
            
            # Upload resume if requested
            if resume_path:
                await self._upload_resume(page, resume_path)
            
            # Upload cover letter if provided
            if cover_letter_path:
                await self._upload_cover_letter(page, cover_letter_path)
            
            # Handle additional questions if enabled
            if self.config.answer_questions:
                await self._handle_application_questions(page)
            
            # Submit application
            submit_button = await page.query_selector("button[aria-label='Submit application']")
            if submit_button:
                if not self.config.stealth_mode:
                    await submit_button.click()
                    logger.info("Submitted application")
                    return True
                else:
                    logger.info("Stealth mode enabled - application ready for manual review")
                    await self.take_screenshot(page, f"application_{job_id}.png")
                    return True
            
            logger.warning("Submit button not found")
            return False
            
        except Exception as e:
            logger.error(f"Error during Easy Apply: {e}")
            return False
            
        finally:
            if browser:
                await browser.close()
                
    async def _upload_resume(self, page: Page, resume_path: str) -> None:
        """Upload resume to application."""
        try:
            file_input = await page.query_selector("input[type='file']")
            if file_input:
                await file_input.set_input_files(resume_path)
                logger.info("Uploaded resume")
            else:
                logger.warning("Resume upload field not found")
        except Exception as e:
            logger.error(f"Error uploading resume: {e}")
            
    async def _upload_cover_letter(self, page: Page, cover_letter_path: str) -> None:
        """Upload cover letter to application if requested."""
        try:
            cover_letter_input = await page.query_selector("input[type='file'][accept='.pdf,.doc,.docx']")
            if cover_letter_input:
                await cover_letter_input.set_input_files(cover_letter_path)
                logger.info("Uploaded cover letter")
            else:
                logger.warning("Cover letter upload field not found")
        except Exception as e:
            logger.error(f"Error uploading cover letter: {e}")
            
    async def _handle_application_questions(self, page: Page) -> None:
        """Handle any additional application questions."""
        try:
            # Get all form fields
            question_elements = await page.query_selector_all("div.jobs-easy-apply-form-section__input")
            
            questions_answered = 0
            for element in question_elements[:self.config.max_questions_to_answer]:
                question_text = await element.text_content()
                if not question_text:
                    continue
                    
                # Add randomized delay if configured
                if self.config.random_delays:
                    delay = random.uniform(self.config.min_delay, self.config.max_delay)
                    await asyncio.sleep(delay)
                
                # Handle different input types
                if await element.query_selector("input[type='text']"):
                    await self._handle_text_input(element, question_text)
                elif await element.query_selector("select"):
                    await self._handle_select_input(element)
                elif await element.query_selector("input[type='radio']"):
                    await self._handle_radio_input(element)
                elif await element.query_selector("input[type='checkbox']"):
                    await self._handle_checkbox_input(element)
                    
                questions_answered += 1
                
            logger.info(f"Handled {questions_answered} application questions")
            
        except Exception as e:
            logger.error(f"Error handling application questions: {e}")
            
    async def _handle_text_input(self, element: ElementHandle, question: str) -> None:
        """Handle text input fields."""
        try:
            input_field = await element.query_selector("input[type='text']")
            if not input_field:
                return
                
            # Get answer from question templates or use default
            answer = await self._get_question_answer(question)
            await input_field.fill(answer)
            
        except Exception as e:
            logger.error(f"Error handling text input: {e}")
            
    async def _handle_select_input(self, element: ElementHandle) -> None:
        """Handle dropdown select fields."""
        try:
            select = await element.query_selector("select")
            if not select:
                return
                
            # Get all available options
            options = await select.query_selector_all("option")
            if not options:
                return
                
            # Select the most appropriate option (usually "Yes" or highest experience level)
            for option in options:
                value = await option.get_attribute("value")
                text = await option.text_content()
                
                if text and ("yes" in text.lower() or 
                           "proficient" in text.lower() or
                           "expert" in text.lower()):
                    await select.select_option(value=value)
                    break
                    
        except Exception as e:
            logger.error(f"Error handling select input: {e}")
            
    async def _handle_radio_input(self, element: ElementHandle) -> None:
        """Handle radio button inputs."""
        try:
            radio_buttons = await element.query_selector_all("input[type='radio']")
            if not radio_buttons:
                return
                
            # Usually select "Yes" for radio buttons
            for button in radio_buttons:
                label = await button.evaluate("el => el.labels[0].textContent")
                if label and "yes" in label.lower():
                    await button.click()
                    break
                    
        except Exception as e:
            logger.error(f"Error handling radio input: {e}")
            
    async def _handle_checkbox_input(self, element: ElementHandle) -> None:
        """Handle checkbox inputs."""
        try:
            checkbox = await element.query_selector("input[type='checkbox']")
            if not checkbox:
                return
                
            # Get checkbox label
            label = await checkbox.evaluate("el => el.labels[0].textContent")
            
            # Check boxes for positive responses
            if label and ("yes" in label.lower() or 
                       "agree" in label.lower() or
                       "confirm" in label.lower()):
                await checkbox.click()
                
        except Exception as e:
            logger.error(f"Error handling checkbox input: {e}")
            
    async def _get_question_answer(self, question: str) -> str:
        """Get appropriate answer for application question."""
        # Default answers for common questions
        default_answers = {
            "years of experience": "5",
            "expected salary": "Competitive / Market Rate",
            "notice period": "2 weeks",
            "willing to relocate": "Yes",
            "authorized to work": "Yes",
            "require sponsorship": "No"
        }
        
        # Try to find a matching default answer
        for key, answer in default_answers.items():
            if key in question.lower():
                return answer
                
        return "Yes"  # Default fallback answer

    async def apply_to_linkedin_job(self,
                             job_url: str,
                             resume_path: str,
                             cover_letter_path: Optional[str] = None,
                             phone: Optional[str] = None) -> bool:
        """
        Apply to a LinkedIn job using Easy Apply.
        
        Args:
            job_url: URL of the LinkedIn job posting
            resume_path: Path to resume file
            cover_letter_path: Optional path to cover letter
            phone: Optional phone number to fill in application
            
        Returns:
            True if application was successful, False otherwise
        """
        try:
            # Create a new browser page
            browser = await Browser.create(
                headless=self.config.headless,
                slow_mo=self.config.slow_mo
            )
            page = await browser.new_page()
            
            # Navigate to job posting
            await page.goto(job_url)
            logger.info(f"Navigated to job posting: {job_url}")
            
            # Wait for and click Easy Apply button
            try:
                easy_apply_button = await page.wait_for_selector('[data-control-name="easy_apply_button"]', timeout=5000)
                if easy_apply_button:
                    await easy_apply_button.click()
                    logger.info("Clicked Easy Apply button")
                else:
                    logger.warning("Easy Apply button not found")
                    return False
            except Exception as e:
                logger.error(f"Error finding Easy Apply button: {e}")
                return False

            # Handle each step of the application
            while True:
                try:
                    # Wait for form to load
                    await page.wait_for_selector('form.jobs-easy-apply-form', timeout=5000)
                    
                    # Check for resume upload
                    resume_upload = await page.query_selector('input[type="file"][name="resume"]')
                    if resume_upload:
                        await resume_upload.set_input_files(resume_path)
                        logger.info("Uploaded resume")
                        
                    # Check for cover letter upload
                    if cover_letter_path:
                        cover_letter_upload = await page.query_selector('input[type="file"][name="cover_letter"]')
                        if cover_letter_upload:
                            await cover_letter_upload.set_input_files(cover_letter_path)
                            logger.info("Uploaded cover letter")
                            
                    # Fill phone number if needed
                    if phone:
                        phone_input = await page.query_selector('input[type="tel"]')
                        if phone_input:
                            await phone_input.fill(phone)
                            logger.info("Filled phone number")
                            
                    # Check for additional questions
                    questions = await self._handle_additional_questions(page)
                    if not questions:
                        logger.warning("Failed to handle additional questions")
                        return False
                        
                    # Look for Next or Submit button
                    next_button = await page.query_selector('button[aria-label="Continue to next step"]')
                    submit_button = await page.query_selector('button[aria-label="Submit application"]')
                    
                    if submit_button:
                        # Final step - submit application
                        await submit_button.click()
                        logger.info("Submitted application")
                        return True
                    elif next_button:
                        # Move to next step
                        await next_button.click()
                        logger.info("Moved to next step")
                        await page.wait_for_load_state('networkidle')
                    else:
                        logger.warning("No next/submit button found")
                        return False
                        
                except Exception as e:
                    logger.error(f"Error in application step: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error applying to job: {e}")
            return False
        finally:
            await browser.close()
            
    async def _handle_additional_questions(self, page: Page) -> bool:
        """Handle additional application questions using AI."""
        try:
            # Find all question elements
            questions = await page.query_selector_all('.jobs-easy-apply-form-section__question')
            
            for question in questions:
                # Get question text
                question_text = await question.text_content()
                if not question_text:
                    continue
                    
                # Use LLM to generate appropriate answer
                answer = await self._generate_question_answer(question_text)
                
                # Find input field type and fill appropriately
                input_field = await question.query_selector('input, textarea, select')
                if input_field:
                    tag_name = await input_field.get_property('tagName')
                    tag_name = await tag_name.json_value()
                    
                    if tag_name == 'SELECT':
                        # Handle dropdown
                        options = await input_field.query_selector_all('option')
                        best_option = await self._find_best_option(options, answer)
                        if best_option:
                            await best_option.click()
                    else:
                        # Handle text input
                        await input_field.fill(answer)
                        
            return True
            
        except Exception as e:
            logger.error(f"Error handling additional questions: {e}")
            return False
            
    async def _generate_question_answer(self, question: str) -> str:
        """Generate an appropriate answer for an application question using AI."""
        try:
            agent_response = await self.agent.run(
                f"""
                Generate an appropriate answer for this job application question:
                Question: {question}
                
                Consider:
                - Be honest and professional
                - Provide specific but concise answers
                - For yes/no questions, prefer "Yes" if qualified
                - For years of experience, be consistent with resume
                """
            )
            
            return agent_response.strip()
            
        except Exception as e:
            logger.error(f"Error generating question answer: {e}")
            return ""
            
    async def _find_best_option(self, options, desired_answer: str) -> Optional[ElementHandle]:
        """Find the best matching option for a dropdown."""
        try:
            best_match = None
            highest_score = 0
            
            for option in options:
                option_text = await option.text_content()
                if not option_text:
                    continue
                    
                # Calculate simple match score
                score = self._calculate_match_score(option_text.lower(), desired_answer.lower())
                
                if score > highest_score:
                    highest_score = score
                    best_match = option
                    
            return best_match
            
        except Exception as e:
            logger.error(f"Error finding best option: {e}")
            return None
            
    def _calculate_match_score(self, text1: str, text2: str) -> float:
        """Calculate a simple match score between two strings."""
        try:
            # Convert to sets of words
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            # Calculate Jaccard similarity
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            return intersection / union if union > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating match score: {e}")
            return 0


# Example usage
async def main():
    job_search_browser = JobSearchBrowser()
    job_listings = await job_search_browser.search_for_jobs(
        keywords=["software engineer", "python"],
        location="New York",
        job_site="linkedin"
    )
    print(f"Found {len(job_listings)} job listings")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())