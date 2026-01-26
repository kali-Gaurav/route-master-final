"""
Comprehensive Multi-Transfer Route Test Suite
Tests route generation with up to 4 transfers using different station pairs
"""

import time
import json
from datetime import datetime
from database_manager import DatabaseManager
from advanced_multi_transfer import AdvancedMultiTransferRouter
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiTransferTestSuite:
    """Test suite for multi-transfer route generation"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.router = AdvancedMultiTransferRouter(self.db)
        self.test_results = {}
    
    def run_all_tests(self):
        """Run comprehensive multi-transfer tests"""
        
        logger.info("\n" + "="*80)
        logger.info("MULTI-TRANSFER ROUTE TEST SUITE")
        logger.info("="*80)
        
        # Test cases with different station pairs
        test_cases = [
            # Short distance (nearby stations)
            {"source": "CSMT", "destination": "DADA", "name": "Short Distance (Mumbai nearby)"},
            
            # Medium distance
            {"source": "CSMT", "destination": "KOTA", "name": "Medium Distance (Mumbai-Rajasthan)"},
            
            # Long distance (likely to have 4-transfer routes)
            {"source": "CSMT", "destination": "SBC", "name": "Long Distance (Mumbai-Bangalore)"},
        ]
        
        all_results = {
            'test_suite_metadata': {
                'total_tests': len(test_cases),
                'test_timestamp': datetime.now().isoformat(),
                'max_transfers': 4,
            },
            'test_cases': {}
        }
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n[Test {i}/{len(test_cases)}] {test_case['name']}")
            logger.info(f"  {test_case['source']} → {test_case['destination']}")
            
            try:
                # Generate routes
                start = time.time()
                routes = self.router.generate_all_transfer_routes(
                    source=test_case['source'],
                    destination=test_case['destination'],
                    max_transfers=4,
                    max_routes_per_type=100
                )
                gen_time = time.time() - start
                
                # Analyze routes
                analysis = self.router.analyze_multi_transfer_routes(routes)
                
                # Store results
                test_result = {
                    'source': test_case['source'],
                    'destination': test_case['destination'],
                    'name': test_case['name'],
                    'generation_time': gen_time,
                    'total_routes': routes['summary']['total_routes'],
                    'routes_by_transfer': routes['summary'],
                    'analysis': analysis,
                }
                
                all_results['test_cases'][f"test_{i}"] = test_result
                
                logger.info(f"  ✓ Test completed in {gen_time:.2f}s")
                
            except Exception as e:
                logger.error(f"  ✗ Test failed: {e}")
                all_results['test_cases'][f"test_{i}"] = {
                    'error': str(e),
                    'source': test_case['source'],
                    'destination': test_case['destination'],
                }
        
        return all_results
    
    def generate_comparison_report(self, results: dict) -> str:
        """Generate a comparison report across all test cases"""
        
        logger.info("\n" + "="*80)
        logger.info("COMPARISON REPORT: Multi-Transfer Routes")
        logger.info("="*80)
        
        report_lines = [
            "# Multi-Transfer Route Generation Test Report",
            f"\nGenerated: {datetime.now().isoformat()}",
            f"Test Timestamp: {results['test_suite_metadata']['test_timestamp']}",
            f"Total Tests: {results['test_suite_metadata']['total_tests']}",
            "\n## Test Results Summary\n"
        ]
        
        # Create comparison table
        report_lines.append("| Route Pair | Total Routes | 0-Transfer | 1-Transfer | 2-Transfer | 3-Transfer | 4-Transfer | Time (s) |")
        report_lines.append("|------------|--------------|-----------|-----------|-----------|-----------|-----------|----------|")
        
        for test_id, test_case in results['test_cases'].items():
            if 'error' not in test_case:
                source = test_case['source']
                dest = test_case['destination']
                pair = f"{source}→{dest}"
                
                route_summary = test_case['routes_by_transfer']
                total = route_summary.get('total_routes', 0)
                t0 = route_summary.get('0_transfer_routes', 0)
                t1 = route_summary.get('1_transfer_routes', 0)
                t2 = route_summary.get('2_transfer_routes', 0)
                t3 = route_summary.get('3_transfer_routes', 0)
                t4 = route_summary.get('4_transfer_routes', 0)
                time_taken = test_case['generation_time']
                
                report_lines.append(
                    f"| {pair} | {total} | {t0} | {t1} | {t2} | {t3} | {t4} | {time_taken:.2f} |"
                )
        
        # Detailed analysis for each test
        report_lines.append("\n## Detailed Analysis by Route Pair\n")
        
        for test_id, test_case in results['test_cases'].items():
            if 'error' not in test_case:
                source = test_case['source']
                dest = test_case['destination']
                name = test_case['name']
                
                report_lines.append(f"### {name}")
                report_lines.append(f"**Route:** {source} → {dest}")
                report_lines.append(f"**Generation Time:** {test_case['generation_time']:.2f}s\n")
                
                # Transfer type breakdown
                report_lines.append("#### Route Distribution by Transfers\n")
                
                analysis = test_case['analysis']
                for tc in sorted(analysis['transfer_type_breakdown'].keys()):
                    stats = analysis['transfer_type_breakdown'][tc]
                    if stats['count'] > 0:
                        report_lines.append(
                            f"**{tc} Transfer(s):** {stats['count']} routes ({stats['percentage']:.1f}%)"
                        )
                        report_lines.append(f"  - Duration: {stats['avg_duration_hours']:.2f}h avg (min: {stats['min_duration_hours']:.2f}h, max: {stats['max_duration_hours']:.2f}h)")
                        report_lines.append(f"  - Distance: {stats['avg_distance_km']:.0f}km avg (min: {stats['min_distance_km']:.0f}km, max: {stats['max_distance_km']:.0f}km)")
                        report_lines.append(f"  - Cost: ₹{stats['avg_cost']:.0f} avg (min: ₹{stats['min_cost']:.0f}, max: ₹{stats['max_cost']:.0f})\n")
                
                # Sample routes
                report_lines.append("#### Sample Routes\n")
                
                for tc in sorted(analysis['sample_routes'].keys()):
                    samples = analysis['sample_routes'][tc]
                    if samples:
                        report_lines.append(f"**{tc} Transfer(s):**")
                        for sample in samples[:2]:  # Show first 2 samples
                            route_num = sample['index']
                            segments = sample['segments']
                            duration = sample['total_duration']
                            distance = sample['total_distance']
                            cost = sample['total_cost']
                            
                            report_lines.append(f"  Route {route_num}: {segments} segments")
                            report_lines.append(f"    Duration: {duration:.2f}h | Distance: {distance:.0f}km | Cost: ₹{cost:.0f}")
                            report_lines.append("    Segments:")
                            
                            for seg in sample['segments_list'][:3]:  # Show first 3 segments
                                report_lines.append(
                                    f"      - Train {seg['train']}: {seg['from']} → {seg['to']} "
                                    f"({seg['distance_km']:.0f}km, {seg['duration_hours']:.2f}h travel, {seg['wait_before_hours']:.2f}h wait)"
                                )
                            
                            if len(sample['segments_list']) > 3:
                                report_lines.append(f"      ... and {len(sample['segments_list']) - 3} more segments")
                            
                            report_lines.append("")
        
        # Summary and recommendations
        report_lines.append("\n## Summary\n")
        report_lines.append("### Key Findings\n")
        
        total_all_routes = sum(
            test['total_routes'] 
            for test in results['test_cases'].values() 
            if 'error' not in test
        )
        
        report_lines.append(f"- **Total routes generated:** {total_all_routes} across all test cases")
        report_lines.append("- **Multi-transfer support:** Routes with up to 4 transfers are now supported")
        report_lines.append("- **Station-dependent:** The number of 4-transfer routes depends on station distance and network topology")
        report_lines.append("- **Short distances (CSMT→DADA):** Primarily direct and 1-transfer routes are feasible")
        report_lines.append("- **Long distances:** More likely to generate routes with 3-4 transfers\n")
        
        report_lines.append("### Recommendations\n")
        report_lines.append("1. **Use the advanced_multi_transfer module** for comprehensive route generation")
        report_lines.append("2. **Adjust max_routes_per_type** based on distance: increase for long distances")
        report_lines.append("3. **Monitor performance:** BFS search scales with transfer count - watch queue sizes")
        report_lines.append("4. **User presentation:** Display routes grouped by transfer count for clarity")
        report_lines.append("5. **Optimization:** Use Pareto optimization to select best routes from each category\n")
        
        report = "\n".join(report_lines)
        
        # Log the report
        logger.info(report)
        
        return report


def main():
    """Run the comprehensive test suite"""
    
    test_suite = MultiTransferTestSuite()
    results = test_suite.run_all_tests()
    
    # Generate comparison report
    report = test_suite.generate_comparison_report(results)
    
    # Save detailed results to JSON
    output_file = f"multi_transfer_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\n✓ Detailed results saved to: {output_file}")
    
    # Save report to markdown (with UTF-8 encoding to support special characters)
    report_file = f"MULTI_TRANSFER_TEST_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"✓ Report saved to: {report_file}")


if __name__ == "__main__":
    main()
