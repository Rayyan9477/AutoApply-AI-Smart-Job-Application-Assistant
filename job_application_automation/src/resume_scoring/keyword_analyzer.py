"""
Keyword analyzer for comparing resumes and job descriptions.
"""
from typing import Dict, List, Tuple, Set
import logging
from collections import Counter
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)

class KeywordAnalyzer:
    """Analyzer for matching keywords between resumes and job descriptions."""

    def __init__(self):
        """Initialize the keyword analyzer."""
        # Load spaCy model for text analysis
        try:
            self.nlp = spacy.load('en_core_web_md')
        except OSError:
            logger.warning("Downloading spaCy model 'en_core_web_md'...")
            spacy.cli.download('en_core_web_md')
            self.nlp = spacy.load('en_core_web_md')

        # Initialize TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=10000,
            ngram_range=(1, 3)  # Include phrases up to 3 words
        )

        # Common industry terms and phrases to look for
        self.industry_terms = {
            'technical': {
                'api', 'rest', 'soap', 'microservices', 'scalable', 'distributed',
                'cloud', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'ci/cd',
                'agile', 'scrum', 'devops', 'git', 'version control'
            },
            'soft_skills': {
                'leadership', 'communication', 'teamwork', 'problem solving',
                'analytical', 'project management', 'time management',
                'collaboration', 'initiative', 'adaptability'
            },
            'achievements': {
                'improved', 'increased', 'reduced', 'launched', 'developed',
                'implemented', 'managed', 'led', 'created', 'designed',
                'optimized', 'streamlined', 'automated'
            },
            'metrics': {
                'roi', 'kpi', 'metrics', 'performance', 'efficiency',
                'productivity', 'revenue', 'cost', 'budget', 'growth',
                'reduction', 'improvement', 'impact'
            }
        }

    def analyze_keywords(self,
                      resume_text: str,
                      job_description: str) -> Tuple[float, Dict[str, float]]:
        """Analyze keyword matches between resume and job description.
        
        Args:
            resume_text: Text content of the resume
            job_description: Text content of the job description
            
        Returns:
            Tuple containing:
            - float: Overall keyword match score (0-1)
            - Dict[str, float]: Dictionary of keyword matches and their scores
        """
        # 1. Extract important phrases from job description
        job_phrases = self._extract_important_phrases(job_description)

        # 2. Extract phrases from resume
        resume_phrases = self._extract_important_phrases(resume_text)

        # 3. Calculate TF-IDF similarity
        tfidf_score = self._calculate_tfidf_similarity(resume_text, job_description)

        # 4. Calculate phrase matches
        phrase_matches = {}
        for phrase in job_phrases:
            score = self._calculate_phrase_match_score(phrase, resume_phrases)
            if score > 0:
                phrase_matches[phrase] = score

        # 5. Calculate semantic similarity
        semantic_score = self._calculate_semantic_similarity(resume_text, job_description)

        # 6. Calculate industry term coverage
        term_coverage = self._calculate_term_coverage(resume_text, job_description)

        # 7. Combine scores
        weights = {
            'tfidf': 0.3,
            'phrase': 0.3,
            'semantic': 0.2,
            'term_coverage': 0.2
        }

        overall_score = (
            weights['tfidf'] * tfidf_score +
            weights['phrase'] * (sum(phrase_matches.values()) / max(len(job_phrases), 1)) +
            weights['semantic'] * semantic_score +
            weights['term_coverage'] * term_coverage
        )

        return overall_score, phrase_matches

    def _extract_important_phrases(self, text: str) -> Set[str]:
        """Extract important phrases from text.
        
        Args:
            text: Text to extract phrases from
            
        Returns:
            Set[str]: Set of important phrases
        """
        doc = self.nlp(text.lower())
        phrases = set()

        # Extract noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 3:  # Limit to 3 words
                phrases.add(chunk.text)

        # Extract named entities
        for ent in doc.ents:
            if len(ent.text.split()) <= 3:
                phrases.add(ent.text)

        # Extract verb phrases (verb + direct object)
        for token in doc:
            if token.dep_ == 'ROOT' and token.pos_ == 'VERB':
                phrase = token.text
                for child in token.children:
                    if child.dep_ in {'dobj', 'pobj'}:
                        phrase = f"{phrase} {child.text}"
                        phrases.add(phrase)

        # Add industry terms found in text
        for category in self.industry_terms.values():
            for term in category:
                if term in text.lower():
                    phrases.add(term)

        return phrases

    def _calculate_tfidf_similarity(self, text1: str, text2: str) -> float:
        """Calculate TF-IDF similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            float: Similarity score (0-1)
        """
        try:
            # Fit and transform the texts
            tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating TF-IDF similarity: {str(e)}")
            return 0.0

    def _calculate_phrase_match_score(self,
                                  phrase: str,
                                  target_phrases: Set[str]) -> float:
        """Calculate how well a phrase matches against a set of target phrases.
        
        Args:
            phrase: Phrase to match
            target_phrases: Set of phrases to match against
            
        Returns:
            float: Match score (0-1)
        """
        # Direct match
        if phrase in target_phrases:
            return 1.0

        # Try semantic matching
        phrase_doc = self.nlp(phrase)
        max_similarity = 0.0

        for target in target_phrases:
            try:
                target_doc = self.nlp(target)
                similarity = phrase_doc.similarity(target_doc)
                max_similarity = max(max_similarity, similarity)
            except Exception:
                continue

        return max_similarity

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts using spaCy.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            float: Similarity score (0-1)
        """
        try:
            doc1 = self.nlp(text1)
            doc2 = self.nlp(text2)
            return doc1.similarity(doc2)
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {str(e)}")
            return 0.0

    def _calculate_term_coverage(self, resume_text: str, job_description: str) -> float:
        """Calculate coverage of industry terms.
        
        Args:
            resume_text: Resume text
            job_description: Job description text
            
        Returns:
            float: Coverage score (0-1)
        """
        resume_text = resume_text.lower()
        job_description = job_description.lower()

        # Find terms present in job description
        relevant_terms = set()
        for category in self.industry_terms.values():
            for term in category:
                if term in job_description:
                    relevant_terms.add(term)

        if not relevant_terms:
            return 1.0  # No relevant terms to match

        # Count matches in resume
        matches = sum(1 for term in relevant_terms if term in resume_text)
        return matches / len(relevant_terms)

    def get_missing_keywords(self,
                         resume_text: str,
                         job_description: str,
                         threshold: float = 0.3) -> List[str]:
        """Get important keywords from job description missing in resume.
        
        Args:
            resume_text: Resume text
            job_description: Job description text
            threshold: Importance threshold for keywords
            
        Returns:
            List[str]: List of important missing keywords
        """
        # Get important phrases from job description
        job_phrases = self._extract_important_phrases(job_description)
        
        # Get phrases from resume
        resume_phrases = self._extract_important_phrases(resume_text)
        
        # Find missing important phrases
        missing = []
        for phrase in job_phrases:
            if (phrase not in resume_phrases and
                self._calculate_phrase_match_score(phrase, resume_phrases) < threshold):
                missing.append(phrase)
        
        return missing

    def suggest_keyword_improvements(self,
                                resume_text: str,
                                job_description: str) -> List[str]:
        """Suggest improvements for keyword usage in resume.
        
        Args:
            resume_text: Resume text
            job_description: Job description text
            
        Returns:
            List[str]: List of improvement suggestions
        """
        suggestions = []
        
        # Get missing keywords
        missing = self.get_missing_keywords(resume_text, job_description)
        
        if missing:
            suggestions.append(
                f"Consider adding these keywords: {', '.join(missing[:5])}"
            )
        
        # Check industry term coverage
        term_coverage = self._calculate_term_coverage(resume_text, job_description)
        if term_coverage < 0.7:
            # Find missing industry terms
            for category, terms in self.industry_terms.items():
                relevant_terms = [
                    term for term in terms
                    if term in job_description.lower() and term not in resume_text.lower()
                ]
                if relevant_terms:
                    suggestions.append(
                        f"Add {category.replace('_', ' ')} terms: {', '.join(relevant_terms)}"
                    )
        
        # Check achievement verbs
        if not any(verb in resume_text.lower() 
                  for verb in self.industry_terms['achievements']):
            suggestions.append(
                "Use more achievement-oriented verbs (e.g., improved, increased, developed)"
            )
        
        # Check metrics
        if not any(metric in resume_text.lower() 
                  for metric in self.industry_terms['metrics']):
            suggestions.append(
                "Include more quantifiable metrics and results"
            )
        
        return suggestions 