"""
Workflow Orchestrator for AI Linting Fixer

This module contains the main workflow orchestration logic that was
previously in the main function, now properly separated and focused.
"""

import logging
import os
from typing import Any, cast

from codeflow_engine.actions.ai_linting_fixer.core import AILintingFixer
from codeflow_engine.actions.ai_linting_fixer.detection import IssueDetector
from codeflow_engine.actions.ai_linting_fixer.display import (
    DisplayConfig,
    OutputMode,
    get_display,
)
from codeflow_engine.actions.ai_linting_fixer.error_handler import ErrorRecoveryStrategy
from codeflow_engine.actions.ai_linting_fixer.models import (
    AILintingFixerInputs,
    AILintingFixerOutputs,
    LintingIssue,
    create_empty_outputs,
)
from codeflow_engine.core.llm.sluice import SluiceAgent, SluiceConfig
from codeflow_engine.workflows.error_handler_workflow import handle_error_with_workflow
from codeflow_engine.actions.llm.manager import (
    ActionLLMProviderManager as LLMProviderManager,
)

logger = logging.getLogger(__name__)

# Constants
DEFAULT_SUCCESS_RATE_THRESHOLD = 0.5


class WorkflowOrchestrator:
    """
    Orchestrates the main AI linting workflow.

    This class handles the high-level flow of:
    1. Issue detection
    2. Issue queuing
    3. Issue processing
    4. Results generation
    """

    def __init__(self, display_config: DisplayConfig):
        """Initialize the workflow orchestrator."""
        self.display = get_display(display_config)
        self.issue_detector = IssueDetector()

    def create_llm_manager(self, inputs: AILintingFixerInputs) -> Any | None:
        """Create and configure the LLM manager."""
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
        llm_config: dict[str, Any] = {
            "default_provider": None,  # Will be set based on available providers
            "fallback_order": [],  # Will be populated based on available providers
            "providers": {},
        }

        # Prefer the Sluice gateway when configured: it centralises spend tracking
        # and enforces per-key budgets. Added before the vendor providers because the
        # default is derived from insertion order below; those stay as fallbacks for
        # deployments with no gateway. Tagged `linting-fixer` per Sluice ADR 17.
        if SluiceConfig.from_env() is not None:
            llm_config["providers"]["sluice"] = {"agent": SluiceAgent.LINTING_FIXER}

        # Add Azure OpenAI provider only if properly configured
        if azure_configured:
            llm_config["providers"]["azure_openai"] = {
                "azure_endpoint": azure_endpoint,
                "api_key": azure_api_key,
                "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
                "deployment_name": os.getenv(
                    "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo"
                ),
            }

        # Add other providers for fallback
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            llm_config["providers"]["openai"] = {
                "api_key": openai_api_key,
            }

        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_api_key:
            llm_config["providers"]["anthropic"] = {
                "api_key": anthropic_api_key,
            }

        # Determine default provider and fallback order based on available providers
        available_providers = list(llm_config["providers"].keys())
        if available_providers:
            # Set default provider to the first available one
            # (or use input provider if specified and available)
            if inputs.provider and inputs.provider in available_providers:
                llm_config["default_provider"] = inputs.provider
            else:
                llm_config["default_provider"] = available_providers[0]
            # Set fallback order to all available providers
            llm_config["fallback_order"] = available_providers
        else:
            # No providers available
            return None

        return LLMProviderManager(llm_config)

    def detect_issues(self, target_path: str) -> list[Any]:
        """Detect linting issues in the target path."""
        self.display.operation.show_detection_progress(target_path)
        issues = self.issue_detector.detect_issues(target_path)

        if not issues:
            self.display.operation.show_detection_results(0, 0)
            return []

        files_count = len({issue.file_path for issue in issues})
        self.display.operation.show_detection_results(len(issues), files_count)
        return issues

    def convert_to_legacy_format(self, issues: list[Any]) -> list[LintingIssue]:
        """Convert modern issue format to legacy format for compatibility."""
        legacy_issues = []
        for issue in issues:
            legacy_issue = LintingIssue(
                file_path=issue.file_path,
                line_number=issue.line_number,
                column_number=issue.column_number,
                error_code=issue.error_code,
                message=issue.message,
                line_content=issue.line_content,
            )
            legacy_issues.append(legacy_issue)
        return legacy_issues

    def queue_issues(
        self, fixer: AILintingFixer, issues: list[LintingIssue], quiet: bool
    ) -> int:
        """Queue detected issues for processing."""
        self.display.operation.show_queueing_progress(len(issues))

        queued_count = fixer.queue_detected_issues(issues, quiet=quiet)
        fixer.stats["issues_queued"] = queued_count

        self.display.operation.show_queueing_results(queued_count, len(issues))
        return queued_count

    async def process_issues(
        self,
        fixer: AILintingFixer,
        issues: list[LintingIssue],
        inputs: AILintingFixerInputs,
    ) -> dict[str, Any]:
        """Process queued issues."""
        # Note: processing mode could be used for future enhancements
        _processing_mode = (
            "redis"
            if hasattr(fixer, "redis_manager") and fixer.redis_manager
            else "local"
        )
        self.display.operation.show_processing_start(len(issues))

        process_results = await fixer.process_queued_issues(
            filter_types=inputs.fix_types,
            max_fixes=inputs.max_fixes_per_run,
            quiet=inputs.quiet,
        )

        # Update stats from processing results
        fixer.stats["issues_processed"] = process_results.get("processed", 0)
        fixer.stats["issues_fixed"] = process_results.get("fixed", 0)
        fixer.stats["issues_failed"] = process_results.get("failed", 0)

        self.display.operation.show_processing_results(
            process_results.get("fixed", 0), process_results.get("failed", 0)
        )

        return process_results

    def generate_final_results(
        self, fixer: AILintingFixer, inputs: AILintingFixerInputs
    ) -> AILintingFixerOutputs:
        """Generate the final results output."""
        session_results = fixer.get_session_results()

        # Convert dict to AILintingFixerOutputs instance
        final_results = AILintingFixerOutputs(
            total_issues_found=session_results.get("total_issues", 0),
            issues_fixed=session_results.get("successful_fixes", 0),
            files_modified=[],  # This would need to be filled from fixer if available
            success=session_results.get("success_rate", 0.0) > 0.5,
            summary=(
                f"Processed {session_results.get('total_issues', 0)} issues with "
                f"{session_results.get('success_rate', 0.0):.1%} success rate"
            ),
            total_issues_detected=session_results.get("total_issues", 0),
            issues_processed=session_results.get("total_issues", 0),
            issues_failed=session_results.get("failed_fixes", 0),
            total_duration=session_results.get("duration", 0.0),
            session_id=session_results.get("session_id"),
            agent_stats=session_results.get("stats", {}).get("agent_performance", {}),
            queue_stats=session_results.get("stats", {}).get("queue_statistics", {}),
        )

        # Display comprehensive results
        self.display.results.show_results_summary(final_results)
        if inputs.verbose_metrics:
            # Extract nested metrics from session_results
            agent_stats = session_results.get("stats", {}).get("agent_performance", {})
            queue_stats = session_results.get("stats", {}).get("queue_statistics", {})
            self.display.results.show_agent_performance(agent_stats)
            self.display.results.show_queue_statistics(queue_stats)
        # Generate suggestions based on results
        suggestions = []
        if final_results.issues_failed > 0:
            suggestions.append("Review failed fixes and consider manual intervention")
        success_rate = final_results.issues_fixed / max(
            final_results.total_issues_found, 1
        )
        if success_rate < 0.8:
            suggestions.append(
                "Consider adjusting fix parameters or reviewing code patterns"
            )
        self.display.results.show_suggestions(suggestions)

        return final_results

    def create_error_output(
        self,
        error_msg: str,
        *,
        summary: str | None = None,
        warnings: list[str] | None = None,
        session_id: str | None = None,
    ) -> AILintingFixerOutputs:
        """Create error output when something goes wrong."""
        error_results = create_empty_outputs(session_id or "error")
        error_results.success = False
        error_results.summary = summary or error_msg
        error_results.errors = [error_msg]
        if warnings:
            error_results.warnings = warnings
        return error_results


