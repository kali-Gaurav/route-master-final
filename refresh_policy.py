"""
Smart Refresh Strategy for Living Dataset

Implements intelligent refresh policy:
- New trains → fetch once
- <7 days → use cache
- 7-30 days → refresh if requested
- >30 days → force refresh
- Not found → mark INACTIVE
- Unknown → retry periodically

Optimizes API usage while maintaining data freshness
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

from config import REFRESH_POLICY
from logger import logger, LoggerFactory
from database_manager import TrainStatus

logger = LoggerFactory.get_logger("refresh_policy")


class RefreshPriority(Enum):
    """Refresh priority levels"""
    SKIP = 0              # Skip refresh
    LOW = 1               # Refetch if time permits
    MEDIUM = 2            # Include in regular refresh
    HIGH = 3              # Prioritize this refresh
    CRITICAL = 4          # Force refresh immediately


class RefreshDecision:
    """Result of refresh decision"""
    
    def __init__(self, train_no: str, should_refresh: bool, priority: RefreshPriority,
                 reason: str, cache_age_days: Optional[float] = None):
        self.train_no = train_no
        self.should_refresh = should_refresh
        self.priority = priority
        self.reason = reason
        self.cache_age_days = cache_age_days
    
    def __repr__(self):
        return f"<RefreshDecision {self.train_no}: {self.should_refresh} ({self.priority.name})>"


class RefreshPolicyEngine:
    """
    Main refresh policy engine
    Decides which trains to refresh and when
    """
    
    def __init__(self):
        self.logger = LoggerFactory.get_logger("refresh_engine")
        self.cache_valid_days = REFRESH_POLICY["cache_valid_days"]
        self.refresh_after_days = REFRESH_POLICY["refresh_after_days"]
        self.unknown_check_days = REFRESH_POLICY["unknown_train_check_days"]
        self.inactive_cleanup_days = REFRESH_POLICY["inactive_train_cleanup_days"]
    
    def decide_refresh(self, train_no: str, current_status: TrainStatus,
                      last_updated: Optional[datetime] = None,
                      last_fetched: Optional[datetime] = None,
                      is_frequently_searched: bool = False) -> RefreshDecision:
        """
        Decide whether a train should be refreshed
        
        Args:
            train_no: Train number
            current_status: Current train status (ACTIVE, INACTIVE, UNKNOWN)
            last_updated: When data was last updated
            last_fetched: When data was last fetched
            is_frequently_searched: If train is frequently searched
        
        Returns:
            RefreshDecision object
        """
        now = datetime.utcnow()
        
        # Case 1: Unknown status - need to validate
        if current_status == TrainStatus.UNKNOWN:
            if last_fetched is None:
                return RefreshDecision(
                    train_no, True, RefreshPriority.HIGH,
                    "Never fetched - initial validation needed"
                )
            
            days_since_fetch = (now - last_fetched).days
            if days_since_fetch >= self.unknown_check_days:
                return RefreshDecision(
                    train_no, True, RefreshPriority.MEDIUM,
                    f"Unknown train - recheck after {self.unknown_check_days} days",
                    cache_age_days=days_since_fetch
                )
            
            return RefreshDecision(
                train_no, False, RefreshPriority.SKIP,
                f"Unknown train - recheck in {self.unknown_check_days - days_since_fetch} days",
                cache_age_days=days_since_fetch
            )
        
        # Case 2: Inactive status - periodic cleanup check
        if current_status == TrainStatus.INACTIVE:
            if last_fetched is None:
                return RefreshDecision(
                    train_no, True, RefreshPriority.LOW,
                    "Inactive train - verify status"
                )
            
            days_since_fetch = (now - last_fetched).days
            if days_since_fetch >= self.inactive_cleanup_days:
                return RefreshDecision(
                    train_no, True, RefreshPriority.LOW,
                    f"Inactive train - recheck after {self.inactive_cleanup_days} days",
                    cache_age_days=days_since_fetch
                )
            
            return RefreshDecision(
                train_no, False, RefreshPriority.SKIP,
                "Inactive train - no refresh needed",
                cache_age_days=days_since_fetch if last_fetched else None
            )
        
        # Case 3: Active status - standard refresh policy
        if current_status == TrainStatus.ACTIVE:
            if last_fetched is None:
                return RefreshDecision(
                    train_no, False, RefreshPriority.SKIP,
                    "Active train - use existing data"
                )
            
            days_since_fetch = (now - last_fetched).days
            
            # Cache still valid
            if days_since_fetch < self.cache_valid_days:
                if is_frequently_searched:
                    # Frequently searched trains get refresh nudge
                    return RefreshDecision(
                        train_no, False, RefreshPriority.LOW,
                        f"Cache valid ({days_since_fetch}d) - frequently searched",
                        cache_age_days=days_since_fetch
                    )
                
                return RefreshDecision(
                    train_no, False, RefreshPriority.SKIP,
                    f"Cache valid ({days_since_fetch}d < {self.cache_valid_days}d)",
                    cache_age_days=days_since_fetch
                )
            
            # Cache acceptable but aging
            if days_since_fetch < self.refresh_after_days:
                return RefreshDecision(
                    train_no, False, RefreshPriority.LOW,
                    f"Cache aging ({days_since_fetch}d) - refresh if available",
                    cache_age_days=days_since_fetch
                )
            
            # Cache expired - force refresh
            return RefreshDecision(
                train_no, True, RefreshPriority.HIGH,
                f"Cache expired ({days_since_fetch}d > {self.refresh_after_days}d)",
                cache_age_days=days_since_fetch
            )
        
        # Case 4: Suspended status
        if current_status == TrainStatus.SUSPENDED:
            return RefreshDecision(
                train_no, False, RefreshPriority.SKIP,
                "Train suspended - no refresh needed"
            )
        
        # Case 5: Deprecated status
        if current_status == TrainStatus.DEPRECATED:
            return RefreshDecision(
                train_no, False, RefreshPriority.SKIP,
                "Train deprecated - no refresh needed"
            )
        
        return RefreshDecision(
            train_no, False, RefreshPriority.SKIP,
            "Unknown status"
        )
    
    def batch_refresh_decisions(self, trains: List[Dict]) -> Dict[str, RefreshDecision]:
        """
        Get refresh decisions for multiple trains
        
        Args:
            trains: List of train dicts with status, last_updated, etc.
        
        Returns:
            Dict mapping train_no -> RefreshDecision
        """
        decisions = {}
        
        for train in trains:
            decision = self.decide_refresh(
                train_no=train.get("train_no"),
                current_status=TrainStatus(train.get("status", "UNKNOWN")),
                last_updated=train.get("last_updated"),
                last_fetched=train.get("last_fetched"),
                is_frequently_searched=train.get("is_frequently_searched", False)
            )
            decisions[train["train_no"]] = decision
        
        return decisions
    
    def prioritize_refresh_batch(self, decisions: Dict[str, RefreshDecision]) -> List[str]:
        """
        Sort trains by refresh priority
        
        Args:
            decisions: Dict of refresh decisions
        
        Returns:
            Sorted list of train numbers (highest priority first)
        """
        # Filter trains that need refresh
        to_refresh = [
            (train_no, decision) 
            for train_no, decision in decisions.items() 
            if decision.should_refresh
        ]
        
        # Sort by priority (higher priority first)
        to_refresh.sort(key=lambda x: x[1].priority.value, reverse=True)
        
        return [train_no for train_no, _ in to_refresh]
    
    def estimate_api_calls(self, decisions: Dict[str, RefreshDecision]) -> Dict[str, int]:
        """
        Estimate API calls by priority
        
        Args:
            decisions: Dict of refresh decisions
        
        Returns:
            Count by priority level
        """
        counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "SKIP": 0
        }
        
        for decision in decisions.values():
            counts[decision.priority.name] += 1
        
        return counts
    
    def generate_refresh_report(self, decisions: Dict[str, RefreshDecision]) -> str:
        """Generate human-readable refresh report"""
        estimate = self.estimate_api_calls(decisions)
        
        total_trains = len(decisions)
        needs_refresh = sum(1 for d in decisions.values() if d.should_refresh)
        
        report = f"""
