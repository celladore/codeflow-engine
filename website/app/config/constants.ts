/**
 * Application constants
 * 
 * Centralized configuration for URLs and other constants used across the website.
 */

/**
 * The deployed CodeFlow Engine application URL.
 * This is the custom domain configured for the Azure Container Apps deployment.
 *
 * NOTE (2026-08-19): was `https://app.codeflow.io` — a legacy brand domain
 * we don't control (see orchestration/infrastructure/README.md: "do not
 * use codeflow.io until domain ownership and brand risk are resolved").
 * The backend (`cel-prod-codeflow-api`) has served real traffic since the
 * CEL migration's Phase 4, but had no custom domain bound until this
 * cutover — see orchestration/infrastructure/CEL_MIGRATION_PLAN.md's
 * Phase 8 log. Do not flip this back to app.codeflow.io.
 */
export const APP_URL = 'https://app.codeflow.celladoresystems.com';

/**
 * API base URL for CodeFlow Engine
 */
export const API_URL = `${APP_URL}/api`;