async def orchestrate_ai_linting_workflow(
    inputs: AILintingFixerInputs,
) -> AILintingFixerOutputs:
    """
    Main workflow orchestration function.

    This function orchestrates the entire AI linting workflow using
    the WorkflowOrchestrator class for clean separation of concerns.
    """
    # Initialize display system
    display_config = DisplayConfig(
        mode=(
            OutputMode.QUIET
            if inputs.quiet
            else (OutputMode.VERBOSE if inputs.verbose_metrics else OutputMode.NORMAL)
        )
    )

    orchestrator = WorkflowOrchestrator(display_config)
    display = orchestrator.display
    current_step = "initialize"
    fixer: AILintingFixer | None = None

    try:
        # Create LLM manager
        current_step = "create_llm_manager"
        llm_manager = orchestrator.create_llm_manager(inputs)

        # Initialize main fixer
        current_step = "initialize_fixer"
        fixer = AILintingFixer(llm_manager=llm_manager)

        # Show session start information
        display.operation.show_session_start(inputs, fixer.session_id)

        # Show provider status
        current_step = "provider_status"
        if llm_manager is not None:
            try:
                available_providers = llm_manager.get_available_providers()
                display.system.show_provider_status(available_providers)
            except Exception as e:
                logger.warning("Could not check provider status: %s", e)
        else:
            display.error.show_warning(
                "No LLM providers configured. AI features will be disabled."
            )
            display.error.show_info("To enable AI features, configure at least one of:")
            display.error.show_info(
                "  - AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT"
            )
            display.error.show_info("  - OPENAI_API_KEY")
            display.error.show_info("  - ANTHROPIC_API_KEY")

        # Step 1: Detect issues
        current_step = "detect_issues"
        issues = orchestrator.detect_issues(inputs.target_path)
        fixer.stats["issues_detected"] = len(issues)

        if not issues:
            # No issues found
            results = create_empty_outputs(fixer.session_id)
            results.success = True
            results.total_issues_detected = 0
            display.results.show_results_summary(results)
            return results

        # Step 2: Convert and queue issues
        current_step = "queue_issues"
        legacy_issues = orchestrator.convert_to_legacy_format(issues)
        queued_count = orchestrator.queue_issues(fixer, legacy_issues, inputs.quiet)

        if queued_count == 0:
            # No issues queued
            results = create_empty_outputs(fixer.session_id)
            results.success = True
            results.total_issues_detected = len(issues)
            results.issues_queued = 0
            display.error.show_warning("No issues were queued for processing")
            return results

        # Step 3: Process issues
        current_step = "process_issues"
        process_results = await orchestrator.process_issues(
            fixer, legacy_issues, inputs
        )

        # Show dry run notice if applicable
        if inputs.dry_run:
            display.operation.show_dry_run_notice()

        # Step 4: Generate final results
        current_step = "generate_final_results"
        return orchestrator.generate_final_results(fixer, inputs)

    except Exception as e:
        recovery_summary: str | None = None
        warning_messages: list[str] = []

        try:
            error_workflow_result = await handle_error_with_workflow(
                e,
                context={
                    "file_path": inputs.target_path,
                    "function_name": "orchestrate_ai_linting_workflow",
                    "workflow_step": current_step,
                    "session_id": fixer.session_id if fixer else None,
                    "additional_info": {
                        "dry_run": inputs.dry_run,
                        "quiet": inputs.quiet,
                        "verbose_metrics": inputs.verbose_metrics,
                        "provider": inputs.provider,
                    },
                },
            )
            strategy = (
                ErrorRecoveryStrategy.FALLBACK
                if error_workflow_result.recovery_successful
                else ErrorRecoveryStrategy.ABORT
            )
            recovery_summary = error_workflow_result.summary
            warning_messages.append(
                f"Error boundary captured failure during '{current_step}' with strategy {strategy.value}"
            )
        except Exception as boundary_error:
            logger.exception("Error boundary handling failed: %s", boundary_error)
            warning_messages.append(
                f"Error boundary failed while handling '{current_step}'"
            )

        # Handle errors with display system
        error_msg = f"AI linting fixer failed: {e}"
        logger.exception(error_msg)
        display.error.show_error(error_msg)
        if recovery_summary:
            display.error.show_info(recovery_summary)

        return orchestrator.create_error_output(
            error_msg,
            summary=recovery_summary or error_msg,
            warnings=warning_messages,
            session_id=fixer.session_id if fixer else None,
        )

    finally:
        # Clean up
        try:
            if fixer is not None:
                fixer.close()
        except Exception as e:
            logger.debug("Cleanup error: %s", e)
