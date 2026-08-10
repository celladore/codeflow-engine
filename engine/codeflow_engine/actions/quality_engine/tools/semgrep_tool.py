"""
Semgrep Tool - Cross-platform static analysis for security and code quality.
"""

import asyncio
import json
from typing import Any

from codeflow_engine.actions.quality_engine.tools.tool_base import Tool


class SemgrepTool(Tool):
    """
    Semgrep static analysis tool for comprehensive security and code quality scanning.
    Cross-platform and works well on Windows, Linux, and macOS.
    """

    def __init__(self) -> None:
        super().__init__()
        # Sized as a hang detector, not a performance budget. Semgrep's cost here is
        # dominated by registry rule loading (the default rules="auto" config sends no
        # --config, so rules are fetched per run), which measured 50-110s even for a
        # single file; a full 200-file scan measured 137-332s. Anything under that turns
        # every semgrep run into a timeout error with zero findings.
        self.default_timeout = 600.0
        self.max_files_per_run = 200

    @property
    def name(self) -> str:
        return "semgrep"

    @property
    def description(self) -> str:
        return "Cross-platform static analysis for security vulnerabilities and code quality issues"

    @property
    def category(self) -> str:
        return "security"

    def is_available(self) -> bool:
        """Check if semgrep command is available."""
        return self.check_command_availability("semgrep")

    def get_required_command(self) -> str | None:
        """Get the required command for this tool."""
        return "semgrep"

    async def run(
        self, files: list[str], config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Run Semgrep on the specified files.
        """
        if not files:
            return []

        # Limit the number of files to prevent timeouts
        files_to_check = files[: self.max_files_per_run]

        # Build the command
        command = ["semgrep", "--json", "--quiet", *files_to_check]

        # Add configuration options
        rules = config.get("rules", "auto")
        if rules != "auto":
            command.extend(["--config", rules])

        extra_args = config.get("args", [])
        command.extend(extra_args)

        try:
            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            # Semgrep returns 0 for no issues, 1 for issues found
            if process.returncode not in [0, 1]:
                error_message = stderr.decode().strip()
                return [{"error": f"Semgrep execution failed: {error_message}"}]

            if not stdout:
                return []

            try:
                results = json.loads(stdout)
                return results.get("results", [])
            except json.JSONDecodeError:
                return [{"error": "Failed to parse semgrep JSON output"}]
        except TimeoutError:
            return [{"error": "Semgrep execution timed out"}]
        except Exception as e:
            return [{"error": f"Semgrep execution error: {e!s}"}]

    def _parse_semgrep_output(self, output: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Parse Semgrep JSON output and convert to standard issue format.
        """
        issues = []

        # Handle results array
        results = output.get("results", [])

        for result in results:
            # Extract location information
            path = result.get("path", "unknown")
            start_line = result.get("start", {}).get("line")
            end_line = result.get("end", {}).get("line")
            start_col = result.get("start", {}).get("col")
            end_col = result.get("end", {}).get("col")

            # Extract message and rule information
            message = result.get("message", "Semgrep issue found")
            rule_id = result.get("check_id", "unknown")
            severity = result.get("extra", {}).get("severity", "medium")

            # Extract additional details
            extra = result.get("extra", {})
            metadata = extra.get("metadata", {})

            # Determine issue category based on rule ID
            category = self._determine_category(rule_id, metadata)

            issues.append(
                {
                    "filename": path,
                    "line_number": start_line,
                    "end_line": end_line,
                    "column_number": start_col,
                    "end_column": end_col,
                    "code": rule_id,
                    "message": message,
                    "severity": severity.lower(),
                    "details": {
                        "rule_id": rule_id,
                        "rule_name": extra.get("rule_name", "Unknown"),
                        "category": category,
                        "confidence": extra.get("confidence", "medium"),
                        "impact": metadata.get("impact", ""),
                        "cwe": metadata.get("cwe", []),
                        "owasp": metadata.get("owasp", []),
                        "references": metadata.get("references", []),
                        "fix": extra.get("fix", ""),
                        "fix_regex": extra.get("fix_regex", {}),
                    },
                }
            )

        return issues

    def _determine_category(self, rule_id: str, metadata: dict[str, Any]) -> str:
        """
        Determine the category of an issue based on rule ID and metadata.
        """
        # Check metadata first
        if metadata.get("category"):
            return metadata["category"]

        # Check for security-related patterns
        security_keywords = [
            "security",
            "vulnerability",
            "injection",
            "xss",
            "sqli",
            "rce",
            "authentication",
            "authorization",
            "crypto",
            "encryption",
        ]

        if any(keyword in rule_id.lower() for keyword in security_keywords):
            return "security"

        # Check for performance patterns
        performance_keywords = [
            "performance",
            "efficiency",
            "complexity",
            "memory",
            "cpu",
        ]

        if any(keyword in rule_id.lower() for keyword in performance_keywords):
            return "performance"

        # Check for maintainability patterns
        maintainability_keywords = [
            "maintainability",
            "readability",
            "style",
            "convention",
            "best-practice",
        ]

        if any(keyword in rule_id.lower() for keyword in maintainability_keywords):
            return "maintainability"

        # Check for bug patterns
        bug_keywords = ["bug", "error", "exception", "null", "undefined", "type"]

        if any(keyword in rule_id.lower() for keyword in bug_keywords):
            return "bug"

        # Default category
        return "general"

    def get_default_config(self) -> dict[str, Any]:
        """
        Get default configuration for Semgrep.
        """
        return {
            "rules": "auto",  # Use Semgrep's auto-detection
            "severity": "INFO,WARNING,ERROR",
            "strict": False,
            "verbose": False,
            "categories": ["security", "performance", "maintainability", "bug"],
        }

    def get_supported_languages(self) -> list[str]:
        """
        Get list of languages supported by Semgrep.
        """
        return [
            "python",
            "javascript",
            "typescript",
            "java",
            "go",
            "ruby",
            "php",
            "c",
            "cpp",
            "csharp",
            "rust",
            "kotlin",
            "scala",
            "swift",
            "yaml",
            "json",
            "docker",
            "terraform",
            "bash",
            "powershell",
        ]

    def get_rule_categories(self) -> dict[str, list[str]]:
        """
        Get available rule categories and their descriptions.
        """
        return {
            "security": [
                "OWASP Top 10 vulnerabilities",
                "Common security anti-patterns",
                "Authentication and authorization issues",
                "Input validation problems",
                "Cryptographic vulnerabilities",
            ],
            "performance": [
                "Performance anti-patterns",
                "Memory leaks and inefficiencies",
                "Algorithm complexity issues",
                "Resource management problems",
            ],
            "maintainability": [
                "Code style and conventions",
                "Best practices violations",
                "Code complexity issues",
                "Documentation problems",
            ],
            "bug": [
                "Common programming errors",
                "Type safety issues",
                "Exception handling problems",
                "Logic errors",
            ],
        }
