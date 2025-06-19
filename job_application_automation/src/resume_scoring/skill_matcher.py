"""
Skill matching engine for analyzing and comparing skills.
"""
from typing import List, Dict, Set, Optional
import logging
from difflib import SequenceMatcher
import spacy
from spacy.tokens import Doc
import numpy as np

logger = logging.getLogger(__name__)

class SkillMatcher:
    """Engine for matching and analyzing skills."""

    def __init__(self):
        """Initialize the skill matcher."""
        # Load spaCy model for text analysis
        try:
            self.nlp = spacy.load('en_core_web_md')
        except OSError:
            logger.warning("Downloading spaCy model 'en_core_web_md'...")
            spacy.cli.download('en_core_web_md')
            self.nlp = spacy.load('en_core_web_md')

        # Common skill variations and abbreviations
        self.skill_variations = {
            'javascript': {'js', 'ecmascript', 'node.js', 'nodejs'},
            'python': {'py', 'python3', 'python2'},
            'java': {'j2ee', 'jvm', 'java8', 'java11'},
            'c++': {'cpp', 'c plus plus'},
            'c#': {'csharp', 'c sharp', 'dotnet', '.net'},
            'machine learning': {'ml', 'deep learning', 'ai'},
            'artificial intelligence': {'ai', 'machine learning', 'deep learning'},
            'amazon web services': {'aws'},
            'microsoft azure': {'azure'},
            'google cloud platform': {'gcp', 'google cloud'},
            'sql': {'mysql', 'postgresql', 'oracle', 'tsql', 't-sql'},
            'react': {'reactjs', 'react.js'},
            'vue': {'vuejs', 'vue.js'},
            'angular': {'angularjs', 'angular2+'},
            'devops': {'devsecops', 'dev ops'},
            'ci/cd': {'cicd', 'continuous integration', 'continuous deployment'},
            'docker': {'containerization', 'containers'},
            'kubernetes': {'k8s', 'container orchestration'},
        }

        # Build reverse mapping for quick lookups
        self.skill_lookup = {}
        for main_skill, variations in self.skill_variations.items():
            self.skill_lookup[main_skill] = main_skill
            for var in variations:
                self.skill_lookup[var] = main_skill

    def has_skill(self, candidate_skills: List[str], required_skill: str) -> bool:
        """Check if a candidate has a required skill or its equivalent.
        
        Args:
            candidate_skills: List of candidate's skills
            required_skill: Required skill to check for
            
        Returns:
            bool: True if the candidate has the skill or equivalent
        """
        required_skill = required_skill.lower()
        candidate_skills = [s.lower() for s in candidate_skills]

        # Direct match
        if required_skill in candidate_skills:
            return True

        # Check normalized versions
        normalized_required = self._normalize_skill(required_skill)
        if any(self._normalize_skill(s) == normalized_required for s in candidate_skills):
            return True

        # Check variations
        if required_skill in self.skill_lookup:
            main_skill = self.skill_lookup[required_skill]
            variations = self.skill_variations[main_skill]
            if any(var in candidate_skills for var in variations):
                return True
            if main_skill in candidate_skills:
                return True

        # Check for fuzzy matches
        if any(self._is_fuzzy_match(required_skill, skill) for skill in candidate_skills):
            return True

        # Check for semantic similarity
        if any(self._is_semantic_match(required_skill, skill) for skill in candidate_skills):
            return True

        return False

    def find_similar_skills(self, skill: str, threshold: float = 0.8) -> List[str]:
        """Find similar skills to a given skill.
        
        Args:
            skill: Skill to find similar skills for
            threshold: Similarity threshold (0-1)
            
        Returns:
            List[str]: List of similar skills
        """
        skill = skill.lower()
        similar_skills = set()

        # Check variations
        normalized = self._normalize_skill(skill)
        if normalized in self.skill_lookup:
            main_skill = self.skill_lookup[normalized]
            similar_skills.update(self.skill_variations[main_skill])
            similar_skills.add(main_skill)

        # Check fuzzy matches
        for main_skill in self.skill_variations:
            if self._is_fuzzy_match(skill, main_skill, threshold):
                similar_skills.add(main_skill)
                similar_skills.update(self.skill_variations[main_skill])

        # Check semantic matches
        skill_doc = self.nlp(skill)
        for main_skill in self.skill_variations:
            if self._calculate_semantic_similarity(skill_doc, main_skill) >= threshold:
                similar_skills.add(main_skill)
                similar_skills.update(self.skill_variations[main_skill])

        return list(similar_skills - {skill})

    def extract_skills(self, text: str) -> Set[str]:
        """Extract skills from text.
        
        Args:
            text: Text to extract skills from
            
        Returns:
            Set[str]: Set of extracted skills
        """
        text = text.lower()
        skills = set()

        # Process text with spaCy
        doc = self.nlp(text)

        # Extract skills using pattern matching
        for main_skill in self.skill_variations:
            if main_skill in text:
                skills.add(main_skill)
            for variation in self.skill_variations[main_skill]:
                if variation in text:
                    skills.add(main_skill)  # Add the main skill, not the variation

        # Extract skills using named entity recognition
        for ent in doc.ents:
            if ent.label_ in {'PRODUCT', 'ORG', 'GPE'}:
                skill = ent.text.lower()
                if skill in self.skill_lookup:
                    skills.add(self.skill_lookup[skill])

        # Extract skills using noun phrases
        for chunk in doc.noun_chunks:
            skill = chunk.text.lower()
            if skill in self.skill_lookup:
                skills.add(self.skill_lookup[skill])

        return skills

    def categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """Categorize skills into different types.
        
        Args:
            skills: List of skills to categorize
            
        Returns:
            Dict[str, List[str]]: Dictionary of skill categories and their skills
        """
        categories = {
            'programming_languages': [],
            'frameworks': [],
            'databases': [],
            'cloud': [],
            'tools': [],
            'soft_skills': [],
            'other': []
        }

        # Define category patterns
        patterns = {
            'programming_languages': {
                'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php',
                'swift', 'kotlin', 'go', 'rust', 'scala', 'perl', 'r'
            },
            'frameworks': {
                'react', 'angular', 'vue', 'django', 'flask', 'spring',
                'express', 'laravel', 'rails', 'asp.net'
            },
            'databases': {
                'sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'redis',
                'cassandra', 'elasticsearch', 'dynamodb'
            },
            'cloud': {
                'aws', 'azure', 'gcp', 'cloud', 'serverless', 'lambda',
                'ec2', 's3', 'kubernetes', 'docker'
            },
            'tools': {
                'git', 'jenkins', 'jira', 'docker', 'kubernetes', 'terraform',
                'ansible', 'maven', 'gradle', 'npm'
            },
            'soft_skills': {
                'leadership', 'communication', 'teamwork', 'problem solving',
                'project management', 'agile', 'scrum'
            }
        }

        for skill in skills:
            skill = skill.lower()
            categorized = False
            
            # Check each category
            for category, category_skills in patterns.items():
                if skill in category_skills:
                    categories[category].append(skill)
                    categorized = True
                    break
                
                # Check variations
                normalized = self._normalize_skill(skill)
                if normalized in self.skill_lookup:
                    main_skill = self.skill_lookup[normalized]
                    if main_skill in category_skills:
                        categories[category].append(skill)
                        categorized = True
                        break

            # If not categorized, add to other
            if not categorized:
                categories['other'].append(skill)

        return categories

    def _normalize_skill(self, skill: str) -> str:
        """Normalize a skill name by removing special characters and spaces.
        
        Args:
            skill: Skill name to normalize
            
        Returns:
            str: Normalized skill name
        """
        return ''.join(c.lower() for c in skill if c.isalnum())

    def _is_fuzzy_match(self,
                     skill1: str,
                     skill2: str,
                     threshold: float = 0.85) -> bool:
        """Check if two skills are fuzzy matches.
        
        Args:
            skill1: First skill
            skill2: Second skill
            threshold: Similarity threshold (0-1)
            
        Returns:
            bool: True if skills are fuzzy matches
        """
        # Normalize skills
        norm1 = self._normalize_skill(skill1)
        norm2 = self._normalize_skill(skill2)

        # Calculate similarity ratio
        ratio = SequenceMatcher(None, norm1, norm2).ratio()
        return ratio >= threshold

    def _is_semantic_match(self,
                        skill1: str,
                        skill2: str,
                        threshold: float = 0.85) -> bool:
        """Check if two skills are semantic matches using spaCy.
        
        Args:
            skill1: First skill
            skill2: Second skill
            threshold: Similarity threshold (0-1)
            
        Returns:
            bool: True if skills are semantic matches
        """
        similarity = self._calculate_semantic_similarity(skill1, skill2)
        return similarity >= threshold

    def _calculate_semantic_similarity(self,
                                  skill1: str | Doc,
                                  skill2: str) -> float:
        """Calculate semantic similarity between two skills.
        
        Args:
            skill1: First skill (or spaCy Doc)
            skill2: Second skill
            
        Returns:
            float: Similarity score (0-1)
        """
        if isinstance(skill1, str):
            doc1 = self.nlp(skill1)
        else:
            doc1 = skill1
        doc2 = self.nlp(skill2)
        
        return doc1.similarity(doc2) 