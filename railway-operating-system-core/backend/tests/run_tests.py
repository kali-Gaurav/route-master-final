#!/usr/bin/env python3
"""
Comprehensive Test Runner for Railway Operating System Backend

This script runs all security, validation, and integration tests
with detailed reporting and coverage analysis.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List, Any

class TestRunner:
    """Comprehensive test runner with reporting"""

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.backend_dir = self.workspace_root / "railway-operating-system-core" / "backend"
        self.test_dir = self.backend_dir / "tests"
        self.reports_dir = self.backend_dir / "test_reports"
        # Ensure backend directory exists
        self.backend_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)

    def run_pytest(self, test_pattern: str = "", verbose: bool = False, coverage: bool = False) -> Dict[str, Any]:
        """Run pytest with specified options"""
        cmd = ["python", "-m", "pytest"]

        if test_pattern:
            cmd.append(f"-k {test_pattern}")

        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")

        if coverage:
            cmd.extend([
                "--cov=backend",
                "--cov-report=html:test_reports/coverage_html",
                "--cov-report=xml:test_reports/coverage.xml",
                "--cov-report=term-missing"
            ])

        cmd.extend([
            "--tb=short",
            "--junitxml=test_reports/junit.xml",
            "--json-report",
            "--json-report-file=test_reports/results.json",
            str(self.test_dir)
        ])

        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=self.backend_dir, capture_output=True, text=True)

        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd)
        }

    def run_security_tests(self) -> Dict[str, Any]:
        """Run security-specific tests"""
        print("\n🔒 Running Security Tests...")
        return self.run_pytest("test_security_features", verbose=True)

    def run_validation_tests(self) -> Dict[str, Any]:
        """Run validation and schema tests"""
        print("\n✅ Running Validation Tests...")
        return self.run_pytest("test_route_validation", verbose=True)

    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration and middleware tests"""
        print("\n🔗 Running Integration Tests...")
        return self.run_pytest("test_middleware_integration", verbose=True)

    def run_all_tests(self, coverage: bool = True) -> Dict[str, Any]:
        """Run all tests with coverage"""
        print("\n🚀 Running All Tests with Coverage...")
        return self.run_pytest("", verbose=False, coverage=coverage)

    def run_load_tests(self) -> Dict[str, Any]:
        """Run load and performance tests"""
        print("\n⚡ Running Load Tests...")
        return self.run_pytest("load", verbose=True)

    def analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test results"""
        analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_success": results["returncode"] == 0,
            "test_suites": {}
        }

        # Try to parse JSON results if available
        json_file = self.reports_dir / "results.json"
        if json_file.exists():
            try:
                with open(json_file, 'r') as f:
                    json_data = json.load(f)
                    analysis["test_suites"] = self._parse_json_results(json_data)
            except Exception as e:
                print(f"Warning: Could not parse JSON results: {e}")

        # Parse stdout for basic metrics
        stdout = results["stdout"]
        analysis["summary"] = self._parse_stdout_summary(stdout)

        return analysis

    def _parse_json_results(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse detailed JSON test results"""
        suites = {}

        if "tests" in json_data:
            for test in json_data["tests"]:
                suite_name = test.get("nodeid", "").split("::")[0]
                if suite_name not in suites:
                    suites[suite_name] = {
                        "total": 0,
                        "passed": 0,
                        "failed": 0,
                        "errors": 0,
                        "skipped": 0,
                        "duration": 0.0
                    }

                suites[suite_name]["total"] += 1
                suites[suite_name]["duration"] += test.get("duration", 0)

                outcome = test.get("outcome", "")
                if outcome == "passed":
                    suites[suite_name]["passed"] += 1
                elif outcome == "failed":
                    suites[suite_name]["failed"] += 1
                elif outcome == "error":
                    suites[suite_name]["errors"] += 1
                elif outcome == "skipped":
                    suites[suite_name]["skipped"] += 1

        return suites

    def _parse_stdout_summary(self, stdout: str) -> Dict[str, Any]:
        """Parse basic test summary from stdout"""
        summary = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "warnings": 0
        }

        lines = stdout.split('\n')
        for line in lines:
            line = line.strip().lower()
            if "passed" in line and "failed" in line:
                # Parse summary line like "5 passed, 2 failed"
                parts = line.replace("=", "").strip().split(",")
                for part in parts:
                    part = part.strip()
                    if "passed" in part:
                        summary["passed"] = int(part.split()[0])
                    elif "failed" in part:
                        summary["failed"] = int(part.split()[0])
                    elif "error" in part:
                        summary["errors"] = int(part.split()[0])
                    elif "skipped" in part:
                        summary["skipped"] = int(part.split()[0])
                    elif "warning" in part:
                        summary["warnings"] = int(part.split()[0])

        summary["total_tests"] = summary["passed"] + summary["failed"] + summary["errors"] + summary["skipped"]
        return summary

    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("# Railway Operating System Backend - Test Report")
        report.append(f"**Generated:** {analysis['timestamp']}")
        report.append(f"**Overall Status:** {'✅ PASSED' if analysis['overall_success'] else '❌ FAILED'}")
        report.append("")

        # Summary
        summary = analysis.get("summary", {})
        report.append("## Summary")
        report.append(f"- **Total Tests:** {summary.get('total_tests', 0)}")
        report.append(f"- **Passed:** {summary.get('passed', 0)}")
        report.append(f"- **Failed:** {summary.get('failed', 0)}")
        report.append(f"- **Errors:** {summary.get('errors', 0)}")
        report.append(f"- **Skipped:** {summary.get('skipped', 0)}")
        report.append("")

        # Test Suites
        suites = analysis.get("test_suites", {})
        if suites:
            report.append("## Test Suites")
            for suite_name, metrics in suites.items():
                status = "✅" if metrics["failed"] == 0 and metrics["errors"] == 0 else "❌"
                report.append(f"### {status} {suite_name}")
                report.append(f"- Total: {metrics['total']}")
                report.append(f"- Passed: {metrics['passed']}")
                report.append(f"- Failed: {metrics['failed']}")
                report.append(f"- Errors: {metrics['errors']}")
                report.append(f"- Duration: {metrics['duration']:.2f}s")
                report.append("")

        # Coverage (if available)
        coverage_file = self.reports_dir / "coverage.xml"
        if coverage_file.exists():
            report.append("## Coverage")
            report.append("*Coverage report available at:* `test_reports/coverage_html/index.html`")
            report.append("")

        # Recommendations
        report.append("## Recommendations")
        if not analysis["overall_success"]:
            report.append("❌ **Critical:** Fix failing tests before deployment")
        else:
            report.append("✅ **Good:** All tests passing")

        if summary.get("failed", 0) > 0:
            report.append("🔧 **Action Required:** Review and fix failed test cases")

        if summary.get("errors", 0) > 0:
            report.append("🚨 **Critical:** Fix test errors - these indicate serious issues")

        return "\n".join(report)

    def save_report(self, report: str, filename: str = "test_report.md"):
        """Save report to file"""
        report_file = self.reports_dir / filename
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"📄 Report saved to: {report_file}")

    def run_comprehensive_test_suite(self) -> bool:
        """Run the complete test suite"""
        print("🧪 Starting Comprehensive Test Suite")
        print("=" * 50)

        # Run all tests with coverage
        results = self.run_all_tests(coverage=True)

        # Analyze results
        analysis = self.analyze_results(results)

        # Generate and save report
        report = self.generate_report(analysis)
        self.save_report(report)

        # Print summary
        print("\n" + "=" * 50)
        if analysis["overall_success"]:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("💥 SOME TESTS FAILED!")
            print("Check the detailed report for more information.")

        print(f"📊 Report: {self.reports_dir}/test_report.md")
        if (self.reports_dir / "coverage_html" / "index.html").exists():
            print(f"📈 Coverage: {self.reports_dir}/coverage_html/index.html")

        return analysis["overall_success"]

def main():
    parser = argparse.ArgumentParser(description="Run Railway Operating System Backend Tests")
    parser.add_argument("--workspace", default=".", help="Workspace root directory")
    parser.add_argument("--test-type", choices=["all", "security", "validation", "integration", "load"],
                       default="all", help="Type of tests to run")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage analysis")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    runner = TestRunner(args.workspace)

    try:
        if args.test_type == "all":
            success = runner.run_comprehensive_test_suite()
        elif args.test_type == "security":
            results = runner.run_security_tests()
            success = results["returncode"] == 0
        elif args.test_type == "validation":
            results = runner.run_validation_tests()
            success = results["returncode"] == 0
        elif args.test_type == "integration":
            results = runner.run_integration_tests()
            success = results["returncode"] == 0
        elif args.test_type == "load":
            results = runner.run_load_tests()
            success = results["returncode"] == 0

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"❌ Test runner failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()