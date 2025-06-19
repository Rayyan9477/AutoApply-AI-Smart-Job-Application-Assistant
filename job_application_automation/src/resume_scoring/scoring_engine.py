"""
Resume scoring engine for evaluating resume-job compatibility.
"""
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .skill_matcher import SkillMatcher
from .keyword_analyzer import KeywordAnalyzer
from .experience_analyzer import ExperienceAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class ScoringWeights:
    """Weights for different scoring components."""
    skills: float = 0.4
    experience: float = 0.3
    education: float = 0.2
    keywords: float = 0.1

@dataclass
class ScoreDetails:
    """Detailed scoring information."""
    overall_score: float
    skill_score: float
    experience_score: float
    education_score: float
    keyword_score: float
    missing_required_skills: List[str]
    missing_preferred_skills: List[str]
    keyword_matches: Dict[str, float]
    experience_matches: List[Dict[str, Any]]
    education_matches: List[Dict[str, Any]]
    improvement_suggestions: List[str]

class ResumeScorer:
    """Engine for scoring resumes against job descriptions."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the resume scorer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.weights = ScoringWeights(
            **config.get('job_matching', {}).get('weights', {})
        )
        
        # Initialize analyzers
        self.skill_matcher = SkillMatcher()
        self.keyword_analyzer = KeywordAnalyzer()
        self.experience_analyzer = ExperienceAnalyzer()
        
        # Initialize TF-IDF vectorizer for semantic matching
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=10000,
            ngram_range=(1, 2)
        )

    def score_resume(self,
                    resume_text: str,
                    job_description: str,
                    candidate_profile: Dict[str, Any],
                    job_metadata: Dict[str, Any]) -> ScoreDetails:
        """Score a resume against a job description.
        
        Args:
            resume_text: Text content of the resume
            job_description: Text content of the job description
            candidate_profile: Dictionary containing candidate information
            job_metadata: Dictionary containing job metadata
            
        Returns:
            ScoreDetails: Detailed scoring information
        """
        # 1. Skill Matching
        skill_score, missing_required, missing_preferred = self._score_skills(
            candidate_profile.get('skills', []),
            job_metadata.get('required_skills', []),
            job_metadata.get('preferred_skills', [])
        )

        # 2. Experience Matching
        experience_score, experience_matches = self._score_experience(
            candidate_profile.get('experience', []),
            job_description,
            job_metadata
        )

        # 3. Education Matching
        education_score, education_matches = self._score_education(
            candidate_profile.get('education', []),
            job_description,
            job_metadata
        )

        # 4. Keyword Matching
        keyword_score, keyword_matches = self._score_keywords(
            resume_text,
            job_description
        )

        # 5. Calculate overall score
        overall_score = (
            self.weights.skills * skill_score +
            self.weights.experience * experience_score +
            self.weights.education * education_score +
            self.weights.keywords * keyword_score
        )

        # 6. Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(
            skill_score,
            experience_score,
            education_score,
            keyword_score,
            missing_required,
            missing_preferred,
            keyword_matches
        )

        return ScoreDetails(
            overall_score=overall_score,
            skill_score=skill_score,
            experience_score=experience_score,
            education_score=education_score,
            keyword_score=keyword_score,
            missing_required_skills=missing_required,
            missing_preferred_skills=missing_preferred,
            keyword_matches=keyword_matches,
            experience_matches=experience_matches,
            education_matches=education_matches,
            improvement_suggestions=suggestions
        )

    def _score_skills(self,
                     candidate_skills: List[str],
                     required_skills: List[str],
                     preferred_skills: List[str]) -> Tuple[float, List[str], List[str]]:
        """Score candidate's skills against job requirements.
        
        Args:
            candidate_skills: List of candidate's skills
            required_skills: List of required skills for the job
            preferred_skills: List of preferred skills for the job
            
        Returns:
            Tuple containing:
            - float: Skill match score (0-1)
            - List[str]: Missing required skills
            - List[str]: Missing preferred skills
        """
        # Convert all skills to lowercase for matching
        candidate_skills = [s.lower() for s in candidate_skills]
        required_skills = [s.lower() for s in required_skills]
        preferred_skills = [s.lower() for s in preferred_skills]

        # Find missing skills
        missing_required = []
        missing_preferred = []
        
        for skill in required_skills:
            if not self.skill_matcher.has_skill(candidate_skills, skill):
                missing_required.append(skill)
                
        for skill in preferred_skills:
            if not self.skill_matcher.has_skill(candidate_skills, skill):
                missing_preferred.append(skill)

        # Calculate scores
        if not required_skills and not preferred_skills:
            return 1.0, missing_required, missing_preferred

        required_weight = 0.7
        preferred_weight = 0.3

        if required_skills:
            required_score = (len(required_skills) - len(missing_required)) / len(required_skills)
        else:
            required_score = 1.0
            required_weight = 0
            preferred_weight = 1.0

        if preferred_skills:
            preferred_score = (len(preferred_skills) - len(missing_preferred)) / len(preferred_skills)
        else:
            preferred_score = 1.0
            if not required_skills:
                return 1.0, missing_required, missing_preferred

        total_score = (required_weight * required_score) + (preferred_weight * preferred_score)
        return total_score, missing_required, missing_preferred

    def _score_experience(self,
                         candidate_experience: List[Dict[str, Any]],
                         job_description: str,
                         job_metadata: Dict[str, Any]) -> Tuple[float, List[Dict[str, Any]]]:
        """Score candidate's experience against job requirements.
        
        Args:
            candidate_experience: List of candidate's experience entries
            job_description: Job description text
            job_metadata: Job metadata dictionary
            
        Returns:
            Tuple containing:
            - float: Experience match score (0-1)
            - List[Dict]: List of experience matches with scores
        """
        return self.experience_analyzer.analyze_experience(
            candidate_experience,
            job_description,
            job_metadata
        )

    def _score_education(self,
                        candidate_education: List[Dict[str, Any]],
                        job_description: str,
                        job_metadata: Dict[str, Any]) -> Tuple[float, List[Dict[str, Any]]]:
        """Score candidate's education against job requirements.
        
        Args:
            candidate_education: List of candidate's education entries
            job_description: Job description text
            job_metadata: Job metadata dictionary
            
        Returns:
            Tuple containing:
            - float: Education match score (0-1)
            - List[Dict]: List of education matches with scores
        """
        # Extract education requirements from job description
        required_degree_level = self._extract_required_education(
            job_description,
            job_metadata
        )

        # Score each education entry
        matches = []
        max_score = 0.0

        for edu in candidate_education:
            degree = edu.get('degree', '').lower()
            score = self._calculate_education_score(degree, required_degree_level)
            matches.append({
                'degree': edu.get('degree'),
                'score': score,
                'matches_requirement': score >= 0.8
            })
            max_score = max(max_score, score)

        return max_score, matches

    def _score_keywords(self,
                       resume_text: str,
                       job_description: str) -> Tuple[float, Dict[str, float]]:
        """Score keyword matches between resume and job description.
        
        Args:
            resume_text: Text content of the resume
            job_description: Job description text
            
        Returns:
            Tuple containing:
            - float: Keyword match score (0-1)
            - Dict[str, float]: Dictionary of keyword matches and their scores
        """
        return self.keyword_analyzer.analyze_keywords(resume_text, job_description)

    def _extract_required_education(self,
                                job_description: str,
                                job_metadata: Dict[str, Any]) -> str:
        """Extract required education level from job description.
        
        Args:
            job_description: Job description text
            job_metadata: Job metadata dictionary
            
        Returns:
            str: Required education level
        """
        # First check metadata
        if 'required_education' in job_metadata:
            return job_metadata['required_education'].lower()

        # Use keyword analysis to find education requirements
        education_keywords = {
            'phd': ['phd', 'doctorate', 'doctoral'],
            'masters': ['masters', "master's", 'ms', 'msc', 'ma'],
            'bachelors': ['bachelors', "bachelor's", 'bs', 'ba'],
            'associates': ['associates', "associate's", 'aa', 'as']
        }

        job_description = job_description.lower()
        
        for level, keywords in education_keywords.items():
            for keyword in keywords:
                if keyword in job_description:
                    return level

        return 'high_school'  # Default if no specific requirement found

    def _calculate_education_score(self,
                               candidate_degree: str,
                               required_level: str) -> float:
        """Calculate education score based on degree levels.
        
        Args:
            candidate_degree: Candidate's degree level
            required_level: Required education level
            
        Returns:
            float: Education match score (0-1)
        """
        degree_levels = {
            'high_school': 1,
            'associates': 2,
            'bachelors': 3,
            'masters': 4,
            'phd': 5
        }

        # Determine candidate's level
        candidate_level = 'high_school'  # Default
        for level, keywords in {
            'phd': ['phd', 'doctorate', 'doctoral'],
            'masters': ['masters', "master's", 'ms', 'msc', 'ma'],
            'bachelors': ['bachelors', "bachelor's", 'bs', 'ba'],
            'associates': ['associates', "associate's", 'aa', 'as']
        }.items():
            if any(kw in candidate_degree.lower() for kw in keywords):
                candidate_level = level
                break

        candidate_value = degree_levels[candidate_level]
        required_value = degree_levels[required_level]

        if candidate_value >= required_value:
            return 1.0
        else:
            # Partial credit for being close
            diff = required_value - candidate_value
            return max(0.0, 1.0 - (diff * 0.25))

    def _generate_improvement_suggestions(self,
                                     skill_score: float,
                                     experience_score: float,
                                     education_score: float,
                                     keyword_score: float,
                                     missing_required: List[str],
                                     missing_preferred: List[str],
                                     keyword_matches: Dict[str, float]) -> List[str]:
        """Generate suggestions for improving the resume.
        
        Args:
            skill_score: Skill match score
            experience_score: Experience match score
            education_score: Education match score
            keyword_score: Keyword match score
            missing_required: List of missing required skills
            missing_preferred: List of missing preferred skills
            keyword_matches: Dictionary of keyword matches and scores
            
        Returns:
            List[str]: List of improvement suggestions
        """
        suggestions = []

        # Skill suggestions
        if missing_required:
            suggestions.append(
                f"Add these required skills to your resume: {', '.join(missing_required)}"
            )
        if missing_preferred:
            suggestions.append(
                f"Consider adding these preferred skills: {', '.join(missing_preferred)}"
            )

        # Experience suggestions
        if experience_score < 0.7:
            suggestions.append(
                "Highlight more relevant experience that matches the job requirements"
            )

        # Education suggestions
        if education_score < 0.7:
            suggestions.append(
                "Your education level might be below the job requirements"
            )

        # Keyword suggestions
        if keyword_score < 0.7:
            # Find important keywords with low scores
            weak_keywords = [
                k for k, v in keyword_matches.items()
                if v < 0.5 and len(k.split()) <= 2  # Only suggest short phrases
            ][:5]  # Limit to top 5 suggestions
            
            if weak_keywords:
                suggestions.append(
                    f"Try incorporating these keywords more prominently: {', '.join(weak_keywords)}"
                )

        return suggestions 