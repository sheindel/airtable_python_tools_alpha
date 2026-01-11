#!/usr/bin/env python3
"""
AI-Executable Regression Test Runner

This script orchestrates the regression test suite for the Airtable Analysis Tools.
It can be executed by an AI agent to verify all functionality is working correctly.

Usage:
    uv run python run_regression_tests.py [--phase PHASE] [--output REPORT.md]
    
    --phase: Run specific phase only (1, 2, 3, 4, or 'all')
    --output: Output report file (default: test_report.md)
"""

import subprocess
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import argparse


@dataclass
class TestResult:
    """Result of a single test"""
    name: str
    phase: str
    status: str  # PASS, FAIL, SKIP, ERROR
    duration: float
    message: str = ""
    details: str = ""
    output: str = ""


@dataclass
class TestReport:
    """Complete test report"""
    start_time: datetime
    end_time: Optional[datetime] = None
    results: List[TestResult] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == "PASS")
    
    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == "FAIL")
    
    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.status == "SKIP")
    
    @property
    def errors(self) -> int:
        return sum(1 for r in self.results if r.status == "ERROR")
    
    def add_result(self, result: TestResult):
        self.results.append(result)
        print(f"  [{result.status}] {result.name} ({result.duration:.2f}s)")
        if result.message:
            print(f"    → {result.message}")
    
    def to_markdown(self) -> str:
        """Generate markdown report"""
        lines = [
            "# Regression Test Report",
            f"Date: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {self.duration:.2f} seconds",
            "",
            "## Environment",
            f"- OS: {self.environment.get('os', 'unknown')}",
            f"- Python: {self.environment.get('python', 'unknown')}",
            f"- Node: {self.environment.get('node', 'unknown')}",
            f"- npm: {self.environment.get('npm', 'unknown')}",
            "",
            "## Summary",
            f"- **Total Tests**: {len(self.results)}",
            f"- **Passed**: {self.passed} ✅",
            f"- **Failed**: {self.failed} ❌",
            f"- **Skipped**: {self.skipped} ⏭️",
            f"- **Errors**: {self.errors} 🔥",
            "",
            "## Results by Phase",
            ""
        ]
        
        # Group results by phase
        phases = {}
        for result in self.results:
            if result.phase not in phases:
                phases[result.phase] = []
            phases[result.phase].append(result)
        
        for phase_name, phase_results in sorted(phases.items()):
            lines.append(f"### {phase_name}")
            lines.append("")
            
            for result in phase_results:
                status_icon = {
                    "PASS": "✅",
                    "FAIL": "❌",
                    "SKIP": "⏭️",
                    "ERROR": "🔥"
                }.get(result.status, "❓")
                
                lines.append(f"#### {status_icon} {result.name}")
                lines.append(f"- **Status**: {result.status}")
                lines.append(f"- **Duration**: {result.duration:.2f}s")
                
                if result.message:
                    lines.append(f"- **Message**: {result.message}")
                
                if result.details:
                    lines.append(f"- **Details**: {result.details}")
                
                if result.output and result.status in ["FAIL", "ERROR"]:
                    lines.append("- **Output**:")
                    lines.append("```")
                    lines.append(result.output[:500])  # Limit output size
                    if len(result.output) > 500:
                        lines.append("... (truncated)")
                    lines.append("```")
                
                lines.append("")
        
        # Critical issues
        critical = [r for r in self.results if r.status in ["FAIL", "ERROR"]]
        if critical:
            lines.append("## ⚠️ Critical Issues")
            lines.append("")
            for result in critical:
                lines.append(f"- **{result.name}**: {result.message or result.status}")
            lines.append("")
        
        # Recommendations
        lines.append("## Recommendations")
        if self.failed > 0:
            lines.append("- Investigate and fix failing tests before deployment")
        if self.errors > 0:
            lines.append("- Address error conditions that prevented test execution")
        if self.failed == 0 and self.errors == 0:
            lines.append("- All tests passed! ✨")
        lines.append("")
        
        return "\n".join(lines)


