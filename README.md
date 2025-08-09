# AutoApply AI: Smart Job Application Assistant ✨

<!-- Badges: Add relevant badges from services like shields.io -->
<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <!-- Example: <img src="https://img.shields.io/github/workflow/status/your-username/your-repo/CI/main" alt="Build Status"> -->
  <!-- Example: <img src="https://img.shields.io/codecov/c/github/your-username/your-repo" alt="Code Coverage"> -->
</p>

**AutoApply AI is an intelligent system designed to streamline your job search. It automates finding relevant job postings, crafting personalized resumes and cover letters using AI, and assists with application submissions, helping you land your dream job faster.**

---

## 🌟 Features

- 🔍 **Multi-source Job Search**: Search for jobs across LinkedIn, Indeed, Glassdoor, and other platforms.
- 🧠 **Intelligent Job Filtering**: Filter jobs based on your skills, experience, location, and custom keywords.
- ✍️ **AI-Powered Document Generation**: Create tailored resumes and cover letters for each job application using advanced AI models (e.g., Llama 4 Maverick, Llama 3).
- 🚀 **Automated Application Submission**: Assists with or fully automates submitting applications through supported platforms like LinkedIn.
- 📊 **Job Match Scoring**: Calculates compatibility scores between your profile and job requirements to prioritize applications.
- 📈 **Application Tracking**: Keep track of all your job applications, their statuses, and follow-up actions in one place.
- 📄 **Resume Optimization**: Analyzes your existing resume against job descriptions and suggests improvements.

---

## 🎬 Demo / Screenshots

*(Placeholder: Consider adding a GIF or screenshots showcasing AutoApply AI in action. For example, a screen recording of the job search, resume generation, or application submission process.)*

```
[-------------------------------------]
|                                     |
|        Your Awesome GIF/Image       |
|         Showcasing the App          |
|                                     |
[-------------------------------------]
```

---

## 📚 Table of Contents

