from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Job Application Automation System"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

setup(
    name="job_application_automation",
    version="1.0.0",
    description="Automated job application system with AI-powered resume and cover letter generation",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Rayyan Ahmed",
    author_email="rayyanahmed265@yahoo.com",
    url="https://github.com/Rayyan9477/job-application-automation",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "isort>=5.12.0",
        ],
        "gpu": [
            "torch>=2.1.0+cu118",  # CUDA 11.8 version
            "faiss-gpu>=1.7.0",
        ],
        "full": [
            "google-generativeai>=0.3.0",
            "openai>=1.3.0",
            "transformers>=4.35.0",
            "sentence-transformers>=2.2.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "job-apply=cli:main",
            "job-automation=main:main",
            "ats-analyzer=ats_cli:main",
            "db-manager=manage_db:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
    ],
    keywords="job application automation ai resume cover letter linkedin",
    project_urls={
        "Bug Reports": "https://github.com/Rayyan9477/job-application-automation/issues",
        "Source": "https://github.com/Rayyan9477/job-application-automation",
        "Documentation": "https://github.com/Rayyan9477/job-application-automation/blob/main/README.md",
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.md", "*.txt"],
    },
    zip_safe=False,
)
