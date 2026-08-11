"""
AI Analyzer for Quality Engine

AI-powered analysis of code quality issues.
"""

import asyncio
from dataclasses import dataclass
import os
from typing import Any

import structlog

from codeflow_engine.actions.llm.manager import ActionLLMProviderManager


logger = structlog.get_logger(__name__)


@dataclass
class CodeSuggestion:
    """Represents an AI-generated code improvement suggestion."""

    file_path: str
    line_number: int | None
    suggestion: str
    explanation: str
    confidence: float
    category: str  # e.g., 'performance', 'security', 'readability', etc.


class AICodeAnalyzer:
    """
    AI-powered code analyzer that leverages LLMs to provide intelligent code suggestions.

    Sluice tagging is not configured here. It belongs to the manager this analyzer is
    handed — `initialize_llm_manager` puts the gateway provider first, tagged
    `quality-analyzer`, and this analyzer is the same calling feature as the rest of
    the quality engine's AI analysis, so it shares that tag rather than adding a
    Prometheus series of its own.
    """

    def __init__(self, llm_manager: ActionLLMProviderManager | None = None):
        """
        Initialize the AI code analyzer.

        Args:
            llm_manager: LLM provider manager instance, as built by
                         `quality_engine.ai.initialize_llm_manager`. If None, AI
                         analysis reports itself unavailable.
        """
        self.llm_manager = llm_manager
        self._system_prompt = self._get_system_prompt()
        self.logger = structlog.get_logger(__name__)

    def _get_system_prompt(self) -> str:
        """Generate the system prompt for code analysis."""
        return (
            "You are CodeQualityGPT, an expert code analysis assistant specialized in "
            "identifying improvements, optimizations, and potential issues in code. "
            "Your task is to analyze code snippets and provide detailed, actionable feedback.\n\n"
            "For each code snippet, provide the following:\n\n"
            "1. A list of suggestions for improvement, including:\n"
            "   - The line number (if applicable)\n"
            "   - A clear description of the issue/improvement\n"
            "   - An explanation of why this is important\n"
            "   - A specific code example showing how to implement the suggestion\n"
            "   - A category for the suggestion (performance, security, readability, maintainability, etc.)\n"
            "   - A confidence level (0.0-1.0) indicating how certain you are about this suggestion\n\n"
            "2. A high-level summary of the code quality\n\n"
            "3. Priority issues that should be addressed first\n\n"
            "Format your response as a valid JSON object with the following structure:\n"
            "```json\n"
            "{\n"
            '  "suggestions": [\n'
            "    {\n"
            '      "line": 12,\n'
            '      "issue": "Unused variable",\n'
            '      "explanation": "The variable \'x\' is defined but never used, which adds unnecessary complexity.",\n'
            '      "example": "Remove the line: x = calculate_value()",\n'
            '      "category": "maintainability",\n'
            '      "confidence": 0.95\n'
            "    }\n"
            "  ],\n"
            '  "summary": "This code has good structure but contains a few unused variables and could benefit from better error handling.",\n'
            '  "priorities": ["Address security vulnerability in line 45", "Improve error handling throughout"]\n'
            "}\n"
            "```\n\n"
            "Each suggestion should be specific, actionable, and explain both what to change and why."
        )

    async def analyze_code(
        self,
        file_path: str,
        code_content: str,
        provider_name: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        Analyze code using the configured LLM provider.

        Args:
            file_path: Path to the file being analyzed
            code_content: Content of the file to analyze
            provider_name: Name of the LLM provider to use (defaults to system default)
            model: Model name to use (defaults to provider default)

        Returns:
            Dictionary containing suggestions, summary, and priorities
        """
        if not self.llm_manager:
            self.logger.warning("No LLM manager provided, AI analysis unavailable")
            return {
                "suggestions": [],
                "summary": "AI analysis unavailable - no LLM manager provided",
                "priorities": [],
            }

        # Create the messages for the LLM
        file_extension = os.path.splitext(file_path)[1]
        language = self._get_language_from_extension(file_extension)
        user_prompt = (
            f"Please analyze the following {language} code from file "
            f"'{file_path}'.\n\n```{language}\n{code_content}\n```"
        )

        # `provider` and `model` are omitted rather than set to None when
        # unspecified: the manager reads them with `.pop(key, default)`, so a
        # present-but-None key defeats its default instead of deferring to it — and
        # that default is the Sluice gateway when one is configured.
        request: dict[str, Any] = {
            "messages": [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,  # Lower temperature for more deterministic responses
            "max_tokens": 2000,
            # ✅ Validated and enforced JSON output per provider
            "response_format": {"type": "json"},
        }
        if provider_name:
            request["provider"] = provider_name
        if model:
            request["model"] = model

        try:
            self.logger.info(
                "Analyzing code with AI",
                file_path=file_path,
                provider=provider_name or "default",
            )
            response = self.llm_manager.complete(request)

            # LLMResponse is a dataclass and so always truthy; a failed call carries
            # `error` with empty content. Checking truthiness alone would send "" on
            # to the JSON parser and report a parse failure for what is really a
            # provider error — including the ADR 17 refusal of an untagged route.
            if not response or response.error or not response.content:
                self.logger.error(
                    "Failed to get AI response for code analysis",
                    file_path=file_path,
                    error=getattr(response, "error", None),
                )
                return {
                    "suggestions": [],
                    "summary": "AI analysis failed - no response from LLM",
                    "priorities": [],
                }

            # Parse the JSON response
            try:
                import json

                # The content may contain markdown code blocks, so we need to extract just the JSON
                content = response.content
                # Extract JSON content from possible markdown code blocks
                if "```json" in content:
                    json_content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_content = content.split("```")[1].strip()
                else:
                    json_content = content

                result: dict[str, Any] = json.loads(json_content)
                self.logger.info(
                    "Successfully analyzed code with AI",
                    file_path=file_path,
                    suggestion_count=len(result.get("suggestions", [])),
                )
                return result
            except Exception as e:
                self.logger.exception(
                    "Failed to parse AI response",
                    error=str(e),
                    content=response.content,
                )
                return {
                    "suggestions": [],
                    "summary": f"Failed to parse AI response: {response.content[:100]}...",
                    "priorities": [],
                }

        except Exception as e:
            self.logger.exception(
                "Error during AI code analysis", error=str(e), file_path=file_path
            )
            return {
                "suggestions": [],
                "summary": f"AI analysis error: {e!s}",
                "priorities": [],
            }

    async def analyze_files(
        self,
        files: list[str],
        provider_name: str | None = None,
        model: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        """
        Analyze multiple files in parallel.

        Args:
            files: List of file paths to analyze
            provider_name: LLM provider to use
            model: Model to use

        Returns:
            Dictionary mapping file paths to their analysis results
        """
        results = {}
        tasks = []

        for file_path in files:
            try:
                with open(file_path) as f:
                    code_content = f.read()

                task = asyncio.create_task(
                    self.analyze_code(file_path, code_content, provider_name, model)
                )
                tasks.append((file_path, task))
            except Exception as e:
                self.logger.exception(
                    "Error reading file for AI analysis",
                    file_path=file_path,
                    error=str(e),
                )
                results[file_path] = {
                    "suggestions": [],
                    "summary": f"Error reading file: {e!s}",
                    "priorities": [],
                }

        # Wait for all tasks to complete
        for file_path, task in tasks:
            try:
                results[file_path] = await task
            except Exception as e:
                self.logger.exception(
                    "Error in AI analysis task", file_path=file_path, error=str(e)
                )
                results[file_path] = {
                    "suggestions": [],
                    "summary": f"Error in analysis: {e!s}",
                    "priorities": [],
                }

        return results

    def _get_language_from_extension(self, extension: str) -> str:
        """Map file extension to language name for code blocks."""
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".java": "java",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".c": "c",
            ".cpp": "cpp",
            ".cs": "csharp",
            ".md": "markdown",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".json": "json",
            ".sh": "bash",
            ".css": "css",
            ".html": "html",
            ".xml": "xml",
        }
        return mapping.get(extension, "text")

    def convert_to_tool_results(
        self, ai_results: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Convert AI analysis results to the format expected by the quality engine.

        Args:
            ai_results: Dictionary mapping file paths to their AI analysis results

        Returns:
            Dictionary formatted for the quality engine
        """
        issues = []
        files_with_issues = []

        for file_path, result in ai_results.items():
            has_issues = False

            for suggestion in result.get("suggestions", []):
                issues.append(
                    {
                        "file": file_path,
                        "line": suggestion.get("line", 0),
                        "message": suggestion.get("issue", "Unknown issue"),
                        "category": suggestion.get("category", "general"),
                        "explanation": suggestion.get("explanation", ""),
                        "example": suggestion.get("example", ""),
                        "confidence": suggestion.get("confidence", 0.0),
                    }
                )
                has_issues = True

            if has_issues:
                files_with_issues.append(file_path)

        # Create a summary from all file summaries
        summaries = [
            result.get("summary", "")
            for result in ai_results.values()
            if result.get("summary")
        ]
        summary = "AI Analysis Results:\n\n" + "\n\n".join(summaries)

        return {
            "issues": issues,
            "files_with_issues": files_with_issues,
            "summary": summary,
        }


class AIAnalyzer:
    """Backward-compatible facade for legacy AI quality callers and tests."""

    async def analyze_code_quality(self, files: list[str]) -> dict[str, Any]:
        return await self._run_provider_analysis(files, analysis_type="code_quality")

    async def analyze_security_issues(self, files: list[str]) -> dict[str, Any]:
        return await self._run_provider_analysis(files, analysis_type="security")

    async def analyze_performance_issues(self, files: list[str]) -> dict[str, Any]:
        return await self._run_provider_analysis(files, analysis_type="performance")

    async def analyze_best_practices(self, files: list[str]) -> dict[str, Any]:
        return await self._run_provider_analysis(files, analysis_type="best_practices")

    async def analyze(self, files: list[str], mode: str) -> dict[str, Any]:
        return await self._run_provider_analysis(files, mode=mode)

    async def analyze_with_context(
        self, files: list[str], context: dict[str, Any]
    ) -> dict[str, Any]:
        return await self._run_provider_analysis(files, context=context)

    def _get_ai_provider(self, provider_name: str = "openai") -> Any | None:
        if provider_name == "openai" and os.getenv("OPENAI_API_KEY"):
            return object()
        if provider_name == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
            return object()
        return None

    async def _run_provider_analysis(
        self, files: list[str], **kwargs: Any
    ) -> dict[str, Any]:
        provider = self._get_ai_provider(kwargs.get("provider_name", "openai"))
        if provider is None:
            return {"success": False, "error": "No AI provider available"}

        try:
            analyze = getattr(provider, "analyze")
            result = await analyze(files=files, **kwargs)
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "suggestions": [],
                "issues": [],
            }

        if isinstance(result, dict):
            result.setdefault("success", True)
            return result
        return {"success": True, "result": result}
