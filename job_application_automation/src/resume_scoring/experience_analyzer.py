"""
Experience analyzer for evaluating candidate experience against job requirements.
"""
from typing import Dict, List, Any, Tuple
import re
import logging
from datetime import datetime
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dateutil import parser as date_parser
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("Spacy model not found. Using basic text processing.")
    nlp = None

class ExperienceAnalyzer:
    """Analyzes candidate experience against job requirements."""

    def __init__(self):
        """Initialize the experience analyzer."""
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=10000,
            ngram_range=(1, 2)
        )
        
        # Common experience-related terms
        self.experience_terms = {
            'leadership': ['lead', 'manage', 'direct', 'oversee', 'supervise', 'head'],
            'technical': ['develop', 'implement', 'architect', 'code', 'program', 'design'],
            'project': ['deliver', 'coordinate', 'plan', 'execute', 'launch'],
            'collaboration': ['collaborate', 'partner', 'work with', 'cross-functional'],
            'achievement': ['improve', 'increase', 'reduce', 'optimize', 'enhance']
        }

    def analyze_experience(self,
                         candidate_experience: List[Dict[str, Any]],
                         job_description: str,
                         job_metadata: Dict[str, Any]) -> Tuple[float, List[Dict[str, Any]]]:
        """Analyze candidate experience against job requirements.
        
        Args:
            candidate_experience: List of candidate's experience entries
            job_description: Job description text
            job_metadata: Job metadata including requirements
            
        Returns:
            Tuple containing:
            - float: Experience match score (0-1)
            - List[Dict]: List of experience matches with scores
        """
        if not candidate_experience:
            return 0.0, []

        # Extract required years and key responsibilities
        required_years = self._extract_required_years(job_description, job_metadata)
        key_responsibilities = self._extract_key_responsibilities(job_description)
        
        # Calculate total relevant experience years
        total_years = self._calculate_total_years(candidate_experience)
        years_score = min(1.0, total_years / required_years) if required_years > 0 else 1.0
        
        # Analyze each experience entry
        experience_matches = []
        total_relevance_score = 0.0
        
        for exp in candidate_experience:
            # Calculate semantic similarity between experience and job requirements
            relevance_score = self._calculate_relevance_score(
                exp.get('description', ''),
                job_description,
                key_responsibilities
            )
            
            # Calculate years for this experience
            years = self._calculate_experience_years(exp)
            
            # Calculate achievement score
            achievement_score = self._calculate_achievement_score(exp.get('description', ''))
            
            # Calculate skill match score
            skill_match_score = self._calculate_skill_match_score(
                exp.get('description', ''),
                job_metadata.get('required_skills', [])
            )
            
            # Calculate weighted score for this experience
            weighted_score = (
                0.4 * relevance_score +
                0.3 * skill_match_score +
                0.3 * achievement_score
            )
            
            experience_matches.append({
                'title': exp.get('title', ''),
                'company': exp.get('company', ''),
                'duration': exp.get('duration', ''),
                'years': years,
                'relevance_score': relevance_score,
                'skill_match_score': skill_match_score,
                'achievement_score': achievement_score,
                'weighted_score': weighted_score
            })
            
            total_relevance_score += weighted_score * years
            
        # Calculate final score
        if total_years > 0:
            avg_relevance_score = total_relevance_score / total_years
        else:
            avg_relevance_score = 0.0
            
        final_score = 0.6 * years_score + 0.4 * avg_relevance_score
        
        # Sort matches by weighted score
        experience_matches.sort(key=lambda x: x['weighted_score'], reverse=True)
        
        return final_score, experience_matches

    def _extract_required_years(self,
                              job_description: str,
                              job_metadata: Dict[str, Any]) -> float:
        """Extract required years of experience from job description."""
        # First check metadata
        if 'required_years' in job_metadata:
            return float(job_metadata['required_years'])
            
        # Look for patterns like "X+ years" or "X years of experience"
        patterns = [
            r'(\d+)(?:\+)?\s*(?:-\s*\d+)?\s+years?(?:\s+of)?\s+experience',
            r'(\d+)(?:\+)?\s*(?:-\s*\d+)?\s+years?(?:\s+of)?\s+work\s+experience',
            r'minimum\s+(?:of\s+)?(\d+)(?:\+)?\s+years?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, job_description.lower())
            if match:
                return float(match.group(1))
                
        return 0.0  # Default if no explicit requirement found

    def _extract_key_responsibilities(self, job_description: str) -> List[str]:
        """Extract key responsibilities from job description."""
        responsibilities = []
        
        # Look for responsibility section
        sections = [
            'responsibilities',
            'key responsibilities',
            'duties',
            'what you\'ll do',
            'role description',
            'job duties'
        ]
        
        job_desc_lower = job_description.lower()
        
        # Try to find responsibility section
        for section in sections:
            start_idx = job_desc_lower.find(section)
            if start_idx != -1:
                # Find next section or end
                next_section_idx = float('inf')
                for next_section in ['requirements', 'qualifications', 'skills', 'about us']:
                    idx = job_desc_lower.find(next_section, start_idx + len(section))
                    if idx != -1:
                        next_section_idx = min(next_section_idx, idx)
                
                if next_section_idx == float('inf'):
                    next_section_idx = len(job_description)
                
                # Extract responsibilities section
                resp_section = job_description[start_idx:next_section_idx]
                
                # Extract bullet points or lines
                for line in resp_section.split('\n'):
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('•')):
                        responsibilities.append(line.strip('- •').strip())
                
                break
        
        # If no structured list found, try NLP extraction
        if not responsibilities and nlp:
            doc = nlp(job_description)
            for sent in doc.sents:
                # Look for action verbs at start of sentence
                if any(token.pos_ == 'VERB' for token in list(sent)[:2]):
                    responsibilities.append(sent.text.strip())
        
        return responsibilities

    def _calculate_total_years(self, experiences: List[Dict[str, Any]]) -> float:
        """Calculate total years of relevant experience."""
        total_years = 0.0
        
        for exp in experiences:
            years = self._calculate_experience_years(exp)
            total_years += years
            
        return total_years

    def _calculate_experience_years(self, experience: Dict[str, Any]) -> float:
        """Calculate years for a single experience entry, robust to various date formats."""
        try:
            duration = experience.get('duration', '')
            if not duration:
                return 0.0
            parts = [p.strip() for p in re.split(r'-|to', duration)]
            if len(parts) != 2:
                return 0.0
            start_str, end_str = parts
            try:
                start_date = date_parser.parse(start_str, fuzzy=True)
            except Exception:
                return 0.0
            if end_str.lower() in ['present', 'current', 'now']:
                end_date = datetime.now()
            else:
                try:
                    end_date = date_parser.parse(end_str, fuzzy=True)
                except Exception:
                    return 0.0
            years = (end_date - start_date).days / 365.25
            return max(0.0, years)
        except Exception:
            return 0.0

    def _calculate_relevance_score(self,
                                 experience_description: str,
                                 job_description: str,
                                 key_responsibilities: List[str]) -> float:
        """Calculate relevance score between experience and job requirements."""
        if not experience_description or not job_description:
            return 0.0
        try:
            texts = [experience_description, job_description]
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except:
            similarity = 0.0
        resp_score = 0.0
        if key_responsibilities:
            matched_resp = self._fuzzy_match(experience_description, key_responsibilities)
            resp_score = matched_resp / len(key_responsibilities)
        return 0.7 * similarity + 0.3 * resp_score

    def _fuzzy_match(self, text: str, keywords: List[str], threshold: int = 80) -> int:
        """Count fuzzy matches above a threshold using fuzzywuzzy."""
        count = 0
        for kw in keywords:
            if fuzz.partial_ratio(kw.lower(), text.lower()) >= threshold:
                count += 1
        return count

    def _calculate_achievement_score(self, description: str) -> float:
        """Calculate achievement score based on impact statements."""
        if not description:
            return 0.0
            
        description_lower = description.lower()
        achievement_count = 0
        
        # Look for achievement indicators
        for terms in self.experience_terms['achievement']:
            if terms in description_lower:
                achievement_count += 1
                
        # Look for metrics/numbers
        metrics_patterns = [
            r'\d+%',  # Percentage
            r'\$\d+',  # Money
            r'\d+x',  # Multiplier
            r'increased|decreased|reduced|improved|optimized|enhanced'  # Impact verbs
        ]
        
        for pattern in metrics_patterns:
            if re.search(pattern, description_lower):
                achievement_count += 1
                
        return min(1.0, achievement_count / 5)  # Cap at 1.0

    def _calculate_skill_match_score(self,
                                   description: str,
                                   required_skills: List[str]) -> float:
        """Calculate skill match score using fuzzy matching."""
        if not description or not required_skills:
            return 0.0
        matched_skills = self._fuzzy_match(description, required_skills)
        return matched_skills / len(required_skills) if required_skills else 0.0 