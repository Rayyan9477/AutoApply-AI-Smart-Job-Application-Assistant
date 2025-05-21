"""
Configuration settings for LLM integration using Llama 4 Maverick.
"""
import os
from pydantic import BaseModel, SecretStr, Field
from typing import Dict, List, Optional, Literal, Union, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LlamaConfig(BaseModel):
    """Configuration for Llama 4 Maverick LLM integration."""
    
    # API Integration Settings
    use_api: bool = True  # Default to use API since we're using GitHub token approach
    api_provider: Literal["local", "groq", "openrouter", "github"] = "github"
    api_key: Optional[str] = None
    api_base_url: Optional[str] = "https://models.github.ai/inference"
    api_model: Optional[str] = "meta/Llama-4-Maverick-17B-128E-Instruct-FP8"  # Default model name for Llama 4 Maverick
    api_request_timeout: int = 60  # Seconds
    
    # GitHub token for Llama 4 access
    github_token: Optional[str] = Field(default_factory=lambda: os.getenv("GITHUB_TOKEN"))
    
    # Model settings
    model_path: str = "../models/llama-4-maverick"
    model_type: Literal["llama", "gpt4all", "falcon"] = "llama"
    context_length: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    
    # Performance settings
    batch_size: int = 8
    num_threads: int = 4
    use_gpu: bool = True
    gpu_layers: int = 32
    
    # Resume generation settings
    resume_templates: Dict[str, str] = {
        "technical": "../templates/technical_resume.docx",
        "executive": "../templates/executive_resume.docx",
        "creative": "../templates/creative_resume.docx",
        "academic": "../templates/academic_resume.docx"
    }
    
    resume_prompt_templates: Dict[str, str] = {
        "skills_section": """
        Analyze the job requirements and candidate's skills:
        {job_requirements}
        {candidate_skills}
        
        Generate a tailored skills section that:
        1. Prioritizes relevant skills
        2. Uses industry-standard terminology
        3. Includes both technical and soft skills
        4. Matches the job requirements
        """,
        
        "experience_section": """
        Optimize work experience for this role:
        Job Description: {job_description}
        Current Experience: {work_experience}
        
        Enhance the experience section to:
        1. Highlight relevant achievements
        2. Use industry keywords
        3. Quantify results where possible
        4. Match required qualifications
        """,
        
        "summary_section": """
        Create a compelling professional summary:
        Role: {job_title}
        Company: {company_name}
        Key Requirements: {key_requirements}
        Candidate Background: {candidate_background}
        
        Generate a summary that:
        1. Aligns with the role
        2. Highlights relevant expertise
        3. Includes key achievements
        4. Uses powerful action verbs
        """
    }
    
    # Cover letter generation settings
    cover_letter_templates: Dict[str, str] = {
        "standard": "../templates/standard_cover_letter.docx",
        "technical": "../templates/technical_cover_letter.docx",
        "creative": "../templates/creative_cover_letter.docx",
        "executive": "../templates/executive_cover_letter.docx",
        "career_change": "../templates/career_change_cover_letter.docx",
        "referral": "../templates/referral_cover_letter.docx"
    }
    
    cover_letter_prompt_templates: Dict[str, str] = {
        "opening_paragraph": """
        Create an engaging opening paragraph:
        Job Title: {job_title}
        Company: {company_name}
        Source: {application_source}
        Key Requirements: {key_requirements}
        
        Generate an opening that:
        1. Shows enthusiasm
        2. Mentions the specific role
        3. Indicates how you found the position
        4. Teases your relevant qualifications
        """,
        
        "body_paragraphs": """
        Generate compelling body paragraphs:
        Job Requirements: {job_requirements}
        Candidate Experience: {relevant_experience}
        Key Achievements: {key_achievements}
        Company Research: {company_research}
        
        Create paragraphs that:
        1. Match requirements to experience
        2. Provide specific examples
        3. Show company knowledge
        4. Demonstrate cultural fit
        """,
        
        "closing_paragraph": """
        Write a strong closing paragraph:
        Action Desired: {call_to_action}
        Follow-up: {follow_up_plan}
        Contact Info: {contact_information}
        
        Create a closing that:
        1. Reiterates interest
        2. Requests an interview
        3. Thanks the reader
        4. Provides clear next steps
        """
    }
    
    # Question answering settings
    qa_templates: Dict[str, str] = {
        "experience": """
        Generate an answer about work experience:
        Question: {question}
        Relevant Experience: {experience}
        Years in Field: {years}
        
        Create a response that:
        1. Is specific and quantifiable
        2. Highlights achievements
        3. Matches the role requirements
        4. Shows growth and learning
        """,
        
        "skills": """
        Answer technical/skill-based questions:
        Question: {question}
        Relevant Skills: {skills}
        Proficiency Levels: {proficiency}
        
        Generate an answer that:
        1. Demonstrates expertise
        2. Provides examples
        3. Shows problem-solving ability
        4. Indicates continuous learning
        """,
        
        "behavioral": """
        Answer behavioral interview questions:
        Question: {question}
        Relevant Situation: {situation}
        Action Taken: {action}
        Result: {result}
        
        Create a STAR response that:
        1. Sets clear context
        2. Explains specific actions
        3. Quantifies results
        4. Shows learning/growth
        """
    }
    
    # Output settings
    output_format: Literal["docx", "pdf", "txt", "md"] = "docx"
    
    # API configuration based on provider
    def get_api_config(self) -> Dict[str, Any]:
        """Return the appropriate API configuration based on the selected provider."""
        if not self.use_api:
            return {}
            
        if self.api_provider == "groq":
            return {
                "api_base": self.api_base_url or "https://api.groq.com/openai/v1",
                "api_key": self.api_key or os.getenv("GROQ_API_KEY", ""),
                "model": self.api_model or "llama-4-maverick",
                "timeout": self.api_request_timeout
            }
        elif self.api_provider == "openrouter":
            return {
                "api_base": self.api_base_url or "https://openrouter.ai/api/v1",
                "api_key": self.api_key or os.getenv("OPENROUTER_API_KEY", ""),
                "model": self.api_model or "meta/llama-4-maverick",
                "timeout": self.api_request_timeout
            }
        elif self.api_provider == "github":
            return {
                "endpoint": self.api_base_url or "https://models.github.ai/inference",
                "token": self.github_token or os.getenv("GITHUB_TOKEN", ""),
                "model": self.api_model or "meta/Llama-4-Maverick-17B-128E-Instruct-FP8",
                "timeout": self.api_request_timeout
            }
        return {}
    
    def __init__(self, **data):
        """Initialize configuration and ensure environment variables are loaded."""
        # Load environment variables first
        load_dotenv()
        # If github_token not provided in data, try to get it from environment
        if "github_token" not in data:
            data["github_token"] = os.getenv("GITHUB_TOKEN")
        super().__init__(**data)
    
    @classmethod
    def from_env(cls) -> "LlamaConfig":
        """Create configuration from environment variables."""
        return cls(
            model_path=os.getenv("LLAMA_MODEL_PATH", "../models/llama-4-maverick"),
            use_gpu=os.getenv("LLAMA_USE_GPU", "True").lower() == "true",
            gpu_layers=int(os.getenv("LLAMA_GPU_LAYERS", "32")),
            # API settings
            use_api=os.getenv("LLAMA_USE_API", "True").lower() == "true",  # Default to True
            api_provider=os.getenv("LLAMA_API_PROVIDER", "github"),  # Default to github
            api_key=os.getenv("GROQ_API_KEY") or os.getenv("OPENROUTER_API_KEY"),
            github_token=os.getenv("GITHUB_TOKEN"),
            api_model=os.getenv("LLAMA_API_MODEL", "meta/Llama-4-Maverick-17B-128E-Instruct-FP8")
        )