#!/usr/bin/env python3
"""
audits/ci/report_merge.py
Consolida logs de auditoría y genera resumen para CI/CD
"""

import sys
from datetime import datetime
from pathlib import Path


def read_log_file(log_path: Path) -> dict:
    """Lee un archivo de log y extrae información relevante"""
    try:
        content = log_path.read_text()
        return {
            "path": str(log_path),
            "size": log_path.stat().st_size,
            "lines": len(content.splitlines()),
            "has_error": "error" in content.lower() or "fail" in content.lower(),
            "has_warning": "warning" in content.lower() or "warn" in content.lower(),
        }
    except Exception as e:
        return {"path": str(log_path), "error": str(e)}


def parse_summary(summary_path: Path) -> dict:
    """Parsea el archivo SUMMARY.md"""
    try:
        content = summary_path.read_text()

        # Extraer estadísticas
        stats = {}
        for line in content.splitlines():
            if "Passed" in line:
                stats["passed"] = int(line.split(":")[-1].strip())
            elif "Failed" in line:
                stats["failed"] = int(line.split(":")[-1].strip())
            elif "Skipped" in line:
                stats["skipped"] = int(line.split(":")[-1].strip())

        # Determinar estado final
        if "AUDIT FAILED" in content:
            status = "FAILED"
        elif "AUDIT PASSED" in content:
            status = "PASSED"
        else:
            status = "UNKNOWN"

        return {"stats": stats, "status": status, "content": content}
    except Exception as e:
        return {"error": str(e)}


def generate_ci_summary(audit_dir: Path) -> str:
    """Genera resumen para GitHub Actions Summary"""
    summary_path = audit_dir / "SUMMARY.md"
    logs_dir = audit_dir / "logs"

    output = []
    output.append("# 📊 Audit Report")
    output.append("")

    # Información básica
    if summary_path.exists():
        summary_data = parse_summary(summary_path)

        if "stats" in summary_data:
            stats = summary_data["stats"]
            output.append("## Results")
            output.append("")
            output.append(f"- ✅ **Passed**: {stats.get('passed', 0)}")
            output.append(f"- ❌ **Failed**: {stats.get('failed', 0)}")
            output.append(f"- ⏭️ **Skipped**: {stats.get('skipped', 0)}")
            output.append("")

            # Badge de estado
            status = summary_data.get("status", "UNKNOWN")
            if status == "PASSED":
                badge = "🟢 **PASSED**"
            elif status == "FAILED":
                badge = "🔴 **FAILED**"
            else:
                badge = "🟡 **WARNING**"

            output.append(f"### Status: {badge}")
            output.append("")

    # Logs disponibles
    if logs_dir.exists():
        output.append("## 📁 Available Logs")
        output.append("")

        log_files = sorted(logs_dir.glob("*.log"))
        if log_files:
            output.append("| Log File | Size | Status |")
            output.append("|----------|------|--------|")

            for log_file in log_files:
                log_data = read_log_file(log_file)
                size_kb = log_data.get("size", 0) / 1024

                if log_data.get("has_error"):
                    status_icon = "❌"
                elif log_data.get("has_warning"):
                    status_icon = "⚠️"
                else:
                    status_icon = "✅"

                output.append(f"| `{log_file.name}` | {size_kb:.1f} KB | {status_icon} |")

            output.append("")

    # Enlaces útiles
    output.append("## 🔗 Quick Links")
    output.append("")
    output.append("- 📄 [Full Summary](SUMMARY.md)")
    output.append("- 📂 [All Logs](logs/)")
    output.append("- 🌳 [Repository Structure](logs/tree.txt)")
    output.append("")

    # Timestamp
    output.append(f"*Generated: {datetime.now().isoformat()}*")

    return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print("Usage: python report_merge.py <audit_directory>", file=sys.stderr)
        sys.exit(1)

    audit_dir = Path(sys.argv[1])

    if not audit_dir.exists():
        print(f"Error: Directory {audit_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    # Generar resumen para CI
    ci_summary = generate_ci_summary(audit_dir)

    # Imprimir a stdout (será capturado por GitHub Actions)
    print(ci_summary)

    # Determinar exit code basado en SUMMARY.md
    summary_path = audit_dir / "SUMMARY.md"
    if summary_path.exists():
        summary_data = parse_summary(summary_path)
        if summary_data.get("status") == "FAILED":
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
