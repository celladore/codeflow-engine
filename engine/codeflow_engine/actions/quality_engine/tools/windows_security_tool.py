"""
Windows Security Tool - A comprehensive security scanning alternative to CodeQL for Windows.
"""

import asyncio
import json
from typing import Any

from codeflow_engine.actions.quality_engine.tools.tool_base import Tool


class WindowsSecurityTool(Tool):
    """
    A comprehensive security scanning tool for Windows that combines multiple security tools.
    This serves as an alternative to CodeQL on Windows systems.
    """

    def __init__(self) -> None:
        super().__init__()
        # Sized as a hang detector, not a performance budget. _run_bandit shells out to
        # `bandit -r .`, so runtime tracks the whole repo rather than max_files_per_run;
        # that measured 29-48s here, straddling the previous 30s limit.
        self.default_timeout = 120.0
        self.max_files_per_run = 50

    @property
    def name(self) -> str:
        return "windows_security"

    @property
    def description(self) -> str:
        return "Comprehensive security scanning for Windows using multiple tools (Bandit, Safety, etc.)"

    @property
    def category(self) -> str:
        return "security"

    def is_available(self) -> bool:
        """Check if Windows security tools are available."""
        # Check if we're on Windows and basic tools are available
        import platform

        if platform.system() != "Windows":
            return False
        return self.check_command_availability("bandit")

    def get_required_command(self) -> str | None:
        """Get the required command for this tool."""
        return "bandit"

    async def run(
        self, files: list[str], config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Run comprehensive security scanning using multiple tools.
        """
        if not files:
            return []

        all_issues = []

        try:
            # Run Bandit for Python security scanning (primary tool)
            bandit_issues = await self._run_bandit(files, config)
            all_issues.extend(bandit_issues)

            # Only run additional checks if we have time and files are limited
            if len(files) <= 10:
                additional_issues = await self._run_additional_checks(files, config)
                all_issues.extend(additional_issues)

        except Exception as e:
            all_issues.append({"error": f"Windows Security tool error: {e!s}"})

        return all_issues

    async def _run_bandit(
        self, files: list[str], config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Run Bandit security scanner with improved error handling."""
        try:
            # Filter for Python files
            python_files = [f for f in files if f.endswith(".py")]
            if not python_files:
                return []

            command = ["bandit", "-f", "json", "-r", "."]

            extra_args = config.get("bandit_args", [])
            command.extend(extra_args)

            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode not in [0, 1]:
                error_message = stderr.decode().strip()
                return [{"error": f"Bandit execution failed: {error_message}"}]

            if not stdout:
                return []

            try:
                output = json.loads(stdout)
                issues = []

                for result in output.get("results", []):
                    issues.append(
                        {
                            "filename": result.get("filename", "unknown"),
                            "line_number": result.get("line_number"),
                            "code": f"BANDIT_{result.get('issue_severity', 'UNKNOWN').upper()}",
                            "message": result.get("issue_text", "Security issue found"),
                            "severity": result.get("issue_severity", "medium"),
                            "details": {
                                "test_id": result.get("test_id"),
                                "test_name": result.get("test_name"),
                                "more_info": result.get("more_info", ""),
                            },
                        }
                    )

                return issues
            except json.JSONDecodeError:
                return [{"error": "Failed to parse Bandit JSON output"}]

        except Exception as e:
            return [{"error": f"Bandit execution error: {e!s}"}]

    async def _run_safety(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Run Safety for dependency vulnerability scanning with improved error handling."""
        try:
            command = ["safety", "check", "--json"]

            extra_args = config.get("safety_args", [])
            command.extend(extra_args)

            process = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode not in [0, 1]:
                error_message = stderr.decode().strip()
                return [{"error": f"Safety execution failed: {error_message}"}]

            if not stdout:
                return []

            try:
                output = json.loads(stdout)
                issues = []

                for vuln in output:
                    issues.append(
                        {
                            "filename": "requirements.txt",  # Dependency issues
                            "line_number": None,
                            "code": f"SAFETY_{vuln.get('severity', 'UNKNOWN').upper()}",
                            "message": f"Vulnerable dependency: {vuln.get('package', 'unknown')}",
                            "severity": vuln.get("severity", "medium"),
                            "details": {
                                "package": vuln.get("package"),
                                "installed_version": vuln.get("installed_version"),
                                "vulnerable_spec": vuln.get("vulnerable_spec"),
                                "description": vuln.get("description", ""),
                                "advisory": vuln.get("advisory", ""),
                            },
                        }
                    )

                return issues
            except json.JSONDecodeError:
                return [{"error": "Failed to parse Safety JSON output"}]

        except Exception as e:
            return [{"error": f"Safety execution error: {e!s}"}]

    async def _run_additional_checks(
        self, files: list[str], config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Run additional security checks with improved error handling."""
        issues = []

        # Check for common security anti-patterns (limit to first 10 files to prevent hanging)
        files_to_check = files[:10]  # Limit to prevent hanging on large codebases

        for file in files_to_check:
            if file.endswith(".py"):
                try:
                    file_issues = await self._check_python_security_patterns(
                        file, config
                    )
                    issues.extend(file_issues)
                except Exception as e:
                    issues.append(
                        {"error": f"Error checking security patterns in {file}: {e!s}"}
                    )

        return issues

    async def _check_python_security_patterns(
        self, file_path: str, config: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Check for common Python security anti-patterns."""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            issues = []

            # Check for hardcoded secrets (simplified check)
            if any(
                pattern in content.lower()
                for pattern in ["password =", "secret =", "key =", "token ="]
            ):
                issues.append(
                    {
                        "filename": file_path,
                        "line_number": None,
                        "code": "HARDCODED_SECRET",
                        "message": "Potential hardcoded secret detected",
                        "severity": "high",
                        "details": {
                            "pattern": "hardcoded_secret",
                            "recommendation": "Use environment variables or secure configuration management",
                        },
                    }
                )

            # Check for eval usage
            if "eval(" in content:
                issues.append(
                    {
                        "filename": file_path,
                        "line_number": None,
                        "code": "EVAL_USAGE",
                        "message": "eval() function usage detected - security risk",
                        "severity": "high",
                        "details": {
                            "pattern": "eval_usage",
                            "recommendation": "Avoid eval() - use ast.literal_eval() or other safe alternatives",
                        },
                    }
                )

            # Check for subprocess with shell=True
            if "subprocess" in content and "shell=True" in content:
                issues.append(
                    {
                        "filename": file_path,
                        "line_number": None,
                        "code": "SHELL_INJECTION",
                        "message": "subprocess with shell=True detected - potential shell injection risk",
                        "severity": "medium",
                        "details": {
                            "pattern": "shell_injection",
                            "recommendation": "Avoid shell=True, use list arguments instead",
                        },
                    }
                )

            return issues

        except Exception as e:
            return [
                {"error": f"Error checking security patterns in {file_path}: {e!s}"}
            ]
