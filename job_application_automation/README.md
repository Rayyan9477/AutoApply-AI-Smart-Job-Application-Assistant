# Automated Job Application System

## Overview

The Automated Job Application System is an advanced tool designed to streamline the job application process by automating various steps from job search to application submission. The system leverages AI technologies to find relevant job postings, generate personalized resumes and cover letters, and even submit applications automatically where possible.

## Features

- **Multi-source Job Search**: Search for jobs across LinkedIn, Indeed, and Glassdoor.
- **Intelligent Job Filtering**: Filter jobs based on skills, experience, and keywords.
- **Personalized Document Generation**: Create tailored resumes and cover letters for each job using AI.
- **Automated Application Submission**: Submit applications automatically through LinkedIn.
- **Job Match Scoring**: Calculate compatibility scores between your profile and job requirements.

## Technology Stack

- **Browser Automation**: Uses `browser-use` to automate web interactions.
- **Web Scraping**: Uses `Crawl4AI` for intelligent data extraction from job listings.
- **LinkedIn Integration**: Uses LinkedIn MCP for direct API interaction.
- **AI-Powered Document Generation**: Uses `Llama 4 Mevrick` for generating personalized resumes and cover letters.
- **Document Processing**: Handles MS Word documents with `python-docx` and `docxtpl`.

## Project Structure

```
job_application_automation/
├── config/                     # Configuration settings
│   ├── __init__.py
│   ├── browser_config.py       # Browser automation settings
│   ├── crawl4ai_config.py      # Web scraping settings
│   ├── linkedin_mcp_config.py  # LinkedIn integration settings
│   └── llama_config.py         # LLM settings for document generation
├── data/                       # Data storage directory
│   └── generated_cover_letters/ # Generated cover letters
├── src/                        # Source code
│   ├── __init__.py
│   ├── browser_automation.py   # Browser automation functionality
│   ├── web_scraping.py         # Web scraping functionality
│   ├── linkedin_integration.py # LinkedIn API integration
│   ├── resume_cover_letter_generator.py # Resume and cover letter generation
│   └── main.py                 # Main application entry point
├── templates/                  # Document templates
│   ├── resume_template.docx    # Template for resume generation
│   └── cover_letter_template.docx # Template for cover letter generation
└── tests/                      # Test cases
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Required Python packages (see `requirements.txt`)
- LinkedIn API access (optional)
- Llama 4 Mevrick model (for AI document generation)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/job_application_automation.git
   cd job_application_automation
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Download the Llama 4 Mevrick model and update `config/llama_config.py` with the path.

4. Create a `.env` file with your configuration:
   ```
   BROWSER_USE_API_KEY=your_api_key
   LINKEDIN_CLIENT_ID=your_client_id
   LINKEDIN_CLIENT_SECRET=your_client_secret
   LINKEDIN_REDIRECT_URI=http://localhost:8000/linkedin/callback
   ```

### Usage

1. First, edit your candidate profile:
   ```bash
   # The system will create a default profile if none exists
   # Edit the file at data/candidate_profile.json
   ```

2. Run the application with basic settings:
   ```bash
   python src/main.py --keywords "software engineer" "python" --location "Remote"
   ```

3. Advanced usage with filtering:
   ```bash
   python src/main.py --keywords "data scientist" "machine learning" --location "New York" \
                     --required-skills "python,sql,machine learning" \
                     --excluded-keywords "senior,principal,10+ years" \
                     --max-jobs 20 --max-applications 10 \
                     --job-site indeed
   ```

4. Use automatic application submission (use with caution):
   ```bash
   python src/main.py --auto-apply
   ```

### Command-line Options

- `--keywords`: Search keywords (e.g., job titles, skills)
- `--location`: Job location
- `--job-site`: Job site to search (linkedin, indeed, glassdoor)
- `--no-linkedin`: Disable LinkedIn API search
- `--no-browser`: Disable browser automation search
- `--max-jobs`: Maximum number of jobs to scrape details for
- `--min-match-score`: Minimum match score for job filtering (0.0-1.0)
- `--required-skills`: Comma-separated list of required skills
- `--excluded-keywords`: Comma-separated list of keywords to exclude
- `--max-applications`: Maximum number of applications to submit
- `--auto-apply`: Enable automatic application submission

## Customization

### Resume and Cover Letter Templates

You can customize the templates in the `templates` directory:
- `resume_template.docx`: Template for resume generation
- `cover_letter_template.docx`: Template for cover letter generation

The templates use Jinja2 syntax for variable substitution.

### Configuration Files

Each component has its own configuration file:
- `browser_config.py`: Configure browser automation settings
- `crawl4ai_config.py`: Configure web scraping settings
- `linkedin_mcp_config.py`: Configure LinkedIn integration
- `llama_config.py`: Configure LLM settings

## Safety and Ethics

This tool is designed to assist with job applications, not to spam employers. Please use it responsibly and ethically:

1. Set reasonable rate limits for job searches and applications
2. Carefully review generated documents before submission
3. Do not misrepresent your qualifications
4. Respect website terms of service

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [browser-use](https://github.com/browser-use/browser-use) for browser automation
- [Crawl4AI](https://github.com/crawl4ai/crawl4ai) for web scraping
- [Llama CPP](https://github.com/ggerganov/llama.cpp) for LLM integration
- [docxtpl](https://github.com/elapouya/python-docx-template) for document template rendering