class TestRunner:
    """Orchestrates test execution"""
    
    def __init__(self):
        self.report = TestReport(start_time=datetime.now())
        self._gather_environment()
    
    def _gather_environment(self):
        """Collect environment information"""
        import platform
        self.report.environment['os'] = platform.system() + " " + platform.release()
        
        # Get tool versions
        for tool, cmd in [
            ('python', 'python --version'),
            ('node', 'node --version'),
            ('npm', 'npm --version'),
            ('uv', 'uv --version')
        ]:
            try:
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=5
                )
                version = result.stdout.strip() or result.stderr.strip()
                self.report.environment[tool] = version
            except Exception:
                self.report.environment[tool] = 'not found'
    
    def _run_command(
        self, 
        cmd: str, 
        timeout: int = 60,
        check: bool = False
    ) -> Tuple[int, str, str]:
        """Run a shell command and return (returncode, stdout, stderr)"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return -1, "", str(e)
    
    def run_test(
        self,
        name: str,
        phase: str,
        command: str,
        timeout: int = 60,
        expected_in_output: Optional[str] = None,
        expected_returncode: int = 0,
        check_files: Optional[List[str]] = None
    ) -> TestResult:
        """Run a single test and return result"""
        start = time.time()
        
        try:
            returncode, stdout, stderr = self._run_command(command, timeout)
            duration = time.time() - start
            
            # Check return code
            if returncode != expected_returncode:
                return TestResult(
                    name=name,
                    phase=phase,
                    status="FAIL",
                    duration=duration,
                    message=f"Expected return code {expected_returncode}, got {returncode}",
                    output=stdout + "\n" + stderr
                )
            
            # Check expected output
            if expected_in_output:
                combined = stdout + stderr
                if expected_in_output not in combined:
                    return TestResult(
                        name=name,
                        phase=phase,
                        status="FAIL",
                        duration=duration,
                        message=f"Expected '{expected_in_output}' in output",
                        output=combined
                    )
            
            # Check files exist
            if check_files:
                missing = [f for f in check_files if not Path(f).exists()]
                if missing:
                    return TestResult(
                        name=name,
                        phase=phase,
                        status="FAIL",
                        duration=duration,
                        message=f"Missing expected files: {', '.join(missing)}",
                        output=stdout
                    )
            
            return TestResult(
                name=name,
                phase=phase,
                status="PASS",
                duration=duration,
                message="Success",
                output=stdout[:200]  # Keep some output for debugging
            )
        
        except Exception as e:
            duration = time.time() - start
            return TestResult(
                name=name,
                phase=phase,
                status="ERROR",
                duration=duration,
                message=str(e)
            )
    
    def phase_1_setup_and_unit_tests(self):
        """Phase 1: Environment setup and unit tests"""
        print("\n" + "=" * 60)
        print("PHASE 1: Environment Setup and Unit Tests")
        print("=" * 60)
        
        # Check if demo schema exists
        demo_schema = Path("demo_base_schema.json")
        if not demo_schema.exists():
            self.report.add_result(TestResult(
                name="Demo Schema Check",
                phase="Phase 1: Setup",
                status="SKIP",
                duration=0,
                message="demo_base_schema.json not found - some CLI tests will be skipped"
            ))
        
        # Build CSS
        result = self.run_test(
            name="Build Tailwind CSS",
            phase="Phase 1: Setup",
            command="npm run build:css",
            timeout=30,
            check_files=["web/output.css"]
        )
        self.report.add_result(result)
        
        # Run unit tests
        result = self.run_test(
            name="Run Unit Tests",
            phase="Phase 1: Unit Tests",
            command="uv run pytest -v",
            timeout=120,
            expected_in_output="passed"
        )
        self.report.add_result(result)
        
        # Run coverage
        result = self.run_test(
            name="Generate Coverage Report",
            phase="Phase 1: Unit Tests",
            command="uv run pytest --cov=web --cov-report=term-missing",
            timeout=120
        )
        self.report.add_result(result)
    
    def phase_2_cli_tests(self):
        """Phase 2: CLI command testing"""
        print("\n" + "=" * 60)
        print("PHASE 2: CLI Command Tests")
        print("=" * 60)
        
        # Test CLI help commands
        cli_tests = [
            ("CLI Help", "uv run python main.py --help", "Usage:"),
            ("get-airtable-metadata Help", "uv run python main.py get-airtable-metadata --help", "Get Airtable metadata"),
            ("generate-mermaid-graph Help", "uv run python main.py generate-mermaid-graph --help", "Generate"),
            ("eval-formula Help", "uv run python main.py eval-formula --help", "Evaluate"),
        ]
        
        for name, cmd, expected in cli_tests:
            result = self.run_test(
                name=name,
                phase="Phase 2: CLI",
                command=cmd,
                expected_in_output=expected,
                timeout=10
            )
            self.report.add_result(result)
        
        # Test formula evaluation (doesn't require API)
        result = self.run_test(
            name="Eval Formula: Simple IF",
            phase="Phase 2: CLI",
            command='uv run python main.py eval-formula -f "IF(TRUE, \'yes\', \'no\')"',
            expected_in_output="yes",
            timeout=10
        )
        self.report.add_result(result)
        
        result = self.run_test(
            name="Eval Formula: Addition",
            phase="Phase 2: CLI",
            command='uv run python main.py eval-formula -f "1 + 2"',
            expected_in_output="3",
            timeout=10
        )
        self.report.add_result(result)
        
        # If demo schema exists, test commands that use it
        if Path("demo_base_schema.json").exists():
            result = self.run_test(
                name="Generate Postgres Schema",
                phase="Phase 2: CLI",
                command="uv run python main.py generate-postgres-schema -s demo_base_schema.json -o test_schema.sql",
                expected_in_output="written",
                check_files=["test_schema.sql"],
                timeout=30
            )
            self.report.add_result(result)
        else:
            self.report.add_result(TestResult(
                name="Generate Postgres Schema",
                phase="Phase 2: CLI",
                status="SKIP",
                duration=0,
                message="demo_base_schema.json not found"
            ))
    
    def phase_3_web_tests(self):
        """Phase 3: Web application testing (requires Chrome MCP)"""
        print("\n" + "=" * 60)
        print("PHASE 3: Web Application Tests")
        print("=" * 60)
        print("Note: This phase requires Chrome DevTools MCP to be running")
        print("      These tests should be executed manually or via MCP")
        
        # These tests require Chrome MCP which we can't directly invoke from Python
        # Instead, document what needs to be tested
        self.report.add_result(TestResult(
            name="Web App Tests",
            phase="Phase 3: Web App",
            status="SKIP",
            duration=0,
            message="Web app tests require Chrome MCP - see docs/ai-testing-guide.md for manual execution"
        ))
    
    def phase_4_integration(self):
        """Phase 4: Integration tests"""
        print("\n" + "=" * 60)
        print("PHASE 4: Integration Tests")
        print("=" * 60)
        
        # Check web modules can be imported
        result = self.run_test(
            name="Import Web Modules",
            phase="Phase 4: Integration",
            command='uv run python -c "import sys; sys.path.append(\'web\'); from at_metadata_graph import metadata_to_graph"',
            timeout=10
        )
        self.report.add_result(result)
        
        # Verify pyproject.toml is valid
        result = self.run_test(
            name="Validate pyproject.toml",
            phase="Phase 4: Integration",
            command='uv run python -c "import tomllib; tomllib.load(open(\'pyproject.toml\', \'rb\'))"',
            timeout=5
        )
        self.report.add_result(result)
        
        # Check that web/output.css exists
        if Path("web/output.css").exists():
            result = TestResult(
                name="Web CSS Asset Check",
                phase="Phase 4: Integration",
                status="PASS",
                duration=0,
                message="web/output.css exists"
            )
        else:
            result = TestResult(
                name="Web CSS Asset Check",
                phase="Phase 4: Integration",
                status="FAIL",
                duration=0,
                message="web/output.css not found - run 'npm run build:css'"
            )
        self.report.add_result(result)
    
    def run_all_phases(self):
        """Run all test phases"""
        self.phase_1_setup_and_unit_tests()
        self.phase_2_cli_tests()
        self.phase_3_web_tests()
        self.phase_4_integration()
        
        self.report.end_time = datetime.now()
    
    def save_report(self, output_file: str):
        """Save report to file"""
        report_md = self.report.to_markdown()
        Path(output_file).write_text(report_md)
        print(f"\n📊 Report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Run regression tests for Airtable Analysis Tools"
    )
    parser.add_argument(
        "--phase",
        choices=["1", "2", "3", "4", "all"],
        default="all",
        help="Which phase to run (default: all)"
    )
    parser.add_argument(
        "--output",
        default="test_report.md",
        help="Output report file (default: test_report.md)"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    print("🚀 Starting Regression Tests")
    print(f"   Output: {args.output}")
    print(f"   Phase: {args.phase}")
    
    if args.phase == "all":
        runner.run_all_phases()
    elif args.phase == "1":
        runner.phase_1_setup_and_unit_tests()
    elif args.phase == "2":
        runner.phase_2_cli_tests()
    elif args.phase == "3":
        runner.phase_3_web_tests()
    elif args.phase == "4":
        runner.phase_4_integration()
    
    runner.report.end_time = datetime.now()
    runner.save_report(args.output)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total:   {len(runner.report.results)}")
    print(f"Passed:  {runner.report.passed} ✅")
    print(f"Failed:  {runner.report.failed} ❌")
    print(f"Skipped: {runner.report.skipped} ⏭️")
    print(f"Errors:  {runner.report.errors} 🔥")
    print(f"Duration: {runner.report.duration:.2f}s")
    
    # Exit with error code if tests failed
    if runner.report.failed > 0 or runner.report.errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
