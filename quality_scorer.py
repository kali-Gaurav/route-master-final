"""
Quality Scoring System

Assigns freshness scores to datasets:
- <7 days = 100% fresh
- 7-14 days = 80% fresh
- 14-30 days = 60% fresh
- >30 days = 40% fresh

Scores drive routing decisions and refresh priorities
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics

from config import QUALITY_SCORING
from logger import LoggerFactory

logger = LoggerFactory.get_logger("quality_scorer")


@dataclass
class QualityScore:
    """Quality score for a dataset"""
    train_no: str
    freshness_score: float  # 0-100
    completeness_score: float  # 0-100
    validation_score: float  # 0-100
    overall_score: float  # Weighted average
    last_update_age_days: float
    data_quality_grade: str  # A, B, C, D, F
    recommendations: List[str]


class QualityScorer:
    """Calculate data quality scores"""
    
    def __init__(self):
        self.logger = LoggerFactory.get_logger("quality_scorer")
        self.config = QUALITY_SCORING
    
    def calculate_freshness_score(self, last_updated: Optional[datetime]) -> float:
        """
        Calculate freshness score based on age
        
        Returns:
            0-100 score
        """
        if last_updated is None:
            return 0.0
        
        age_days = (datetime.utcnow() - last_updated).days
        fresh_threshold = self.config.get("fresh_threshold_days", 7)
        acceptable_threshold = self.config.get("acceptable_threshold_days", 14)
        warning_threshold = self.config.get("warning_threshold_days", 30)
        critical_threshold = self.config.get("critical_threshold_days", 90)
        
        if age_days <= fresh_threshold:
            return 100.0
        elif age_days <= acceptable_threshold:
            # Linear interpolation: 100% at 7d, 80% at 14d
            return 100.0 - (age_days - fresh_threshold) / (acceptable_threshold - fresh_threshold) * 20
        elif age_days <= warning_threshold:
            # Linear: 80% at 14d, 60% at 30d
            return 80.0 - (age_days - acceptable_threshold) / (warning_threshold - acceptable_threshold) * 20
        elif age_days <= critical_threshold:
            # Linear: 60% at 30d, 40% at 90d
            return 60.0 - (age_days - warning_threshold) / (critical_threshold - warning_threshold) * 20
        else:
            # Below 40% after 90 days
            return max(0.0, 40.0 - (age_days - critical_threshold) / 30)
    
    def calculate_completeness_score(self, data: Dict,
                                    required_fields: List[str]) -> float:
        """
        Calculate completeness score
        
        Args:
            data: Data dictionary to check
            required_fields: List of required fields
        
        Returns:
            0-100 score
        """
        if not required_fields:
            return 100.0
        
        found = 0
        for field in required_fields:
            if field in data and data[field] is not None:
                found += 1
        
        return (found / len(required_fields)) * 100
    
    def calculate_validation_score(self, validation_errors: int,
                                  validation_warnings: int,
                                  total_records: int) -> float:
        """
        Calculate validation score based on errors and warnings
        
        Returns:
            0-100 score
        """
        # Errors are worse than warnings
        error_impact = validation_errors * 10
        warning_impact = validation_warnings * 2
        
        # Normalize to 0-100
        max_impact = total_records * 100
        impact = min(error_impact + warning_impact, max_impact)
        
        return max(0.0, 100.0 - (impact / max_impact) * 100)
    
    def calculate_overall_score(self, freshness: float,
                               completeness: float,
                               validation: float) -> float:
        """
        Calculate weighted overall score
        
        Weights:
        - Freshness: 50% (most important)
        - Completeness: 30%
        - Validation: 20%
        """
        return (freshness * 0.5) + (completeness * 0.3) + (validation * 0.2)
    
    def get_quality_grade(self, overall_score: float) -> str:
        """
        Convert score to letter grade
        
        Returns:
            A, B, C, D, or F
        """
        if overall_score >= 90:
            return "A"
        elif overall_score >= 80:
            return "B"
        elif overall_score >= 70:
            return "C"
        elif overall_score >= 60:
            return "D"
        else:
            return "F"
    
    def score_train(self, train: Dict) -> QualityScore:
        """
        Calculate complete quality score for a train
        
        Args:
            train: Train data dictionary
        
        Returns:
            QualityScore object
        """
        train_no = train.get("train_no", "UNKNOWN")
        last_updated = train.get("last_updated")
        
        # Calculate component scores
        freshness_score = self.calculate_freshness_score(last_updated)
        
        required_fields = ["train_no", "train_name", "status"]
        completeness_score = self.calculate_completeness_score(train, required_fields)
        
        validation_errors = train.get("validation_errors", 0)
        validation_warnings = train.get("validation_warnings", 0)
        validation_score = self.calculate_validation_score(
            validation_errors, validation_warnings, 1
        )
        
        # Calculate overall
        overall_score = self.calculate_overall_score(
            freshness_score, completeness_score, validation_score
        )
        
        grade = self.get_quality_grade(overall_score)
        
        # Calculate age
        age_days = (datetime.utcnow() - last_updated).days if last_updated else 999
        
        # Recommendations
        recommendations = []
        if freshness_score < 80:
            recommendations.append("Data is aging - consider refresh")
        if completeness_score < 90:
            recommendations.append("Missing fields - check data source")
        if validation_score < 80:
            recommendations.append("Validation issues detected - review report")
        if overall_score < 60:
            recommendations.append("Overall quality poor - do not use for routing")
        
        return QualityScore(
            train_no=train_no,
            freshness_score=freshness_score,
            completeness_score=completeness_score,
            validation_score=validation_score,
            overall_score=overall_score,
            last_update_age_days=age_days,
            data_quality_grade=grade,
            recommendations=recommendations
        )
    
    def score_batch(self, trains: List[Dict]) -> List[QualityScore]:
        """Score multiple trains"""
        return [self.score_train(train) for train in trains]
    
    def calculate_dataset_quality_metrics(self, scores: List[QualityScore]) -> Dict:
        """
        Calculate overall dataset quality metrics
        
        Returns:
            Dictionary with aggregate metrics
        """
        if not scores:
            return {
                "total_trains": 0,
                "avg_freshness": 0,
                "avg_completeness": 0,
                "avg_validation": 0,
                "avg_overall": 0,
                "grade_distribution": {}
            }
        
        freshness_scores = [s.freshness_score for s in scores]
        completeness_scores = [s.completeness_score for s in scores]
        validation_scores = [s.validation_score for s in scores]
        overall_scores = [s.overall_score for s in scores]
        
        # Grade distribution
        grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for score in scores:
            grade_counts[score.data_quality_grade] += 1
        
        return {
            "total_trains": len(scores),
            "avg_freshness": statistics.mean(freshness_scores),
            "avg_completeness": statistics.mean(completeness_scores),
            "avg_validation": statistics.mean(validation_scores),
            "avg_overall": statistics.mean(overall_scores),
            "median_overall": statistics.median(overall_scores),
            "min_overall": min(overall_scores),
            "max_overall": max(overall_scores),
            "grade_distribution": grade_counts,
            "percent_grade_a": (grade_counts["A"] / len(scores)) * 100,
            "percent_grade_b": (grade_counts["B"] / len(scores)) * 100,
            "percent_grade_c": (grade_counts["C"] / len(scores)) * 100,
        }


# Global scorer instance
scorer = QualityScorer()
