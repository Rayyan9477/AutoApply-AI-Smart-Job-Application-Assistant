import pytest
from job_application_automation.src.resume_scoring.experience_analyzer import ExperienceAnalyzer
from datetime import datetime

def make_exp(title, company, duration, description):
    return {
        'title': title,
        'company': company,
        'duration': duration,
        'description': description
    }

def test_basic_experience_match():
    analyzer = ExperienceAnalyzer()
    candidate_experience = [
        make_exp('Software Engineer', 'TechCorp', '2020 - 2023', 'Developed Python applications and led a team.'),
        make_exp('Data Analyst', 'DataCo', '2018 - 2020', 'Analyzed data and improved reporting efficiency by 20%.')
    ]
    job_description = '''
    Responsibilities:
    - Develop software in Python
    - Lead engineering teams
    Requirements:
    - 3+ years of experience
    - Python, leadership
    '''
    job_metadata = {'required_skills': ['Python', 'leadership']}
    score, matches = analyzer.analyze_experience(candidate_experience, job_description, job_metadata)
    assert 0.7 < score <= 1.0
    assert any(m['skill_match_score'] > 0 for m in matches)

def test_fuzzy_skill_matching():
    analyzer = ExperienceAnalyzer()
    candidate_experience = [
        make_exp('ML Engineer', 'AI Inc', '2019 - 2022', 'Worked with Pyhton and led dev teams.'),
    ]
    job_description = 'Looking for Python developers with leadership experience.'
    job_metadata = {'required_skills': ['Python', 'leadership']}
    score, matches = analyzer.analyze_experience(candidate_experience, job_description, job_metadata)
    assert score > 0.5
    assert matches[0]['skill_match_score'] > 0

def test_robust_date_parsing():
    analyzer = ExperienceAnalyzer()
    candidate_experience = [
        make_exp('Consultant', 'Biz', 'Jan 2017 to Mar 2019', 'Consulted on business strategy.'),
        make_exp('Manager', 'Retail', '2015 - Present', 'Managed retail operations.')
    ]
    job_description = 'Requires 5+ years of experience.'
    job_metadata = {}
    score, matches = analyzer.analyze_experience(candidate_experience, job_description, job_metadata)
    # Should parse both date formats and count present as current year
    assert score > 0.5

def test_missing_fields():
    analyzer = ExperienceAnalyzer()
    candidate_experience = [
        {'title': 'Intern', 'company': 'X', 'duration': '', 'description': ''},
    ]
    job_description = 'No requirements.'
    job_metadata = {}
    score, matches = analyzer.analyze_experience(candidate_experience, job_description, job_metadata)
    assert score == 0.0
    assert matches[0]['weighted_score'] == 0.0

def test_edge_case_empty_experience():
    analyzer = ExperienceAnalyzer()
    score, matches = analyzer.analyze_experience([], 'Any job', {})
    assert score == 0.0
    assert matches == []

def test_responsibility_fuzzy_matching():
    analyzer = ExperienceAnalyzer()
    candidate_experience = [
        make_exp('DevOps', 'Cloudy', '2021 - 2023', 'Automated deployments and managed CI/CD pipelines.'),
    ]
    job_description = 'Responsibilities:\n- Automate deployment\n- Manage continuous integration'
    job_metadata = {}
    score, matches = analyzer.analyze_experience(candidate_experience, job_description, job_metadata)
    assert matches[0]['relevance_score'] > 0.3 