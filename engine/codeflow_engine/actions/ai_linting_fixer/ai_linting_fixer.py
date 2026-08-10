"""
AI Linting Fixer

A comprehensive AI-powered linting fixer that automatically detects and fixes Python code issues
using advanced language models and specialized agents.
"""

import logging
import os
import time
from typing import Any

from codeflow_engine.actions.ai_linting_fixer.ai_agent_manager import AIAgentManager
from codeflow_engine.actions.ai_linting_fixer.code_analyzer import CodeAnalyzer
from codeflow_engine.actions.ai_linting_fixer.detection import IssueDetector
from codeflow_engine.actions.ai_linting_fixer.display import (
    AILintingFixerDisplay,
    DisplayConfig,
)
from codeflow_engine.actions.ai_linting_fixer.error_handler import ErrorHandler
from codeflow_engine.actions.ai_linting_fixer.file_manager import FileManager
from codeflow_engine.actions.ai_linting_fixer.issue_converter import (
    convert_detection_issue_to_model_issue,
)
from codeflow_engine.actions.ai_linting_fixer.issue_fixer import IssueFixer
from codeflow_engine.actions.ai_linting_fixer.models import (
    AILintingFixerInputs,
    AILintingFixerOutputs,
)
from codeflow_engine.actions.ai_linting_fixer.performance_tracker import (
    PerformanceTracker,
)
from codeflow_engine.actions.llm.manager import ActionLLMProviderManager
from codeflow_engine.core.llm.sluice import SluiceAgent, SluiceConfig

logger = logging.getLogger(__name__)


