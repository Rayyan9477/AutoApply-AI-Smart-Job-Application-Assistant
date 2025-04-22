#!/usr/bin/env python3
"""
Smart Job Application Script

This script automates the job application process by:
1. Taking a job description as input
2. Scoring the resume against the job description
3. Optimizing the resume if the score is below threshold
4. Submitting the application if the score meets threshold

Usage:
    python smart_apply.py --job-desc "path/to/job_description.txt" --resume "path/to/resume.pdf" 
                         [--threshold 80] [--no-apply] [--external-url URL]
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import asyncio
import webbrowser
from datetime import datetime

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import project modules
from src.ats_integration import ATSIntegrationManager
from src.linkedin_integration import LinkedInIntegration
from src.resume_optimizer import ATSScorer, ResumeOptimizer
from src.application_tracker import ApplicationTracker
from config.llama_config import LlamaConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, "data", "main.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SmartJobApplicant:
    """
    Class to handle the smart job application workflow.
    """
    
    def __init__(self, llama_config: Optional[LlamaConfig] = None):
        """Initialize the Smart Job Applicant."""
        self.ats_manager = ATSIntegrationManager(llama_config)
        self.linkedin = LinkedInIntegration()
        self.app_tracker = ApplicationTracker()
        self.score_threshold = 0.8  # Default 80% threshold
        
    async def process_job(self,
                     resume_path: str,
                     job_description: str,
                     job_metadata: Dict[str, Any],
                     score_threshold: float = 0.8,
                     auto_apply: bool = True,
                     external_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a job application using the smart workflow.
        
        Args:
            resume_path: Path to the resume file
            job_description: The job description text
            job_metadata: Dictionary with job metadata (title, company, etc.)
            score_threshold: ATS score threshold to proceed (0.0-1.0)
            auto_apply: Whether to attempt automatic application
            external_url: URL for external job application
            
        Returns:
            Dictionary with process results
        """
        logger.info(f"Processing job: {job_metadata.get('job_title')} at {job_metadata.get('company')}")
        
        # 1. Process through ATS and optimize if needed
        ats_result = self.ats_manager.process_job_application(
            resume_path=resume_path,
            job_description=job_description,
            job_metadata=job_metadata,
            min_score_threshold=score_threshold,
            auto_optimize=True
        )
        
        # 2. Determine if we should proceed with application
        if not ats_result["should_proceed"]:
            logger.warning(f"ATS score below threshold ({score_threshold*100}%), not proceeding with application")
            result = {
                "success": False,
                "message": f"ATS score too low: {ats_result['original_score']['overall_score']}%",
                "ats_result": ats_result
            }
            
            # Track in application tracker
            self.app_tracker.add_application(
                job_title=job_metadata.get("job_title", "Unknown"),
                company=job_metadata.get("company", "Unknown"),
                status="rejected",
                reason=f"ATS score below threshold: {ats_result['original_score']['overall_score']}%",
                url=job_metadata.get("url", external_url),
                application_data={
                    "resume_path": resume_path,
                    "ats_report": ats_result["report_path"]
                }
            )
            
            return result
        
        # 3. Determine which resume to use (original or optimized)
        selected_resume = ats_result.get("optimized_resume", resume_path) or resume_path
        
        # 4. Track the application attempt
        application_id = self.app_tracker.add_application(
            job_title=job_metadata.get("job_title", "Unknown"),
            company=job_metadata.get("company", "Unknown"),
            status="in_progress",
            url=job_metadata.get("url", external_url),
            application_data={
                "resume_path": selected_resume,
                "ats_report": ats_result["report_path"]
            }
        )
        
        # 5. Determine application approach based on job source
        if not auto_apply:
            # Just prepare materials but don't apply
            result = {
                "success": True,
                "applied": False,
                "message": "Resume optimized but auto-apply disabled",
                "resume_path": selected_resume,
                "ats_result": ats_result,
                "application_id": application_id
            }
            
            # Update application tracker
            self.app_tracker.update_application(
                application_id=application_id,
                status="prepared",
                notes="Resume optimized but auto-apply disabled"
            )
            
            return result
        
        # 6. Try to apply (LinkedIn or external)
        try:
            # A. Check if it's a LinkedIn job
            if job_metadata.get("source") == "linkedin" and job_metadata.get("job_id"):
                # Authenticate with LinkedIn
                authenticated = await self.linkedin.authenticate()
                if authenticated:
                    # Apply via LinkedIn
                    cover_letter_path = None  # Add cover letter generation if needed
                    
                    success = await self.linkedin.apply_to_job(
                        job_id=job_metadata["job_id"],
                        resume_path=selected_resume,
                        cover_letter_path=cover_letter_path
                    )
                    
                    if success:
                        self.app_tracker.update_application(
                            application_id=application_id,
                            status="applied",
                            notes=f"Successfully applied via LinkedIn on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        )
                        
                        result = {
                            "success": True,
                            "applied": True,
                            "message": "Successfully applied via LinkedIn",
                            "resume_path": selected_resume,
                            "ats_result": ats_result,
                            "application_id": application_id
                        }
                    else:
                        self.app_tracker.update_application(
                            application_id=application_id,
                            status="failed",
                            notes=f"Failed to apply via LinkedIn on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        )
                        
                        result = {
                            "success": False,
                            "applied": False,
                            "message": "Failed to apply via LinkedIn",
                            "resume_path": selected_resume,
                            "ats_result": ats_result,
                            "application_id": application_id
                        }
                else:
                    # LinkedIn auth failed
                    self.app_tracker.update_application(
                        application_id=application_id,
                        status="pending",
                        notes="LinkedIn authentication failed, manual application required"
                    )
                    
                    result = {
                        "success": False,
                        "applied": False,
                        "message": "LinkedIn authentication failed",
                        "resume_path": selected_resume,
                        "ats_result": ats_result,
                        "application_id": application_id
                    }
            
            # B. External URL provided
            elif external_url:
                # Open browser to the application URL
                webbrowser.open(external_url)
                
                self.app_tracker.update_application(
                    application_id=application_id,
                    status="in_progress",
                    notes=f"Browser opened to {external_url} for manual application completion"
                )
                
                result = {
                    "success": True,
                    "applied": False,
                    "message": "Browser opened for external application",
                    "resume_path": selected_resume,
                    "external_url": external_url,
                    "ats_result": ats_result,
                    "application_id": application_id
                }
            
            # C. No application method available
            else:
                self.app_tracker.update_application(
                    application_id=application_id,
                    status="pending",
                    notes="No application method available"
                )
                
                result = {
                    "success": False,
                    "applied": False,
                    "message": "No application method available",
                    "resume_path": selected_resume,
                    "ats_result": ats_result,
                    "application_id": application_id
                }
                
        except Exception as e:
            logger.error(f"Error during application process: {e}")
            
            self.app_tracker.update_application(
                application_id=application_id,
                status="error",
                notes=f"Error during application: {str(e)}"
            )
            
            result = {
                "success": False,
                "applied": False,
                "message": f"Error during application: {str(e)}",
                "resume_path": selected_resume,
                "ats_result": ats_result,
                "application_id": application_id
            }
        
        return result
    
    def get_application_status(self, application_id: str) -> Dict[str, Any]:
        """
        Get the status of an application.
        
        Args:
            application_id: Application ID to check
            
        Returns:
            Dictionary with application status information
        """
        return self.app_tracker.get_application(application_id)
    
    def generate_ats_report(self) -> str:
        """Generate overall ATS performance report."""
        return self.ats_manager.generate_ats_performance_report()


async def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Smart Job Application Script")
    parser.add_argument("--job-desc", type=str, help="Path to job description file or raw job description")
    parser.add_argument("--resume", type=str, default="Rayyan_Ahmed_Resume_2025.pdf", 
                      help="Path to resume file (default: Rayyan_Ahmed_Resume_2025.pdf)")
    parser.add_argument("--threshold", type=float, default=80,
                      help="ATS score threshold percentage (default: 80)")
    parser.add_argument("--no-apply", action="store_true",
                      help="Don't auto-apply, just optimize resume")
    parser.add_argument("--external-url", type=str,
                      help="URL for external job application")
    parser.add_argument("--job-title", type=str, default="",
                      help="Job title")
    parser.add_argument("--company", type=str, default="",
                      help="Company name")
    parser.add_argument("--report", action="store_true",
                      help="Generate ATS performance report")
    
    args = parser.parse_args()
    
    # Create smart applicant
    applicant = SmartJobApplicant()
    
    # If generating report only
    if args.report:
        report_path = applicant.generate_ats_report()
        if report_path:
            print(f"Generated ATS performance report: {report_path}")
            
            # Open the report in browser
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
        else:
            print("Failed to generate ATS performance report")
        return
    
    # Check required arguments
    if not args.job_desc:
        print("Error: Job description is required")
        parser.print_help()
        return
    
    # Load resume path
    resume_path = os.path.join(project_root, args.resume)
    if not os.path.isabs(args.resume):
        resume_path = os.path.join(project_root, args.resume)
    
    if not os.path.exists(resume_path):
        print(f"Error: Resume file not found: {resume_path}")
        return
    
    # Check if job description is a file or raw text
    job_description = args.job_desc
    if os.path.exists(args.job_desc):
        with open(args.job_desc, 'r', encoding='utf-8') as f:
            job_description = f.read()
    
    # Create job metadata
    job_title = args.job_title or "Job Position"
    company = args.company or "Company"
    
    job_metadata = {
        "job_title": job_title,
        "company": company,
        "url": args.external_url,
        "job_id": f"manual_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    }
    
    # Process job
    result = await applicant.process_job(
        resume_path=resume_path,
        job_description=job_description,
        job_metadata=job_metadata,
        score_threshold=args.threshold / 100.0,  # Convert percentage to decimal
        auto_apply=not args.no_apply,
        external_url=args.external_url
    )
    
    # Print result
    print("\n=== Smart Job Application Results ===")
    
    if result.get("ats_result"):
        ats_score = result["ats_result"]["original_score"]["overall_score"]
        print(f"Original ATS Score: {ats_score}%")
        
        if result["ats_result"].get("optimized_score"):
            opt_score = result["ats_result"]["optimized_score"]["overall_score"]
            print(f"Optimized ATS Score: {opt_score}%")
    
    print(f"Status: {'Success' if result['success'] else 'Failed'}")
    print(f"Message: {result['message']}")
    
    if result.get("resume_path"):
        print(f"Resume used: {result['resume_path']}")
    
    if result.get("application_id"):
        print(f"Application ID: {result['application_id']}")
        
    # Open ATS report if available
    if result.get("ats_result", {}).get("report_path"):
        report_path = result["ats_result"]["report_path"]
        print(f"ATS Report: {report_path}")
        
        # Ask if user wants to view the report
        view_report = input("Do you want to view the ATS report? (y/n): ")
        if view_report.lower() == 'y':
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
    
    # Continue applying?
    if not args.no_apply and not result.get("applied", False):
        continue_app = input("Do you want to manually complete this application? (y/n): ")
        if continue_app.lower() == 'y' and args.external_url:
            webbrowser.open(args.external_url)


if __name__ == "__main__":
    asyncio.run(main())