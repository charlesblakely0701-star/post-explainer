#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CLI for running the evaluation harness."""

import argparse
import asyncio
import json
import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows compatibility
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="Evaluation harness for the Post Explainer agent"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run evaluation tests")
    run_parser.add_argument(
        "--case",
        type=str,
        help="Run a single test case by ID"
    )
    run_parser.add_argument(
        "--category",
        type=str,
        help="Run tests from a specific category (tech, culture, news, meme, finance)"
    )
    run_parser.add_argument(
        "--output",
        type=str,
        help="Output file path for results"
    )
    run_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate evaluation report")
    report_parser.add_argument(
        "--input",
        type=str,
        help="Input results file (defaults to latest)"
    )
    report_parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format"
    )
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available test cases")
    
    return parser


async def run_evaluation(args: argparse.Namespace) -> int:
    """Run evaluation tests."""
    from evaluation.runner import load_test_cases, run_all_tests, save_results
    
    # Load test cases
    test_cases = load_test_cases()
    
    # Filter by case ID if specified
    if args.case:
        test_cases = [tc for tc in test_cases if tc["id"] == args.case]
        if not test_cases:
            print(f"Error: Test case '{args.case}' not found")
            return 1
    
    # Filter by category if specified
    if args.category:
        test_cases = [tc for tc in test_cases if tc["category"] == args.category]
        if not test_cases:
            print(f"Error: No test cases found for category '{args.category}'")
            return 1
    
    # Initialize explainer
    try:
        # Add backend directory to path so relative imports work
        backend_path = Path(__file__).parent.parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        from services.explainer import PostExplainer
        explainer = PostExplainer()
    except Exception as e:
        print(f"Error initializing explainer: {e}")
        print("Make sure your .env file is configured with valid API keys")
        import traceback
        traceback.print_exc()
        return 1
    
    # Run tests
    verbose = not args.quiet
    results = await run_all_tests(test_cases, explainer, verbose)
    
    # Save results
    output_path = save_results(results, args.output)
    if verbose:
        print(f"Results saved to: {output_path}")
    
    # Return exit code based on pass rate
    pass_rate = results["summary"]["pass_rate"]
    return 0 if pass_rate >= 0.7 else 1


def generate_report(args: argparse.Namespace) -> int:
    """Generate evaluation report."""
    from pathlib import Path
    import json
    
    # Find results file
    if args.input:
        results_path = Path(args.input)
    else:
        # Find latest results file
        results_dir = Path(__file__).parent / "results"
        if not results_dir.exists():
            print("No results found. Run 'evaluation run' first.")
            return 1
        
        results_files = sorted(results_dir.glob("results_*.json"))
        if not results_files:
            print("No results found. Run 'evaluation run' first.")
            return 1
        
        results_path = results_files[-1]
    
    # Load results
    with open(results_path) as f:
        results = json.load(f)
    
    # Generate report
    if args.format == "json":
        print(json.dumps(results, indent=2))
    elif args.format == "markdown":
        print(generate_markdown_report(results))
    else:
        print(generate_text_report(results))
    
    return 0


def generate_text_report(results: dict) -> str:
    """Generate plain text report."""
    lines = []
    summary = results["summary"]
    
    lines.append("=" * 60)
    lines.append("EVALUATION REPORT")
    lines.append(f"Generated: {results['timestamp']}")
    lines.append("=" * 60)
    lines.append("")
    lines.append("SUMMARY")
    lines.append("-" * 30)
    lines.append(f"Total Tests: {summary['total_tests']}")
    lines.append(f"Passed: {summary['passed']}")
    lines.append(f"Failed: {summary['failed']}")
    lines.append(f"Errors: {summary['errors']}")
    lines.append(f"Pass Rate: {summary['pass_rate']*100:.1f}%")
    lines.append(f"Average Score: {summary['average_score']:.3f}")
    lines.append(f"Average Time: {summary['average_time']:.2f}s")
    lines.append("")
    lines.append("DETAILED RESULTS")
    lines.append("-" * 30)
    
    for result in results["results"]:
        # Use ASCII-safe symbols
        status_symbol = "[PASS]" if result["status"] == "passed" else "[FAIL]" if result["status"] == "failed" else "[ERR]"
        score = result["metrics"]["overall_score"] if result["metrics"] else 0
        lines.append(f"{status_symbol} {result['test_id']}: {score:.3f}")
        
        if result["error"]:
            lines.append(f"  Error: {result['error']}")
        elif result["metrics"]:
            m = result["metrics"]
            lines.append(f"  Keywords: {m['keyword_coverage']['score']:.2f} | Topics: {m['topic_coverage']['score']:.2f}")
    
    return "\n".join(lines)


def generate_markdown_report(results: dict) -> str:
    """Generate markdown report."""
    lines = []
    summary = results["summary"]
    
    lines.append("# Evaluation Report")
    lines.append("")
    lines.append(f"*Generated: {results['timestamp']}*")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Tests | {summary['total_tests']} |")
    lines.append(f"| Passed | {summary['passed']} |")
    lines.append(f"| Failed | {summary['failed']} |")
    lines.append(f"| Errors | {summary['errors']} |")
    lines.append(f"| Pass Rate | {summary['pass_rate']*100:.1f}% |")
    lines.append(f"| Average Score | {summary['average_score']:.3f} |")
    lines.append(f"| Average Time | {summary['average_time']:.2f}s |")
    lines.append("")
    lines.append("## Detailed Results")
    lines.append("")
    lines.append("| Test ID | Status | Score | Time |")
    lines.append("|---------|--------|-------|------|")
    
    for result in results["results"]:
        status = "PASS" if result["status"] == "passed" else "FAIL" if result["status"] == "failed" else "ERROR"
        score = f"{result['metrics']['overall_score']:.3f}" if result["metrics"] else "N/A"
        time = f"{result['elapsed_time']:.2f}s"
        lines.append(f"| {result['test_id']} | {status} | {score} | {time} |")
    
    return "\n".join(lines)


def list_test_cases(args: argparse.Namespace) -> int:
    """List available test cases."""
    from evaluation.runner import load_test_cases
    
    test_cases = load_test_cases()
    
    print(f"\nAvailable test cases ({len(test_cases)} total):\n")
    print(f"{'ID':<15} {'Category':<10} {'Difficulty':<10} Post")
    print("-" * 70)
    
    for tc in test_cases:
        post_preview = tc["post_text"][:40] + "..." if len(tc["post_text"]) > 40 else tc["post_text"]
        print(f"{tc['id']:<15} {tc['category']:<10} {tc['difficulty']:<10} {post_preview}")
    
    return 0


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.command == "run":
        return asyncio.run(run_evaluation(args))
    elif args.command == "report":
        return generate_report(args)
    elif args.command == "list":
        return list_test_cases(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())

