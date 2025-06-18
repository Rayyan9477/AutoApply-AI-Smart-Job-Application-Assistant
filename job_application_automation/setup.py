from setuptools import setup, find_packages

setup(
    name="job_application_automation",
    version="0.1.0",
    description="Automated job application system with AI-powered resume and cover letter generation",
    author="Rayyan Ahmed",
    author_email="rayyan.a@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "python-dotenv>=0.19.0",
        "pydantic>=1.8.0",
        "loguru>=0.5.3",
        "requests>=2.26.0",
        "beautifulsoup4>=4.10.0",
        "selenium>=4.0.0",
        "webdriver-manager>=3.5.2",
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "python-docx>=0.8.11",
        "python-pptx>=0.6.21",
        "openai>=0.27.0",
        "sentence-transformers>=2.2.0",
        "faiss-cpu>=1.7.0",
        "sqlalchemy>=1.4.0",
        "alembic>=1.7.4",
        "psycopg2-binary>=2.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.5",
            "pytest-cov>=2.12.1",
            "pytest-mock>=3.6.1",
        ]
    },
    entry_points={
        "console_scripts": [
            "job-apply=job_application_automation.main:main",
        ],
    },
)