REFRESH POLICY REPORT
=====================
Total Trains: {total_trains}
Needs Refresh: {needs_refresh} ({needs_refresh*100//total_trains}%)

Priority Breakdown:
  CRITICAL: {estimate['CRITICAL']}
  HIGH:     {estimate['HIGH']}
  MEDIUM:   {estimate['MEDIUM']}
  LOW:      {estimate['LOW']}
  SKIP:     {estimate['SKIP']}

Configuration:
  Cache Valid:  {self.cache_valid_days} days
  Refresh After: {self.refresh_after_days} days
  Unknown Check: {self.unknown_check_days} days
  Inactive Cleanup: {self.inactive_cleanup_days} days
"""
        return report


# Global engine instance
refresh_engine = RefreshPolicyEngine()


def should_refresh_train(train_no: str, current_status: TrainStatus,
                        last_fetched: Optional[datetime] = None,
                        is_frequently_searched: bool = False) -> bool:
    """
    Convenience function to check if train should be refreshed
    
    Args:
        train_no: Train number
        current_status: Current status
        last_fetched: When last fetched
        is_frequently_searched: If frequently searched
    
    Returns:
        True if should refresh
    """
    decision = refresh_engine.decide_refresh(
        train_no, current_status,
        last_fetched=last_fetched,
        is_frequently_searched=is_frequently_searched
    )
    return decision.should_refresh