- [AutoApply AI: Smart Job Application Assistant ✨](#autoapply-ai-smart-job-application-assistant-)
- [🌟 Features](#-features)
- [🎬 Demo / Screenshots](#-demo--screenshots)
- [🛠️ Technology Stack](#️-technology-stack)
- [📁 Project Structure](#-project-structure)
- [🚀 Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [💡 Usage](#-usage)
- [🎨 Customization](#-customization)
  - [Resume and Cover Letter Templates](#resume-and-cover-letter-templates)
- [🤝 Contributing](#-contributing)
- [🛡️ Safety and Ethics](#️-safety-and-ethics)
- [📜 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)

---

## 🛠️ Technology Stack

- **Core Engine**: Python
- **Browser Automation**: `browser-use` for automating web interactions.
- **Web Scraping**: `Crawl4AI` for intelligent data extraction from job listings.
- **LinkedIn Integration**: Custom integration (potentially using `linkedin-mcp-config.py` logic).
- **AI-Powered Document Generation**: Configurable LLMs (e.g., Llama 4 Maverick, Llama 3) via APIs (GitHub, Groq, OpenRouter) or local `llama_cpp` setup. See <mcfile name="llama_config.py" path="c:\Users\rayyan.a\PycharmProjects\linkedin\job_application_automation\config\llama_config.py"></mcfile>.
- **Document Processing**: `python-docx` and `docxtpl` for MS Word documents.
- **Database**: SQLAlchemy for application tracking (see <mcfile name="application_tracker.py" path="c:\Users\rayyan.a\PycharmProjects\linkedin\job_application_automation\src\application_tracker.py"></mcfile> and <mcfile name="database.py" path="c:\Users\rayyan.a\PycharmProjects\linkedin\job_application_automation\src\database.py"></mcfile>).
- **Database Migrations**: Alembic (see <mcfile name="alembic.ini" path="c:\Users\rayyan.a\PycharmProjects\linkedin\job_application_automation\alembic.ini"></mcfile>).
- **Configuration Management**: Pydantic, `.env` files, YAML (e.g., `config/config.yaml`).
- **Dependencies**: Managed via <mcfile name="requirements.txt" path="c:\Users\rayyan.a\PycharmProjects\linkedin\job_application_automation\requirements.txt"></mcfile> (and potentially <mcfile name="pyproject.toml" path="c:\Users\rayyan.a\PycharmProjects\linkedin\pyproject.toml"></mcfile> for the broader workspace).

---

## 📁 Project Structure

```
job_application_automation/
├── .env.example                # Example environment variables
├── README.md                   # This file
├── requirements.txt            # Python dependencies for this application
├── alembic.ini                 # Alembic migration configuration
├── config/                     # Configuration settings
│   ├── __init__.py
│   ├── browser_config.py       # Browser automation settings
│   ├── llama_config.py         # LLM settings
│   └── ... (other config files)
├── data/                       # Data storage (logs, generated docs, DB, etc.)
│   ├── candidate_profile.json  # Example candidate profile
│   ├── job_applications.db     # SQLite database for tracking
│   └── generated_cover_letters/
├── src/                        # Source code
│   ├── __init__.py
│   ├── main.py                 # Main application entry point
│   ├── smart_apply.py          # Core application logic script
│   ├── browser_automation.py   # Browser interaction logic
│   ├── web_scraping.py         # Job scraping utilities
│   ├── linkedin_integration.py # LinkedIn specific functions
│   ├── resume_cover_letter_generator.py # AI document generation
│   ├── resume_optimizer.py     # Resume analysis and improvement
│   ├── application_tracker.py  # Tracks job applications
│   ├── database.py             # Database models and session management
│   └── ... (other modules)
├── templates/                  # Document templates (resume, cover letter)
│   ├── resume_template.docx
│   └── cover_letter_template.docx
├── tests/                      # Test cases
└── ... (other project files)
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Pip (Python package installer)
- Git (for cloning the repository)
- Access to an LLM:
    - API key for services like Groq, OpenRouter, OR
    - GitHub Personal Access Token for GitHub Models (like Llama 4 Maverick), OR
    - A local GGUF model file (e.g., Llama 3, Llama 2) and `llama-cpp-python` installed.
- (Optional) LinkedIn account for features involving direct LinkedIn interaction.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name/job_application_automation 
    ```
    *(Replace `your-username/your-repo-name` with your actual repository URL if applicable, otherwise adjust `cd` path if already cloned.)*

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    # From project root
    pip install -r job_application_automation/requirements.txt
    ```
    *(If `llama-cpp-python` is needed for local models and not in `requirements.txt`, you might need to install it separately, potentially with GPU support flags like `CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python`)*

### Configuration

1.  **Set up Environment Variables:**
    Navigate to the `job_application_automation` directory. Copy the <mcfile name=".env.example" path="c:\Users\rayyan.a\PycharmProjects\linkedin\job_application_automation\.env.example"></mcfile> file to `.env`:
    ```bash
    cp .env.example .env  # For macOS/Linux
     # copy .env.example .env  # For Windows
    ```
    Edit the `.env` file with your specific configurations. Key variables to set (refer to <mcfile name="llama_config.py" path="c:\Users\rayyan.a\PycharmProjects\linkedin\job_application_automation\config\llama_config.py"></mcfile> for details):
    ```env
    # --- LLM Configuration ---
    LLAMA_USE_API=True # Set to False for local model
    LLAMA_API_PROVIDER="github" # Options: "github", "groq", "openrouter", "local"
    
    # If LLAMA_API_PROVIDER="github"
    GITHUB_TOKEN="your_github_personal_access_token_with_models_scope" 
    LLAMA_API_MODEL="meta/Llama-4-Maverick-17B-128E-Instruct-FP8" # Or other compatible GitHub model

    # If LLAMA_API_PROVIDER="groq"
    # GROQ_API_KEY="your_groq_api_key"
    # LLAMA_API_MODEL="llama3-8b-8192" # Or other Groq model

    # If LLAMA_API_PROVIDER="openrouter"
    # OPENROUTER_API_KEY="your_openrouter_api_key"
    # LLAMA_API_MODEL="meta-llama/llama-3-8b-instruct" # Or other OpenRouter model
    
    # If LLAMA_USE_API=False (for local model)
    # LLAMA_MODEL_PATH="../models/your_local_model_name.gguf" # Adjust path to your model file
    # LLAMA_USE_GPU=True # Set to False if no compatible GPU
    # LLAMA_GPU_LAYERS=32 # Adjust based on your GPU capabilities and model (0 for CPU only)

    # --- LinkedIn Credentials (Optional) ---
    # LINKEDIN_EMAIL="your_linkedin_email"
    # LINKEDIN_PASSWORD="your_linkedin_password"

    # --- Other configurations ---
    # Review config/ files for more settings like browser paths, etc.
    ```

2.  **Database Setup:**
    The application uses SQLAlchemy and Alembic for database management (tracking job applications).
    Initialize or upgrade the database schema:
    ```bash
     cd job_application_automation && alembic upgrade head
    ```
    This command should be run from the `job_application_automation` directory where `alembic.ini` is located. This will create/update the `job_applications.db` file in the `job_application_automation/data/` directory.

3.  **Candidate Profile:**
    Create or update your candidate profile in `data/candidate_profile.json`. This file is used to personalize resumes and cover letters. An example structure might be:
    ```json
    {
      "full_name": "Your Name",
      "email": "your.email@example.com",
      "phone": "123-456-7890",
      "linkedin_url": "https://linkedin.com/in/yourprofile",
      "github_url": "https://github.com/yourusername",
      "portfolio_url": "https://yourportfolio.com",
      "summary": "A brief professional summary...",
      "skills": ["Python", "AI", "Web Scraping", "Project Management"],
      "experience": [
        {
          "title": "Software Engineer",
          "company": "Tech Corp",
          "dates": "Jan 2020 - Present",
          "description": "Developed amazing things..."
        }
      ],
      "education": [
        {
          "degree": "B.S. in Computer Science",
          "university": "State University",
          "year": "2019"
        }
      ]
    }
    ```

---

## 💡 Usage

The primary way to run the application is likely through <mcfile name="smart_apply.py" path="c:\Users\rayyan.a\PycharmProjects\linkedin\job_application_automation\src\smart_apply.py"></mcfile> or <mcfile name="main.py" path="c:\Users\rayyan.a\PycharmProjects\linkedin\job_application_automation\src\main.py"></mcfile>.

1.  **Run the application:**
    ```bash
    cd job_application_automation
    python src/cli.py search --keywords "python,ai" --location "Remote"
    ```
    *(Or `python src/main.py` for the end-to-end flow.)*

2.  **Interactive Mode / CLI:**
    The application might offer an interactive command-line interface to:
    - Search for jobs.
    - Select jobs for application.
    - Review and approve generated documents.
    - Track application status.
    *(Refer to the script's help messages or internal documentation for specific commands: `python src/smart_apply.py --help`)*

---

## 🎨 Customization

### Resume and Cover Letter Templates

You can customize the base MS Word templates used for document generation. These are located in the `templates/` directory:

-   `templates/resume_template.docx`: Base template for resumes.
-   `templates/cover_letter_template.docx`: Base template for cover letters.

These templates use Jinja2 syntax (e.g., `{{ variable_name }}`) for placeholders that the AI will populate. You can modify their structure, formatting, and add or remove placeholders to better suit your personal style. The <mcsymbol name="CoverLetterTemplateManager" filename="resume_cover_letter_generator.py" path="c:\Users\rayyan.a\PycharmProjects\linkedin\job_application_automation\src\resume_cover_letter_generator.py" startline="61" type="class"></mcsymbol> in <mcfile name="resume_cover_letter_generator.py" path="c:\Users\rayyan.a\PycharmProjects\linkedin\job_application_automation\src\resume_cover_letter_generator.py"></mcfile> shows how different styles/templates can be managed programmatically.

---

## 🤝 Contributing

Contributions are highly welcome! Whether it's reporting a bug, proposing a new feature, improving documentation, or writing code, your help is appreciated.

1.  **Fork the repository.**
2.  **Create a new branch** for your feature or bug fix:
    ```bash
    git checkout -b feature/your-amazing-feature
    ```
3.  **Make your changes** and commit them with clear, descriptive messages.
4.  **Ensure your code passes any existing tests** and, if adding new features, include new tests.
5.  **Push your branch** to your fork:
    ```bash
    git push origin feature/your-amazing-feature
    ```
6.  **Open a Pull Request** against the `main` (or `develop`) branch of the original repository. Please provide a detailed description of your changes.

---

## 🛡️ Safety and Ethics

AutoApply AI is a powerful tool. Please use it responsibly and ethically:

1.  **Review AI-Generated Content**: **Always** carefully review resumes, cover letters, and any application answers generated by the AI before submission. Ensure accuracy, authenticity, and that it truly represents you.
2.  **Respect Rate Limits**: Be mindful of the frequency of job searches and application submissions to avoid overloading job portals or APIs. Configure delays if necessary.
3.  **Honest Representation**: Do not use this tool to misrepresent your skills, experience, or qualifications. The AI is an assistant, not a replacement for your genuine abilities.
4.  **Adhere to Terms of Service**: Respect the terms of service of any job boards (LinkedIn, Indeed, etc.) or platforms interacted with by this tool. Automation may be against the ToS of some platforms.
5.  **Privacy**: Be cautious about the personal information you provide (credentials, profile data) and how it's handled by the system and any third-party APIs. Store sensitive data securely.

---

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file in the repository for full details.
*(If no LICENSE file exists, consider adding one. MIT is a common choice for open-source projects.)*

---

## 🙏 Acknowledgments

This project stands on the shoulders of giants and leverages many fantastic open-source tools and communities:

-   [browser-use](https://github.com/browser-use/browser-use) for robust browser automation.
-   [Crawl4AI](https://github.com/crawl4ai/crawl4ai) for intelligent web scraping.
-   LLM Providers & Libraries (e.g., [Llama CPP](https://github.com/ggerganov/llama.cpp) for local models, Hugging Face, OpenAI, Groq, OpenRouter).
-   [python-docx-template (docxtpl)](https://github.com/elapouya/python-docx-template) for Word document template rendering.
-   The Python community and the developers of numerous other libraries used.

---

*This README was enhanced with the help of Trae AI, your agentic AI coding assistant.*
```

        