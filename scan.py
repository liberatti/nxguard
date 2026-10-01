#!/usr/bin/env python3
"""Run Semgrep security analysis and generate categorized Markdown reports with actionable TODOs."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def get_semgrep_bin() -> str:
    """Locate the Semgrep executable, prioritizing the active virtual environment."""
    venv_bin = Path(sys.executable).parent / "semgrep"
    if venv_bin.exists():
        return str(venv_bin)
    which_bin = shutil.which("semgrep")
    if which_bin:
        return which_bin
    return "semgrep"


def run_semgrep_scan(config: str, sarif_path: Path | None = None) -> dict:
    """Execute Semgrep scan in-memory and optionally generate SARIF report."""
    semgrep_bin = get_semgrep_bin()
    cmd = [semgrep_bin, "scan", f"--config={config}", "--json"]
    print(f"🔍 Running Semgrep: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if sarif_path:
        sarif_cmd = [
            semgrep_bin,
            "scan",
            f"--config={config}",
            "--sarif",
            "-o",
            str(sarif_path),
        ]
        print(f"📄 Generating SARIF report: {' '.join(sarif_cmd)}")
        subprocess.run(sarif_cmd)

    if result.returncode in (0, 1) and result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            print(f"❌ Failed to decode Semgrep JSON output: {exc}", file=sys.stderr)
            return {}
    else:
        print(f"❌ Semgrep execution failed:\n{result.stderr}", file=sys.stderr)
        return {}


def classify_finding(item: dict) -> str:
    """Classify a finding into: SECURITY, BEST_PRACTICE, or AUDIT."""
    extra = item.get("extra", {})
    metadata = extra.get("metadata", {})
    severity = extra.get("severity", "INFO").upper()
    category = metadata.get("category", "").lower()
    subcategories = [s.lower() for s in metadata.get("subcategory", [])]
    check_id = item.get("check_id", "").lower()

    if severity == "ERROR" or "vuln" in subcategories:
        return "SECURITY"
    if "audit" in subcategories or "missing-integrity" in check_id:
        return "AUDIT"
    if category == "best-practice" or "mutable-action-tag" in check_id:
        return "BEST_PRACTICE"
    if category == "security":
        return "SECURITY"

    return "BEST_PRACTICE"


def write_markdown_file(
    filepath: Path, title: str, description: str, items: list[dict]
) -> None:
    """Write a categorized Markdown report containing actionable TODO checkboxes."""
    by_severity: dict[str, list[dict]] = {"ERROR": [], "WARNING": [], "INFO": []}
    for item in items:
        sev = item.get("extra", {}).get("severity", "INFO").upper()
        by_severity.setdefault(sev, []).append(item)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"{description}\n\n")
        f.write("## 📊 Summary\n\n")
        f.write(f"- **Total findings:** `{len(items)}`\n")
        f.write(f"- 🔴 **ERROR:** `{len(by_severity.get('ERROR', []))}`\n")
        f.write(f"- 🟡 **WARNING:** `{len(by_severity.get('WARNING', []))}`\n")
        f.write(f"- 🔵 **INFO:** `{len(by_severity.get('INFO', []))}`\n\n")
        f.write("---\n\n")
        f.write("## 📋 Task List (TODOs)\n\n")

        if not items:
            f.write("🎉 *No findings detected in this category!*\n")
            return

        for sev in ["ERROR", "WARNING", "INFO"]:
            sub_items = by_severity.get(sev, [])
            if not sub_items:
                continue

            icon = "🔴" if sev == "ERROR" else ("🟡" if sev == "WARNING" else "🔵")
            f.write(f"### {icon} {sev} ({len(sub_items)})\n\n")

            for item in sub_items:
                path = item.get("path", "unknown")
                start = item.get("start", {})
                line = start.get("line", 1)
                rule = item.get("check_id", "unknown-rule")
                msg = (
                    item.get("extra", {}).get("message", "").strip().replace("\n", " ")
                )

                f.write(f"- [ ] **`{rule}`**\n")
                f.write(f"  - **File:** [`{path}:{line}`]({path}#L{line})\n")
                f.write(f"  - **Details:** {msg}\n\n")


def generate_reports(data: dict) -> dict[str, int]:
    """Categorize findings and write the respective Markdown report files."""
    results = data.get("results", [])

    categorized: dict[str, list[dict]] = {
        "SECURITY": [],
        "BEST_PRACTICE": [],
        "AUDIT": [],
    }

    for item in results:
        cat = classify_finding(item)
        categorized.setdefault(cat, []).append(item)

    # 1. TODO_SECURITY.md
    write_markdown_file(
        Path("TODO_SECURITY.md"),
        "🚨 Security Vulnerabilities (TODOs)",
        "Direct security vulnerabilities, injection flaws, and critical security issues.",
        categorized["SECURITY"],
    )

    # 2. TODO_BEST.md
    write_markdown_file(
        Path("TODO_BEST.md"),
        "✨ Best Practices & Code Quality (TODOs)",
        "Software development best practices, supply chain security, and dependency maintenance.",
        categorized["BEST_PRACTICE"],
    )

    # 3. TODO_AUDIT.md
    write_markdown_file(
        Path("TODO_AUDIT.md"),
        "🔍 Security Audit & Integrity (TODOs)",
        "Compliance items, Subresource Integrity (SRI), and items requiring manual review.",
        categorized["AUDIT"],
    )

    return {k: len(v) for k, v in categorized.items()}


def main():
    parser = argparse.ArgumentParser(
        description="Run Semgrep security analysis and generate categorized Markdown reports."
    )
    parser.add_argument(
        "--config",
        default="auto",
        help="Semgrep rule configuration (default: auto)",
    )
    parser.add_argument(
        "--sarif",
        action="store_true",
        help="Generate semgrep.sarif file for GitHub Security integration",
    )
    parser.add_argument(
        "--keep-json",
        action="store_true",
        help="Retain intermediate raw semgrep.json output file",
    )

    args = parser.parse_args()

    sarif_path = Path("semgrep.sarif") if args.sarif else None
    try:
        data = run_semgrep_scan(args.config, sarif_path)

        if args.keep_json:
            json_path = Path("semgrep.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"💾 Raw JSON saved to: {json_path.resolve()}")

        counts = generate_reports(data)

        print("\n✅ Reports generated successfully:")
        print(f"  • TODO_SECURITY.md:  {counts.get('SECURITY', 0)} tasks")
        print(f"  • TODO_BEST.md:      {counts.get('BEST_PRACTICE', 0)} tasks")
        print(f"  • TODO_AUDIT.md:     {counts.get('AUDIT', 0)} tasks")
        print(f"  Total: {sum(counts.values())} findings")
    finally:
        # Clean up temporary/leftover files
        leftovers = [Path("=semgrep.json"), Path("=semgrep.sarif")]
        if not args.sarif:
            leftovers.append(Path("semgrep.sarif"))

        for leftover in leftovers:
            if leftover.exists():
                try:
                    leftover.unlink()
                except OSError:
                    pass


if __name__ == "__main__":
    main()
