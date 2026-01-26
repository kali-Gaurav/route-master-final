"""
COMPLETE ROUTE GENERATION TEST WITH DETAILED REPORTING
Tests all three route categories and generates comprehensive reports

This script:
1. Generates routes between random station pairs
2. Validates all three route categories (direct, single-transfer, multi-transfer)
3. Ensures sufficient routes are generated
4. Displays optimal routes and all routes
5. Shows total routes generated with breakdown
"""

import json
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class RouteCategory:
    """Route category breakdown"""
    name: str
    description: str
    count: int
    min_required: int
    status: str  # "OK" or "WARNING"


@dataclass
class RouteStatistics:
    """Statistics for a route generation session"""
    source: str
    destination: str
    total_routes: int
    direct_routes: int
    single_transfer_routes: int
    multi_transfer_routes: int
    pareto_optimal: int
    generation_time: float
    optimization_time: float


class RouteGenerationTest:
    """Complete route generation test and reporting"""
    
    def __init__(self):
        self.results = []
    
    def validate_route_category_count(self, direct: int, single: int, multi: int) -> Tuple[bool, List[str]]:
        """Validate that sufficient routes exist in each category"""
        issues = []
        
        # Minimum requirements
        min_total = 50  # Should have at least 50 total routes
        min_single = 10  # At least 10 routes with some options
        
        if direct == 0 and single == 0 and multi == 0:
            issues.append("ERROR: No routes generated at all!")
            return False, issues
        
        total = direct + single + multi
        
        if total < min_total:
            issues.append(f"WARNING: Only {total} routes generated (expected ≥ {min_total})")
        
        # Check distribution
        if direct == 0:
            issues.append("WARNING: No direct routes found (may not exist for this pair)")
        
        if single == 0 and multi == 0:
            issues.append("ERROR: No transfer routes found!")
            return False, issues
        
        if single + multi < min_single:
            issues.append(f"WARNING: Only {single + multi} transfer options (expected ≥ {min_single})")
        
        return len([i for i in issues if i.startswith("ERROR")]) == 0, issues
    
    def format_route_for_display(self, route: Dict, category: str) -> str:
        """Format a route for nice display"""
        segments = route.get('segments', [])
        transfers = len(segments) - 1
        
        route_str = "  Route: "
        for i, seg in enumerate(segments):
            route_str += f"{seg.get('from')} → {seg.get('to')}"
            if i < len(segments) - 1:
                route_str += " | TRANSFER | "
        
        route_str += f"\n    • Segments: {len(segments)} trains"
        route_str += f"\n    • Transfers: {transfers}"
        route_str += f"\n    • Total Time: {route.get('totalTime', 0)} min"
        route_str += f"\n    • Total Cost: ₹{route.get('totalCost', 0)}"
        route_str += f"\n    • Seat Probability: {route.get('seatProbability', 0)}%"
        
        return route_str
    
    def test_route_generation(self, source: str, destination: str) -> RouteStatistics:
        """Test complete route generation for a station pair"""
        logger.info(f"\n{'=' * 80}")
        logger.info(f"Testing Route Generation: {source} → {destination}")
        logger.info(f"{'=' * 80}")
        
        try:
            from route_optimizer import ParetoTrainRouter
            from database_manager import DatabaseManager
            import time
            
            db = DatabaseManager()
            router = ParetoTrainRouter(db)
            
            # Generate all routes
            logger.info("\n[Phase 1] Generating all routes...")
            start_time = time.time()
            all_routes = router.generate_all_routes(source, destination, max_transfers=3)
            gen_time = time.time() - start_time
            
            logger.info(f"Generated {len(all_routes)} total routes in {gen_time:.2f}s")
            
            # Count by transfer type
            direct = [r for r in all_routes if len(r) == 1]
            single_transfer = [r for r in all_routes if len(r) == 2]
            multi_transfer = [r for r in all_routes if len(r) >= 3]
            
            logger.info(f"\n[Breakdown by Transfer Type]")
            logger.info(f"  • Direct routes (0 transfers): {len(direct)}")
            logger.info(f"  • Single-transfer routes (1 transfer): {len(single_transfer)}")
            logger.info(f"  • Multi-transfer routes (2-3 transfers): {len(multi_transfer)}")
            
            # Validate route counts
            is_valid, issues = self.validate_route_category_count(
                len(direct), len(single_transfer), len(multi_transfer)
            )
            
            if issues:
                logger.info(f"\n[Validation Issues]")
                for issue in issues:
                    logger.info(f"  {issue}")
            
            # Perform Pareto optimization
            logger.info(f"\n[Phase 2] Optimizing routes (Pareto analysis)...")
            opt_start = time.time()
            pareto_front = router.pareto_optimize(all_routes)
            opt_time = time.time() - opt_start
            
            logger.info(f"Pareto front has {len(pareto_front)} non-dominated routes")
            logger.info(f"Optimization completed in {opt_time:.2f}s")
            
            # Select optimal routes
            logger.info(f"\n[Phase 3] Selecting optimal routes...")
            optimal_routes, categories = router.select_optimal_routes(pareto_front)
            
            logger.info(f"Selected {len(optimal_routes)} optimal routes")
            logger.info(f"Categories: {', '.join(categories) if categories else 'Standard'}")
            
            # Display optimal routes
            logger.info(f"\n[OPTIMAL ROUTES] (Displayed on website)")
            logger.info(f"Count: {len(optimal_routes)}")
            
            for i, (route, category) in enumerate(optimal_routes[:5], 1):  # Show top 5
                logger.info(f"\n{i}. {category}")
                logger.info(self.format_route_for_display(route, category))
            
            if len(optimal_routes) > 5:
                logger.info(f"\n... and {len(optimal_routes) - 5} more optimal routes")
            
            # Display all routes summary
            logger.info(f"\n[ALL_ROUTES] (Available for detailed search)")
            logger.info(f"Total count: {len(all_routes)}")
            logger.info(f"Breakdown:")
            logger.info(f"  • Direct (0 transfers): {len(direct)}")
            logger.info(f"  • Single-transfer (1 transfer): {len(single_transfer)}")
            logger.info(f"  • Multi-transfer (2-3 transfers): {len(multi_transfer)}")
            
            # Display summary statistics
            logger.info(f"\n[SUMMARY STATISTICS]")
            logger.info(f"Total routes generated: {len(all_routes)}")
            logger.info(f"Routes on optimal list: {len(optimal_routes)}")
            logger.info(f"Generation time: {gen_time:.2f}s")
            logger.info(f"Optimization time: {opt_time:.2f}s")
            logger.info(f"Total processing time: {gen_time + opt_time:.2f}s")
            
            # Create statistics object
            stats = RouteStatistics(
                source=source,
                destination=destination,
                total_routes=len(all_routes),
                direct_routes=len(direct),
                single_transfer_routes=len(single_transfer),
                multi_transfer_routes=len(multi_transfer),
                pareto_optimal=len(optimal_routes),
                generation_time=gen_time,
                optimization_time=opt_time
            )
            
            self.results.append(stats)
            return stats
        
        except Exception as e:
            logger.error(f"ERROR during route generation: {e}", exc_info=True)
            raise
    
    def test_multiple_station_pairs(self, pairs: List[Tuple[str, str]]):
        """Test route generation for multiple station pairs"""
        logger.info(f"\n{'=' * 80}")
        logger.info(f"COMPREHENSIVE ROUTE GENERATION TEST - {len(pairs)} Station Pairs")
        logger.info(f"{'=' * 80}")
        
        successful = 0
        failed = 0
        
        for source, destination in pairs:
            try:
                self.test_route_generation(source, destination)
                successful += 1
            except Exception as e:
                logger.error(f"Failed for {source} → {destination}: {e}")
                failed += 1
        
        # Print final summary
        logger.info(f"\n{'=' * 80}")
        logger.info(f"FINAL TEST SUMMARY")
        logger.info(f"{'=' * 80}")
        logger.info(f"Successful tests: {successful}/{len(pairs)}")
        logger.info(f"Failed tests: {failed}/{len(pairs)}")
        
        if self.results:
            logger.info(f"\nPerformance Summary:")
            avg_gen_time = sum(r.generation_time for r in self.results) / len(self.results)
            avg_opt_time = sum(r.optimization_time for r in self.results) / len(self.results)
            avg_total_routes = sum(r.total_routes for r in self.results) / len(self.results)
            avg_optimal = sum(r.pareto_optimal for r in self.results) / len(self.results)
            
            logger.info(f"  Average generation time: {avg_gen_time:.2f}s")
            logger.info(f"  Average optimization time: {avg_opt_time:.2f}s")
            logger.info(f"  Average routes generated: {avg_total_routes:.0f}")
            logger.info(f"  Average optimal routes: {avg_optimal:.0f}")
        
        logger.info(f"\n✅ Test suite completed!")


def main():
    """Main entry point"""
    
    # Test pairs (mix of known and potential random pairs)
    test_pairs = [
        ("NDLS", "KOTA"),      # Major route
        ("NDLS", "MAS"),       # Longer route
        ("HWH", "CSMT"),       # Kolkata to Mumbai
        ("SBC", "NDLS"),       # Bangalore to Delhi
        ("PGT", "HYD"),        # Different corridor
    ]
    
    try:
        tester = RouteGenerationTest()
        tester.test_multiple_station_pairs(test_pairs)
        
        return 0
    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