class AILintingFixer:
    """Main AI Linting Fixer class that orchestrates all components."""

    database: Any = None

    def __init__(self, display_config: DisplayConfig | None = None):
        """Initialize the AI Linting Fixer with all components."""
        # Set logging levels to ERROR by default to prevent clutter
        logging.getLogger("codeflow_engine.actions.ai_linting_fixer").setLevel(
            logging.ERROR
        )
        logging.getLogger("codeflow_engine.actions.llm").setLevel(logging.ERROR)
        logging.getLogger("httpx").setLevel(logging.ERROR)

        # Initialize display
        self.display = AILintingFixerDisplay(display_config)

        # Initialize core components
        self.performance_tracker = PerformanceTracker()
        self.error_handler = ErrorHandler()

        # Get Azure OpenAI configuration
        azure_endpoint = os.getenv(
            "AZURE_OPENAI_ENDPOINT", "https://<your-azure-openai-endpoint>/"
        )
        azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")

        # Soft validation: check if Azure OpenAI is properly configured
        azure_configured = (
            azure_api_key
            and azure_endpoint
            and "<" not in azure_endpoint
            and "your-azure-openai-endpoint" not in azure_endpoint
        )

        # Build LLM configuration with fallback providers
        providers_config: dict[str, dict[str, str | None]] = {}
        llm_config: dict[str, Any] = {
            "default_provider": None,  # Will be set based on available providers
            "fallback_order": [],  # Will be populated based on available providers
            "providers": providers_config,
        }

        # Prefer the Sluice gateway when configured: it centralises spend tracking
        # and enforces per-key budgets. Added before the vendor providers because the
        # default is derived from insertion order below; those stay as fallbacks for
        # deployments with no gateway. Tagged `linting-fixer` per Sluice ADR 17.
        if SluiceConfig.from_env() is not None:
            providers_config["sluice"] = {"agent": SluiceAgent.LINTING_FIXER}
            logger.info("Sluice gateway provider configured")

        # Add Azure OpenAI provider only if properly configured
        if azure_configured:
            providers_config["azure_openai"] = {
                "azure_endpoint": azure_endpoint,
                "api_key": azure_api_key,
                "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
                "deployment_name": os.getenv(
                    "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo"
                ),
            }
            logger.info("Azure OpenAI provider configured successfully")
        else:
            # Log warnings for missing Azure configuration
            if not azure_api_key:
                logger.warning(
                    "Azure OpenAI API key not configured. "
                    "Set AZURE_OPENAI_API_KEY environment variable to enable Azure OpenAI provider."
                )
            if (
                not azure_endpoint
                or "<" in azure_endpoint
                or "your-azure-openai-endpoint" in azure_endpoint
            ):
                logger.warning(
                    "Azure OpenAI endpoint not properly configured. "
                    "Set AZURE_OPENAI_ENDPOINT environment variable to enable "
                    "Azure OpenAI provider. Current value: %s",
                    azure_endpoint,
                )
            logger.info("Azure OpenAI provider skipped due to missing configuration")

        # Add other providers for fallback
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            providers_config["openai"] = {
                "api_key": openai_api_key,
            }
            logger.info("OpenAI provider configured")

        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_api_key:
            providers_config["anthropic"] = {
                "api_key": anthropic_api_key,
            }
            logger.info("Anthropic provider configured")

        # Determine default provider and fallback order based on available providers
        available_providers = list(providers_config.keys())
        if available_providers:
            # Set default provider to the first available one
            llm_config["default_provider"] = available_providers[0]
            # Set fallback order to all available providers
            llm_config["fallback_order"] = available_providers
            logger.info("Default provider set to: %s", llm_config["default_provider"])
        else:
            # No providers available - will be handled gracefully
            logger.warning("No LLM providers configured. AI features will be disabled.")
            logger.warning("To enable AI features, configure at least one of:")
            logger.warning("  - AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT")
            logger.warning("  - OPENAI_API_KEY")
            logger.warning("  - ANTHROPIC_API_KEY")

        # Log final configuration
        configured_providers = list(providers_config.keys())
        logger.info(
            "LLM configuration: default_provider=%s, fallback_order=%s, "
            "configured_providers=%s",
            llm_config["default_provider"],
            llm_config["fallback_order"],
            configured_providers,
        )

        # Initialize LLM manager with validation
        self.llm_manager: ActionLLMProviderManager | None
        if llm_config["default_provider"] is not None:
            self.llm_manager = ActionLLMProviderManager(
                llm_config, display=self.display
            )
            logger.info(
                "LLM manager initialized successfully with provider: %s",
                llm_config["default_provider"],
            )
        else:
            self.llm_manager = None
            logger.warning("LLM manager not initialized - no providers available")

        # Initialize specialized components
        self.issue_detector = IssueDetector()
        self.code_analyzer = CodeAnalyzer()

        # Initialize AI agent manager only if LLM manager is available
        if self.llm_manager is not None:
            self.ai_agent_manager: AIAgentManager | None
            self.ai_agent_manager = AIAgentManager(
                self.llm_manager, self.performance_tracker
            )
            logger.info("AI agent manager initialized successfully")
        else:
            self.ai_agent_manager = None
            logger.warning(
                "AI agent manager not initialized - no LLM provider available"
            )
        self.file_manager = FileManager()

        # Initialize issue fixer only if AI agent manager is available
        if self.ai_agent_manager is not None:
            self.issue_fixer: IssueFixer | None
            self.issue_fixer = IssueFixer(
                self.ai_agent_manager, self.file_manager, self.error_handler
            )
            logger.info("Issue fixer initialized successfully")
        else:
            self.issue_fixer = None
            logger.warning("Issue fixer not initialized - no AI capabilities available")

        # Initialize database for logging interactions
        try:
            from codeflow_engine.actions.ai_linting_fixer.database import (
                AIInteractionDB,
            )

            self.database = AIInteractionDB()
            if self.issue_fixer is not None:
                self.issue_fixer.database = self.database
        except Exception as e:
            logger.warning("Failed to initialize database: %s", e)
            self.database = None

        logger.info("AI Linting Fixer initialized with modular components")

    def _analyze_error(self, error: Exception) -> dict[str, Any]:
        """Analyze an error and provide detailed information for drill-down."""
        error_type = type(error).__name__
        error_msg = str(error)

        analysis: dict[str, Any] = {
            "error_type": error_type,
            "error_message": error_msg,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "severity": "high" if "validation" in error_type.lower() else "medium",
            "category": self._categorize_error(error),
            "context": self._get_error_context(error),
            "stack_trace": self._get_stack_trace(error),
            "suggested_actions": [],
        }

        # Add specific analysis based on error type
        if "validation" in error_type.lower():
            analysis.update(self._analyze_validation_error(error))
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            analysis.update(self._analyze_connection_error(error))
        elif "permission" in error_msg.lower():
            analysis.update(self._analyze_permission_error(error))

        return analysis

    def _categorize_error(self, error: Exception) -> str:
        """Categorize the error for better understanding."""
        error_msg = str(error).lower()

        if "validation" in error_msg:
            return "data_validation"
        if "connection" in error_msg or "timeout" in error_msg:
            return "network"
        if "permission" in error_msg or "access" in error_msg:
            return "permission"
        if "file" in error_msg or "path" in error_msg:
            return "file_system"
        if "api" in error_msg or "key" in error_msg:
            return "api"
        return "general"

    def _get_error_context(self, _error: Exception) -> dict[str, Any]:
        """Get context information about when/where the error occurred."""
        return {
            "session_id": getattr(self, "session_id", "unknown"),
            "processing_stage": "workflow_execution",
            "components_initialized": {
                "display": hasattr(self, "display"),
                "llm_manager": hasattr(self, "llm_manager"),
                "issue_detector": hasattr(self, "issue_detector"),
                "file_manager": hasattr(self, "file_manager"),
                "database": hasattr(self, "database") and self.database is not None,
            },
        }

    def _get_stack_trace(self, error: Exception) -> str:
        """Get a formatted stack trace for the error."""
        import traceback

        return "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )

    def _analyze_validation_error(self, error: Exception) -> dict[str, Any]:
        """Analyze validation errors specifically."""
        error_msg = str(error)

        # Extract field names from validation error
        import re

        field_matches = re.findall(r"'([^']+)'", error_msg)

        return {
            "validation_details": {
                "missing_fields": field_matches,
                "error_pattern": "missing_required_fields",
                "model_affected": "AILintingFixerOutputs",
            },
            "suggested_actions": [
                "Check that all required fields are being set in the output creation",
                "Verify the AILintingFixerOutputs model definition",
                "Use --verbose flag for detailed error information",
            ],
        }

    def _analyze_connection_error(self, _error: Exception) -> dict[str, Any]:
        """Analyze connection-related errors."""
        return {
            "connection_details": {
                "error_type": "network_timeout_or_connection_failure",
                "affected_component": "LLM provider",
            },
            "suggested_actions": [
                "Check your internet connection",
                "Verify API key is valid and has sufficient credits",
                "Try using a different LLM provider",
                "Check if the service is experiencing downtime",
            ],
        }

    def _analyze_permission_error(self, _error: Exception) -> dict[str, Any]:
        """Analyze permission-related errors."""
        return {
            "permission_details": {
                "error_type": "file_or_directory_access_denied",
                "affected_operation": "file reading/writing",
            },
            "suggested_actions": [
                "Check file permissions in the target directory",
                "Ensure you have write access to the backup directory",
                "Run with elevated permissions if necessary",
                "Verify the file paths are correct",
            ],
        }

    def _get_error_recovery_suggestions(
        self, error_details: dict[str, Any]
    ) -> list[str]:
        """Get specific recovery suggestions based on error analysis."""
        suggestions: list[str] = []

        # Add general suggestions
        suggestions.extend(
            (
                "Use --verbose flag for detailed error information",
                "Check the logs for additional context",
            )
        )

        # Add specific suggestions based on error category
        category = error_details.get("category", "general")
        if category == "data_validation":
            suggestions.extend(
                [
                    "Verify input parameters are correct",
                    "Check model field definitions",
                    "Ensure all required fields are provided",
                ]
            )
        elif category == "network":
            suggestions.extend(
                [
                    "Check internet connection",
                    "Verify API credentials",
                    "Try again in a few minutes",
                ]
            )
        elif category == "permission":
            suggestions.extend(
                [
                    "Check file permissions",
                    "Verify directory access rights",
                    "Run with appropriate permissions",
                ]
            )

        # Add suggestions from error analysis
        if "suggested_actions" in error_details:
            suggestions.extend(error_details["suggested_actions"])

        return suggestions

    def is_ai_available(self) -> bool:
        """Check if AI features are available (LLM provider configured)."""
        return (
            self.llm_manager is not None
            and self.ai_agent_manager is not None
            and self.issue_fixer is not None
        )

    def get_ai_availability_message(self) -> str:
        """Get a user-friendly message about AI availability and configuration instructions."""
        if self.is_ai_available():
            return "AI features are available and ready to use."

        message = (
            "AI features are not available. To enable AI-powered linting fixes, "
            "configure at least one LLM provider:\n\n"
        )
        message += "1. OpenAI: Set OPENAI_API_KEY environment variable\n"
        message += "2. Anthropic: Set ANTHROPIC_API_KEY environment variable\n"
        message += (
            "3. Azure OpenAI: Set AZURE_OPENAI_API_KEY and "
            "AZURE_OPENAI_ENDPOINT environment variables\n\n"
        )
        message += (
            "Without AI providers, only issue detection will be available "
            "(no automatic fixes)."
        )
        return message

    def run(self, inputs: AILintingFixerInputs) -> AILintingFixerOutputs:
        """Run the complete AI linting fixer workflow."""
        start_time = time.time()

        try:
            # Configure display based on inputs
            if hasattr(inputs, "verbose") and inputs.verbose:
                self.display.set_verbose(True)
                # Set logging to DEBUG for verbose mode
                logging.getLogger("codeflow_engine.actions.ai_linting_fixer").setLevel(
                    logging.DEBUG
                )
                logging.getLogger("codeflow_engine.actions.llm").setLevel(logging.DEBUG)
                logging.getLogger("httpx").setLevel(logging.DEBUG)
            elif hasattr(inputs, "quiet") and inputs.quiet:
                self.display.set_quiet(True)
                # Set logging to ERROR only for quiet mode
                logging.getLogger("codeflow_engine.actions.ai_linting_fixer").setLevel(
                    logging.ERROR
                )
                logging.getLogger("codeflow_engine.actions.llm").setLevel(logging.ERROR)
                logging.getLogger("httpx").setLevel(logging.ERROR)

            # Show session start
            session_id = f"session_{int(start_time)}"
            self.session_id = session_id
            self.display.operation.show_session_start(inputs, session_id)

            # Use display for user-facing messages instead of logger
            self.display.error.show_info("Starting AI Linting Fixer workflow")

            # Step 1: Detect linting issues
            self.display.operation.show_detection_progress(inputs.target_path)

            issues = self.issue_detector.detect_issues(inputs.target_path)

            # Filter issues by specified types
            if inputs.fix_types:
                filtered_issues = [
                    issue for issue in issues if issue.error_code in inputs.fix_types
                ]
                self.display.error.show_info(
                    f"Filtered to {len(filtered_issues)} issues of specified types"
                )
            else:
                filtered_issues = issues

            # Calculate unique files for accurate reporting
            unique_files_count = len({issue.file_path for issue in filtered_issues})
            self.display.operation.show_detection_results(
                filtered_count=len(filtered_issues),
                total_count=len(issues),
                unique_files_count=unique_files_count,
            )

            if not filtered_issues:
                self.display.error.show_info("No issues found to fix")
                return AILintingFixerOutputs(
                    success=True,
                    total_issues_found=len(issues),
                    issues_fixed=0,
                    files_modified=[],
                    summary="No linting issues found to fix",
                    total_issues_detected=len(issues),
                    issues_processed=0,
                    issues_failed=0,
                    total_duration=time.time() - start_time,
                    backup_files_created=0,
                    agent_stats={},
                    queue_stats={},
                    session_id=session_id,
                    processing_mode="standalone",
                    dry_run=getattr(inputs, "dry_run", False),
                )

            # Step 2: Create backups if requested
            backup_count = 0
            if hasattr(inputs, "create_backups") and inputs.create_backups:
                # Get unique files that will be modified
                unique_files = list({issue.file_path for issue in filtered_issues})
                self.display.operation.show_backup_creation(len(unique_files))
                backup_count = self.file_manager.create_backups(unique_files)
                self.display.error.show_info(f"Created {backup_count} backup files")

            # Step 3: Check AI availability before processing
            if not self.is_ai_available():
                self.display.error.show_warning(self.get_ai_availability_message())
                return AILintingFixerOutputs(
                    success=False,
                    total_issues_found=len(issues),
                    issues_fixed=0,
                    files_modified=[],
                    summary="AI features not available - no LLM providers configured",
                    total_issues_detected=len(issues),
                    issues_processed=0,
                    issues_failed=len(filtered_issues),
                    total_duration=time.time() - start_time,
                    backup_files_created=backup_count,
                    agent_stats={},
                    queue_stats={},
                    session_id=session_id,
                    processing_mode="detection_only",
                    dry_run=getattr(inputs, "dry_run", False),
                )

            # Step 4: Process issues with AI
            self.display.operation.show_processing_start(len(filtered_issues))

            # Limit to max_fixes
            issues_to_process = filtered_issues[: inputs.max_fixes]
            self.display.error.show_info(
                f"Starting AI-powered fix for {len(issues_to_process)} issues"
            )

            processed_issues = []
            failed_issues = []
            files_modified = set()

            for i, issue in enumerate(issues_to_process, 1):
                self.display.operation.show_processing_progress(
                    i,
                    len(issues_to_process),
                    convert_detection_issue_to_model_issue(issue),
                )

                try:
                    # Read current file content
                    content = self.file_manager.read_file(issue.file_path)
                    if content is None:
                        self.display.error.show_warning(
                            f"Could not read file: {issue.file_path}"
                        )
                        failed_issues.append(issue)
                        continue

                    # Fix the issue (with additional safety check)
                    if self.issue_fixer is None:
                        self.display.error.show_error(
                            "Issue fixer not available - AI features not configured"
                        )
                        failed_issues.append(issue)
                        continue

                    result = self.issue_fixer.fix_single_issue(
                        file_path=issue.file_path,
                        content=content,
                        issue=convert_detection_issue_to_model_issue(issue),
                        provider=inputs.provider,
                        model=inputs.model,
                    )

                    if result.get("success", False):
                        # Write the fixed content
                        if not hasattr(inputs, "dry_run") or not inputs.dry_run:
                            success = self.file_manager.write_file(
                                issue.file_path, result["content"]
                            )
                            if success:
                                files_modified.add(issue.file_path)
                                processed_issues.append(issue)
                                confidence = result.get("confidence", 0.0)
                                self.display.error.show_info(
                                    f"✅ Fixed {issue.error_code} in {issue.file_path} "
                                    f"(confidence: {confidence:.3f})"
                                )
                            else:
                                failed_issues.append(issue)
                                self.display.error.show_error(
                                    f"Failed to write fixed content to {issue.file_path}"
                                )
                        else:
                            processed_issues.append(issue)
                            self.display.error.show_info(
                                f"🔍 Would fix {issue.error_code} in {issue.file_path} (dry run)"
                            )
                    else:
                        failed_issues.append(issue)
                        error_msg = result.get("error", "Unknown error")
                        self.display.error.show_warning(
                            f"❌ Failed to fix {issue.error_code}: {error_msg}"
                        )

                except Exception as e:
                    failed_issues.append(issue)
                    self.display.error.show_error(
                        f"Error processing {issue.error_code}: {e!s}"
                    )

            # Show processing results
            self.display.operation.show_processing_results(
                len(processed_issues), len(failed_issues)
            )

            # Generate results
            processing_duration = time.time() - start_time

            # Get performance metrics with defensive guard
            get_perf = getattr(
                self.performance_tracker, "get_performance_summary", None
            )
            if callable(get_perf):
                performance_summary = get_perf()
            else:
                performance_summary = {"agent_performance": {}, "queue_statistics": {}}

            # Create suggestions
            suggestions: list[str] = []
            if failed_issues:
                suggestions.append(
                    "Try increasing --max-fixes if you want to process more issues"
                )
            suggestions.append(
                "Check if the specified fix types match available issues"
            )
            if hasattr(inputs, "verbose") and not inputs.verbose:
                suggestions.append("Use --verbose for detailed performance metrics")
            suggestions.append("Use --db-stats to view database statistics")

            # Create output
            outputs = AILintingFixerOutputs(
                success=len(failed_issues) == 0,
                total_issues_found=len(issues),
                issues_fixed=len(processed_issues),
                files_modified=list(files_modified),
                summary=f"Fixed {len(processed_issues)} out of {len(issues)} issues",
                total_issues_detected=len(issues),
                issues_processed=len(processed_issues),
                issues_failed=len(failed_issues),
                total_duration=processing_duration,
                backup_files_created=backup_count,
                agent_stats=performance_summary.get("agent_performance", {}),
                queue_stats=performance_summary.get("queue_statistics", {}),
                session_id=session_id,
                processing_mode="standalone",
                dry_run=getattr(inputs, "dry_run", False),
            )

            # Show results
            self.display.results.show_results_summary(outputs)
            self.display.results.show_agent_performance(outputs.agent_stats)
            self.display.results.show_queue_statistics(outputs.queue_stats)
            self.display.results.show_suggestions(suggestions)

            return outputs  # noqa: TRY300

        except Exception as e:
            # Enhanced error handling with drill-down capability
            error_details = self._analyze_error(e)
            self.display.error.show_error(f"Error in AI Linting Fixer workflow: {e!s}")

            # Show detailed error information
            if hasattr(inputs, "verbose") and inputs.verbose:
                self.display.error.show_error_details(error_details)

            # Show recovery suggestions
            suggestions = self._get_error_recovery_suggestions(error_details)
            self.display.error.show_suggested_actions(suggestions)

            raise
        finally:
            # Cleanup
            logger.info("AI Linting Fixer resources cleaned up")

    def __enter__(self) -> "AILintingFixer":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Context manager exit."""
        try:
            # End performance tracking
            if hasattr(self.performance_tracker, "end_session"):
                self.performance_tracker.end_session()

            # Export final metrics
            if hasattr(self.performance_tracker, "export_metrics"):
                self.performance_tracker.export_metrics()

            # Use display module for user-facing messages
            if self.display:
                self.display.error.show_info("🔧 AI Linting Fixer resources cleaned up")
            else:
                logger.info("AI Linting Fixer resources cleaned up")

        except Exception as e:
            if self.display:
                self.display.error.show_warning(f"⚠️ Error during cleanup: {e}")
            else:
                logger.exception("Error during cleanup")


# Convenience functions for backward compatibility
def create_ai_linting_fixer(
    display_config: DisplayConfig | None = None,
) -> AILintingFixer:
    """Create an AI linting fixer with default configuration."""
    return AILintingFixer(display_config=display_config)


def run_ai_linting_fixer(
    target_path: str,
    fix_types: list[str] | None = None,
    max_fixes: int = 10,
    provider: str | None = None,
    model: str | None = None,
    max_workers: int = 4,
) -> AILintingFixerOutputs:
    """Run the AI linting fixer with simple parameters."""
    inputs = AILintingFixerInputs(
        target_path=target_path,
        fix_types=fix_types or ["E501", "F401", "F841", "E722"],
        max_fixes=max_fixes,
        provider=provider,
        model=model,
        max_workers=max_workers,
    )

    fixer = AILintingFixer()
    return fixer.run(inputs)
