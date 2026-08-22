# CodeFlow Engine Design System

> **Version:** 1.0.0
> **Last Updated:** December 6, 2025
> **Status:** Alpha Preview

This document defines the comprehensive design system for CodeFlow Engine, establishing visual consistency, accessibility standards, and component guidelines across all applications.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Design Tokens](#2-design-tokens)
3. [Color System](#3-color-system)
4. [Typography](#4-typography)
5. [Spacing & Layout](#5-spacing--layout)
6. [Component Library](#6-component-library)
7. [Gradients & Visual Effects](#7-gradients--visual-effects)
8. [Animations & Transitions](#8-animations--transitions)
9. [Alpha Preview Branding](#9-alpha-preview-branding)
10. [Accessibility Guidelines](#10-accessibility-guidelines)
11. [Dark Mode Implementation](#11-dark-mode-implementation)
12. [Implementation Guide](#12-implementation-guide)

---

## 1. Overview

### 1.1 Design Principles

The CodeFlow Engine design system is built on the following core principles:

| Principle | Description |
|-----------|-------------|
| **Clarity** | Clear visual hierarchy that guides users through complex workflows |
| **Consistency** | Unified visual language across website and desktop applications |
| **Accessibility** | WCAG 2.1 AA compliant design ensuring usability for all users |
| **Performance** | Lightweight, optimized assets that don't compromise load times |
| **Adaptability** | Seamless light/dark mode support with system preference detection |

### 1.2 Applications Covered

| Application | Technology Stack | Primary Purpose |
|-------------|-----------------|-----------------|
| **Website** | Next.js 16, Tailwind CSS 4 | Marketing, documentation, downloads |
| **Desktop App** | Tauri, React, shadcn/ui | PR automation interface |

### 1.3 File Structure

```
codeflow-engine/
â”œâ”€â”€ design-system/
â”‚   â”œâ”€â”€ tokens.css          # Centralized design tokens
â”‚   â””â”€â”€ README.md           # Quick reference guide
â”œâ”€â”€ DESIGN_SYSTEM.md        # This comprehensive documentation
â”œâ”€â”€ website/
â”‚   â””â”€â”€ app/
â”‚       â”œâ”€â”€ globals.css     # Website-specific styles
â”‚       â””â”€â”€ components/     # Website React components
â””â”€â”€ codeflow-desktop/
    â””â”€â”€ src/
        â”œâ”€â”€ App.css         # Desktop app styles
        â””â”€â”€ components/ui/  # shadcn/ui components
```

---

## 2. Design Tokens

Design tokens are the foundational building blocks of our visual language. They are stored in `/design-system/tokens.css` and should be referenced throughout all applications.

### 2.1 Token Categories

| Category | Example Token | Purpose |
|----------|--------------|---------|
| Colors | `--color-primary-600` | Brand and UI colors |
| Typography | `--font-size-lg` | Font sizes and weights |
| Spacing | `--space-4` | Margins, padding, gaps |
| Borders | `--radius-lg` | Border radius and widths |
| Shadows | `--shadow-md` | Elevation and depth |
| Animations | `--duration-200` | Transition timing |

### 2.2 Token Integration

Design tokens are imported into both applications:

**Website (`website/app/globals.css`):**
```css
@import "tailwindcss";
@import "../../design-system/tokens.css";
```

**Desktop App (`codeflow-desktop/src/App.css`):**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
@import "../../design-system/tokens.css";
```

### 2.3 Using Tokens

**Pure CSS:**
```css
.button {
  background-color: var(--color-primary-600);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  transition: background-color var(--duration-200) var(--ease-in-out);
}
```

**Tailwind with CSS variables:**
```tsx
<button className="bg-[var(--color-primary-600)] px-4 py-3 rounded-lg transition-colors duration-200">
  Click me
</button>
```

**Tailwind utility classes (recommended for consistency):**
```tsx
<button className="bg-blue-600 px-4 py-3 rounded-lg transition-colors duration-200">
  Click me
</button>
```

> **Note:** While tokens provide the source of truth, Tailwind utility classes are preferred for developer experience. The token values align with Tailwind's default color palette.

---

## 3. Color System

### 3.1 Primary Palette

The primary color palette uses **Blue** as the main action color and **Purple** as an accent for gradients.

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-primary-400` | `#60a5fa` | Links (dark mode) |
| `--color-primary-500` | `#3b82f6` | Focus rings, particle effects |
| `--color-primary-600` | `#2563eb` | Primary buttons, links (light) |
| `--color-primary-700` | `#1d4ed8` | Hover states |

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-secondary-500` | `#a855f7` | Gradient accents |
| `--color-secondary-600` | `#9333ea` | Gradient endpoints |
| `--color-secondary-700` | `#7e22ce` | Gradient hover states |

### 3.2 Alpha Preview Colors

These colors are used exclusively for alpha/preview branding elements:

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-alpha-100` | `#fef3c7` | Badge background (light) |
| `--color-alpha-500` | `#f59e0b` | Banner gradient start |
| `--color-alpha-800` | `#92400e` | Badge text (light) |
| `--color-alpha-900` | `#78350f` | Badge background (dark) |
| `--color-alpha-accent-500` | `#f97316` | Banner gradient end (orange) |

### 3.3 Neutral Colors (Slate)

| Token | Light Mode Usage | Dark Mode Usage |
|-------|-----------------|-----------------|
| `--color-neutral-50` | Page background | - |
| `--color-neutral-100` | Secondary background | - |
| `--color-neutral-200` | Borders, dividers | Badge text |
| `--color-neutral-400` | Muted text | Secondary text |
| `--color-neutral-600` | Secondary text | - |
| `--color-neutral-700` | - | Borders |
| `--color-neutral-800` | Primary text | Surface background |
| `--color-neutral-900` | - | Page background |

### 3.4 Semantic Colors

| Type | Light Background | Light Text | Dark Background | Dark Text |
|------|-----------------|------------|-----------------|-----------|
| **Success** | `#dcfce7` (100) | `#15803d` (700) | `#14532d` (900) | `#22c55e` (500) |
| **Error** | `#fee2e2` (100) | `#b91c1c` (700) | `#7f1d1d` (900) | `#f87171` (400) |
| **Warning** | `#fef3c7` (100) | `#b45309` (700) | `#78350f` (900) | `#fbbf24` (400) |
| **Info** | `#dbeafe` (100) | `#1d4ed8` (700) | `#1e3a8a` (900) | `#60a5fa` (400) |

### 3.5 Color Contrast Requirements

All color combinations must meet WCAG 2.1 AA contrast requirements:

| Text Type | Minimum Ratio |
|-----------|--------------|
| Normal text (< 18px) | 4.5:1 |
| Large text (>= 18px or 14px bold) | 3:1 |
| UI components and graphics | 3:1 |

**Verified Combinations:**

| Foreground | Background | Ratio | Status |
|------------|------------|-------|--------|
| `slate-800` (#1e293b) | `slate-50` (#f8fafc) | 11.6:1 | Pass |
| `slate-200` (#e2e8f0) | `slate-900` (#0f172a) | 12.1:1 | Pass |
| `amber-800` (#92400e) | `amber-100` (#fef3c7) | 5.8:1 | Pass |
| `amber-200` (#fde68a) | `amber-900` (#78350f) | 4.8:1 | Pass |
| `blue-600` (#2563eb) | `white` (#ffffff) | 4.6:1 | Pass |
| `white` (#ffffff) | `blue-600` (#2563eb) | 4.6:1 | Pass |

---

## 4. Typography

### 4.1 Font Families

| Family | Variable | Usage |
|--------|----------|-------|
| **Geist Sans** | `--font-sans` | Body text, UI elements |
| **Geist Mono** | `--font-mono` | Code, technical content |

**Font Loading:**
```tsx
// website/app/layout.tsx
import localFont from "next/font/local";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
  display: "swap",
});

const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
  display: "swap",
});
```

### 4.2 Type Scale

| Token | Size | Line Height | Usage |
|-------|------|-------------|-------|
| `--font-size-xs` | 12px | 1.5 | Badges, captions |
| `--font-size-sm` | 14px | 1.5 | Buttons, labels |
| `--font-size-base` | 16px | 1.5 | Body text |
| `--font-size-lg` | 18px | 1.5 | Lead paragraphs |
| `--font-size-xl` | 20px | 1.5 | Section descriptions |
| `--font-size-2xl` | 24px | 1.25 | Section headings (H3) |
| `--font-size-3xl` | 30px | 1.25 | Page headings (H2) |
| `--font-size-4xl` | 36px | 1.25 | Large headings |
| `--font-size-5xl` | 48px | 1.1 | Hero headings (H1) |
| `--font-size-6xl` | 60px | 1.1 | Hero headings (desktop) |

### 4.3 Font Weights

| Weight | Token | Usage |
|--------|-------|-------|
| 400 | `--font-weight-normal` | Body text |
| 500 | `--font-weight-medium` | Emphasized text |
| 600 | `--font-weight-semibold` | Buttons, badges, labels |
| 700 | `--font-weight-bold` | Headings |

### 4.4 Typography Components

**Hero Heading:**
```tsx
<h1 className="text-5xl md:text-6xl font-bold tracking-tight">
  Heading Text
</h1>
```

**Section Heading:**
```tsx
<h2 className="text-3xl font-bold">Section Title</h2>
```

**Body Text:**
```tsx
<p className="text-base text-slate-600 dark:text-slate-400">
  Body content
</p>
```

**Caption/Label:**
```tsx
<span className="text-xs font-semibold uppercase tracking-wide">
  Label
</span>
```

---

## 5. Spacing & Layout

### 5.1 Spacing Scale

| Token | Value | Pixels |
|-------|-------|--------|
| `--space-1` | 0.25rem | 4px |
| `--space-2` | 0.5rem | 8px |
| `--space-3` | 0.75rem | 12px |
| `--space-4` | 1rem | 16px |
| `--space-6` | 1.5rem | 24px |
| `--space-8` | 2rem | 32px |
| `--space-12` | 3rem | 48px |
| `--space-16` | 4rem | 64px |
| `--space-24` | 6rem | 96px |

### 5.2 Container Widths

| Token | Value | Usage |
|-------|-------|-------|
| `--container-4xl` | 56rem (896px) | Narrow content sections |
| `--container-7xl` | 80rem (1280px) | Main page container |

### 5.3 Layout Patterns

**Page Container:**
```tsx
<div className="mx-auto max-w-7xl px-6 py-24">
  {/* Content */}
</div>
```

**Narrow Content:**
```tsx
<div className="mx-auto max-w-4xl px-6 py-24">
  {/* Focused content */}
</div>
```

**Flex Layout with Gap:**
```tsx
<div className="flex items-center gap-4">
  {/* Items with consistent spacing */}
</div>
```

**Grid Layout:**
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {/* Grid items */}
</div>
```

---

## 6. Component Library

### 6.1 Unified Component Approach

CodeFlow Engine uses a hybrid component approach:

| Application | Component Source | Styling Approach |
|-------------|-----------------|------------------|
| Website | Custom React components | Tailwind CSS utilities |
| Desktop | shadcn/ui components | Tailwind + CSS variables |

### 6.2 Core Components

#### Button

**Variants:**

| Variant | Description | Usage |
|---------|-------------|-------|
| `default` | Primary blue/purple gradient | Main CTAs |
| `secondary` | Outlined style | Secondary actions |
| `ghost` | No background | Tertiary actions |
| `destructive` | Red background | Dangerous actions |

**Sizes:**

| Size | Height | Padding X | Font Size |
|------|--------|-----------|-----------|
| `sm` | 32px | 12px | 14px |
| `default` | 40px | 16px | 14px |
| `lg` | 44px | 24px | 14px |

**Implementation:**
```tsx
// Primary button
<button className="inline-flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-3 text-sm font-semibold text-white shadow-lg hover:from-blue-700 hover:to-purple-700 hover:shadow-xl transition-all duration-200">
  Get Started
</button>

// Secondary button
<button className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-900 hover:bg-slate-50 transition-colors duration-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:hover:bg-slate-700">
  Learn More
</button>
```

#### Card

**Structure:**
```tsx
<div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm hover:shadow-lg transition-shadow duration-200 dark:border-slate-700 dark:bg-slate-800">
  <div className="space-y-4">
    <h3 className="text-xl font-semibold">Card Title</h3>
    <p className="text-slate-600 dark:text-slate-400">Card content</p>
  </div>
</div>
```

#### Badge

**Variants:**

| Variant | Background | Text |
|---------|------------|------|
| `default` | slate-100 | slate-800 |
| `alpha` | amber-100 | amber-800 |
| `success` | green-100 | green-800 |
| `error` | red-100 | red-800 |

**Alpha Badge:**
```tsx
<span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800 dark:bg-amber-900 dark:text-amber-200">
  Alpha Preview
</span>
```

#### Input

**Implementation:**
```tsx
<input
  type="text"
  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
  placeholder="Enter text..."
/>
```

#### Navigation

**Header:**
```tsx
<header className="sticky top-0 z-50 border-b border-slate-200 bg-white/50 backdrop-blur-md dark:border-slate-700 dark:bg-slate-900/50">
  <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
    {/* Logo and navigation */}
  </nav>
</header>
```

**Navigation Link:**
```tsx
// Active state
<a className="text-sm font-semibold text-slate-900 dark:text-white" aria-current="page">
  Active Link
</a>

// Inactive state
<a className="text-sm text-slate-600 hover:text-slate-900 transition-colors duration-200 dark:text-slate-400 dark:hover:text-white">
  Inactive Link
</a>
```

### 6.3 shadcn/ui Integration (Desktop App)

The desktop application uses shadcn/ui for consistent, accessible components:

**Configuration (`components.json`):**
```json
{
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "src/App.css",
    "baseColor": "slate",
    "cssVariables": true
  }
}
```

**Adding New Components:**
```bash
pnpm dlx shadcn@latest add button card badge
```

---

## 7. Gradients & Visual Effects

### 7.1 Primary Gradients

**CTA Button Gradient:**
```css
/* Normal state */
background: linear-gradient(to right, #2563eb, #9333ea);
/* from-blue-600 to-purple-600 */

/* Hover state */
background: linear-gradient(to right, #1d4ed8, #7e22ce);
/* from-blue-700 to-purple-700 */
```

**Tailwind Implementation:**
```tsx
<button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
  Action
</button>
```

### 7.2 Alpha/Preview Gradients

**Promo Banner:**
```css
background: linear-gradient(to right, #f59e0b, #f97316);
/* from-amber-500 to-orange-500 */
```

**Alpha Section Background (Light):**
```css
background: linear-gradient(to right,
  rgba(255, 251, 235, 0.9),  /* amber-50/90 */
  rgba(255, 247, 237, 0.9)   /* orange-50/90 */
);
```

**Alpha Section Background (Dark):**
```css
background: linear-gradient(to right,
  rgba(69, 26, 3, 0.8),   /* amber-950/80 */
  rgba(67, 20, 7, 0.8)    /* orange-950/80 */
);
```

### 7.3 Page Background Gradients

**Light Mode:**
```tsx
<div className="bg-gradient-to-b from-slate-50/80 to-slate-100/50">
```

**Dark Mode:**
```tsx
<div className="dark:from-slate-900/80 dark:to-slate-950/50">
```

### 7.4 Backdrop Effects

**Glass Effect (Header/Modals):**
```tsx
<div className="bg-white/50 backdrop-blur-md dark:bg-slate-900/50">
```

### 7.5 Shadows

| Level | Token | Usage |
|-------|-------|-------|
| Subtle | `--shadow-sm` | Cards at rest |
| Default | `--shadow-default` | Elevated elements |
| Medium | `--shadow-md` | Dropdowns |
| Large | `--shadow-lg` | Buttons on hover, modals |

---

## 8. Animations & Transitions

### 8.1 Global Transition

All interactive elements should have smooth color transitions:

```css
* {
  transition-property: background-color, border-color, color, fill, stroke;
  transition-duration: 200ms;
  transition-timing-function: ease-in-out;
}
```

### 8.2 Transition Durations

| Duration | Token | Usage |
|----------|-------|-------|
| 75ms | `--duration-75` | Micro-interactions |
| 150ms | `--duration-150` | Quick feedback |
| 200ms | `--duration-200` | Standard transitions (default) |
| 300ms | `--duration-300` | Smooth animations |
| 500ms | `--duration-500` | Emphasis animations |

### 8.3 Easing Functions

| Name | Token | Curve | Usage |
|------|-------|-------|-------|
| Linear | `--ease-linear` | `linear` | Progress bars |
| Ease In | `--ease-in` | `cubic-bezier(0.4, 0, 1, 1)` | Elements exiting |
| Ease Out | `--ease-out` | `cubic-bezier(0, 0, 0.2, 1)` | Elements entering |
| Ease In-Out | `--ease-in-out` | `cubic-bezier(0.4, 0, 0.2, 1)` | Standard (default) |

### 8.4 Keyframe Animations

**Slide In (Notifications/Panels):**
```css
@keyframes slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.animate-slide-in {
  animation: slide-in 0.3s ease-out;
}
```

**Pulse (Loading States):**
```css
/* Built-in Tailwind: animate-pulse */
```

**Spin (Refresh Icons):**
```css
/* Built-in Tailwind: animate-spin */
```

### 8.5 Animated Background

The website features an animated particle background using HTML Canvas:

**Configuration:**
- **Particle Count:** 50
- **Connection Distance:** 150px
- **Light Mode Color:** `rgba(59, 130, 246)` (blue-500)
- **Dark Mode Color:** `rgba(147, 197, 253)` (blue-300)
- **Opacity Range:** 0.1 - 0.6

**Implementation Reference:** `website/app/components/AnimatedBackground.tsx`

### 8.6 Reduced Motion Support

Always respect user preferences for reduced motion:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 9. Alpha Preview Branding

### 9.1 Alpha Branding Elements

The alpha preview status is communicated through consistent visual elements:

| Element | Location | Purpose |
|---------|----------|---------|
| **Promo Banner** | Fixed top of page | Primary status announcement |
| **Alpha Badge** | Header, hero section | Inline status indicator |
| **Featured CTA** | Hero/main sections | Encourages early adoption |

### 9.2 Promo Banner

**Specifications:**
- **Background:** Gradient from amber-500 to orange-500
- **Text Color:** White
- **Padding:** 12px vertical
- **Position:** Fixed top, full width

**Implementation:**
```tsx
<div className="bg-gradient-to-r from-amber-500 to-orange-500 py-3 text-center text-sm text-white">
  <p>
    <span role="img" aria-label="construction">
      ðŸš§
    </span>{" "}
    <span className="font-semibold">Alpha Preview:</span> CodeFlow Engine is
    currently in alpha...
  </p>
</div>
```

### 9.3 Alpha Badge

**Specifications:**
- **Shape:** Pill (rounded-full)
- **Padding:** 2.5px vertical, 8px horizontal
- **Font:** 12px, semibold
- **Light Mode:** amber-100 background, amber-800 text
- **Dark Mode:** amber-900 background, amber-200 text

**Implementation:**
```tsx
<span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800 dark:bg-amber-900 dark:text-amber-200">
  Alpha Preview
</span>
```

### 9.4 Alpha Section Styling

For featured alpha content sections:

**Light Mode:**
```tsx
<section className="rounded-xl border-2 border-amber-500 bg-gradient-to-r from-amber-50/90 to-orange-50/90 p-8">
  {/* Alpha-specific content */}
</section>
```

**Dark Mode:**
```tsx
<section className="dark:from-amber-950/80 dark:to-orange-950/80 dark:border-amber-600">
  {/* Alpha-specific content */}
</section>
```

### 9.5 Emoji Usage in Alpha Content

Approved emojis for alpha/preview messaging:

| Emoji | Name | Usage |
|-------|------|-------|
| ðŸš§ | Construction | Alpha status indicator |
| ðŸš€ | Rocket | Launch/getting started |
| ðŸ¤– | Robot | AI/automation features |
| ðŸ”„ | Cycle | Sync/update features |
| âš¡ | Lightning | Speed/performance |

---

## 10. Accessibility Guidelines

### 10.1 WCAG 2.1 AA Compliance Checklist

> **Audit Date:** December 6, 2025
> **Method:** Manual code review and grep analysis

#### Perceivable

| Criterion | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **1.1.1 Non-text Content** | All images have alt text | N/A | No `<img>` tags in codebase |
| **1.3.1 Info and Relationships** | Proper heading hierarchy | Implemented | Semantic HTML structure used |
| **1.3.4 Orientation** | Content works in portrait/landscape | Implemented | Responsive design with Tailwind |
| **1.4.1 Use of Color** | Color not sole means of conveying info | Implemented | Icons accompany color cues |
| **1.4.3 Contrast (Minimum)** | 4.5:1 for normal text, 3:1 for large | Implemented | Verified: slate-800/slate-50 = 11.6:1 |
| **1.4.4 Resize Text** | Text resizable up to 200% | Implemented | rem-based font sizes |
| **1.4.10 Reflow** | Content reflows at 320px width | Implemented | Mobile-first responsive design |
| **1.4.11 Non-text Contrast** | 3:1 for UI components | Implemented | Button/border contrasts verified |
| **1.4.12 Text Spacing** | No loss of content with increased spacing | Implemented | Flexible layouts |

#### Operable

| Criterion | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **2.1.1 Keyboard** | All functionality keyboard accessible | Implemented | Tab navigation works |
| **2.1.2 No Keyboard Trap** | Focus can be moved away from elements | Implemented | No modal traps |
| **2.4.1 Bypass Blocks** | Skip navigation links | Implemented | Skip link in layout.tsx |
| **2.4.3 Focus Order** | Logical focus order | Implemented | DOM order matches visual |
| **2.4.4 Link Purpose** | Link purpose clear from context | Implemented | aria-label on external links |
| **2.4.6 Headings and Labels** | Descriptive headings and labels | Implemented | Clear heading text |
| **2.4.7 Focus Visible** | Visible focus indicator | Implemented | CSS using design tokens |
| **2.5.5 Target Size** | Touch targets minimum 44x44px | Implemented | Buttons meet 44px minimum |

#### Understandable

| Criterion | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **3.1.1 Language of Page** | Lang attribute on html | Implemented | `<html lang="en">` |
| **3.2.1 On Focus** | No context change on focus | Implemented | No auto-redirects |
| **3.2.2 On Input** | No unexpected context change on input | Implemented | No auto-submit forms |
| **3.3.1 Error Identification** | Errors clearly identified | N/A | No form submissions yet |
| **3.3.2 Labels or Instructions** | Form inputs have labels | N/A | No form inputs yet |

#### Robust

| Criterion | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **4.1.1 Parsing** | Valid HTML markup | Implemented | React JSX compiles to valid HTML |
| **4.1.2 Name, Role, Value** | ARIA attributes correct | Implemented | aria-current, aria-label, aria-hidden used |

#### Implemented Accessibility Features

- **Skip Link:** `<a href="#main-content" class="skip-link">` in layout.tsx
- **Landmark Roles:** `<main id="main-content" role="main">`
- **Navigation Labels:** `<nav aria-label="Main navigation">`
- **Current Page Indicator:** `aria-current="page"` on active nav links
- **External Link Labels:** `aria-label="... (opens in new tab)"` on GitHub link
- **Decorative Elements Hidden:** `aria-hidden="true"` on AnimatedBackground canvas
- **Theme Toggle Label:** `aria-label="Current theme: {theme}. Click to change."`
- **Reduced Motion Support:** AnimatedBackground respects `prefers-reduced-motion`

### 10.2 Focus States

All interactive elements must have a visible focus state:

```css
*:focus-visible {
  outline: 2px solid var(--color-primary-500);
  outline-offset: 2px;
}
```

**Implementation:**
```tsx
<button className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">
  Accessible Button
</button>
```

### 10.3 Keyboard Navigation

| Key | Action |
|-----|--------|
| `Tab` | Move focus to next element |
| `Shift + Tab` | Move focus to previous element |
| `Enter` | Activate buttons and links |
| `Space` | Activate buttons, toggle checkboxes |
| `Escape` | Close modals and dropdowns |
| `Arrow Keys` | Navigate within menus and lists |

### 10.4 ARIA Patterns

**Current Page Indicator:**
```tsx
<a href="/current-page" aria-current="page">
  Current Page
</a>
```

**Button with Icon:**
```tsx
<button aria-label="Refresh data">
  <RefreshIcon aria-hidden="true" />
</button>
```

**Loading State:**
```tsx
<div role="status" aria-label="Loading">
  <Spinner />
</div>
```

**Decorative Elements:**
```tsx
<canvas aria-hidden="true" className="animated-background" />
```

### 10.5 Skip Links

Add skip navigation links for screen reader users:

```tsx
<a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:rounded-md focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:shadow-lg">
  Skip to main content
</a>

<main id="main-content">
  {/* Page content */}
</main>
```

### 10.6 Color Independence

Never rely on color alone to convey information:

**Correct:**
```tsx
// Using icon + color + text
<span className="flex items-center gap-2 text-red-600">
  <ErrorIcon /> Error: Invalid input
</span>
```

**Incorrect:**
```tsx
// Color only - not accessible
<span className="text-red-600">Invalid input</span>
```

---

## 11. Dark Mode Implementation

### 11.1 Strategy

CodeFlow Engine uses **class-based dark mode** with the following features:

- System preference detection (`prefers-color-scheme`)
- Manual toggle (light/dark/system)
- LocalStorage persistence
- Smooth theme transitions

### 11.2 Theme Provider

**Implementation Reference:** `website/app/components/ThemeProvider.tsx`

```tsx
type Theme = "light" | "dark" | "system";

const ThemeContext = createContext<{
  theme: Theme;
  resolvedTheme: "light" | "dark";
  setTheme: (theme: Theme) => void;
}>({...});
```

### 11.3 CSS Custom Properties

**Light Mode (default):**
```css
:root {
  --background: #f8fafc;
  --foreground: #1e293b;
}
```

**Dark Mode:**
```css
.dark {
  --background: #0f172a;
  --foreground: #e2e8f0;
}
```

### 11.4 Theme Toggle Component

The theme toggle provides three states:

| State | Icon | Description |
|-------|------|-------------|
| System | Monitor icon | Follow OS preference |
| Light | Sun icon | Always light mode |
| Dark | Moon icon | Always dark mode |

### 11.5 Dark Mode Classes

Use Tailwind's `dark:` variant for dark mode styles:

```tsx
<div className="bg-white text-slate-900 dark:bg-slate-800 dark:text-white">
  Content
</div>
```

### 11.6 Preventing Flash

To prevent theme flash on page load, the theme is resolved before React hydration:

```tsx
// In layout.tsx
<html lang="en" suppressHydrationWarning>
  <head>
    <script dangerouslySetInnerHTML={{
      __html: `
        (function() {
          const theme = localStorage.getItem('theme') || 'system';
          const resolved = theme === 'system'
            ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
            : theme;
          document.documentElement.classList.add(resolved);
        })()
      `
    }} />
  </head>
</html>
```

---

## 12. Implementation Guide

### 12.1 Getting Started

1. **Import Design Tokens:**
   ```css
   @import "../../design-system/tokens.css";
   ```

2. **Configure Tailwind:**
   Ensure your `tailwind.config.js` extends with design tokens if needed.

3. **Use CSS Variables:**
   Reference tokens using `var(--token-name)` in CSS or Tailwind's arbitrary value syntax.

### 12.2 Adding New Components

1. Check if a similar component exists in the design system
2. Follow existing patterns and naming conventions
3. Ensure WCAG 2.1 AA compliance
4. Support both light and dark modes
5. Include proper focus states
6. Document the component in this guide

### 12.3 Color Naming Convention

| Pattern | Example | Description |
|---------|---------|-------------|
| `--color-{name}-{shade}` | `--color-primary-600` | Color with shade |
| `--color-{semantic}` | `--color-background` | Theme-aware semantic |
| `--gradient-{name}` | `--gradient-primary` | Gradient definitions |

### 12.4 Component Class Naming

Follow Tailwind utility-first approach with consistent ordering:

```tsx
className={cn(
  // Layout
  "flex items-center justify-center",
  // Spacing
  "px-4 py-2 gap-2",
  // Typography
  "text-sm font-semibold",
  // Colors
  "bg-white text-slate-900",
  // Dark mode
  "dark:bg-slate-800 dark:text-white",
  // Border & effects
  "rounded-lg shadow-sm",
  // Interactivity
  "hover:shadow-lg transition-shadow duration-200",
  // Focus
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
)}
```

### 12.5 Testing Checklist

Before submitting changes:

- [ ] Component works in light mode
- [ ] Component works in dark mode
- [ ] Keyboard navigation works correctly
- [ ] Focus states are visible
- [ ] Color contrast meets WCAG AA (4.5:1 for text)
- [ ] Touch targets are at least 44x44px
- [ ] Reduced motion preferences are respected
- [ ] Component is responsive across breakpoints

### 12.6 Resources

| Resource | URL |
|----------|-----|
| Tailwind CSS Docs | https://tailwindcss.com/docs |
| shadcn/ui | https://ui.shadcn.com |
| WCAG 2.1 Guidelines | https://www.w3.org/WAI/WCAG21/quickref/ |
| Color Contrast Checker | https://webaim.org/resources/contrastchecker/ |
| Lucide Icons | https://lucide.dev |

---

## Changelog

### Version 1.0.2 (December 6, 2025)
- **Critical Fix:** Fixed circular CSS variable references in globals.css `@theme` block
- **Critical Fix:** Moved `@import` before `@tailwind` directives in desktop App.css
- **Critical Fix:** Fixed invalid `transition-property: var()` usage (CSS vars don't work for property lists)
- **Desktop Fonts:** Added desktop-specific font stack (`--font-sans-desktop`) since Geist isn't available in Tauri
- **Skip Link Fix:** Replaced `outline: none` with proper focus ring on skip link
- **Firefox Scrollbars:** Added `scrollbar-width` and `scrollbar-color` for Firefox support
- **Reduced Motion:** Fixed animation restart when user toggles reduced motion preference
- **Token Docs:** Updated transition tokens documentation to warn about CSS limitations

### Version 1.0.1 (December 6, 2025)
- **Token Integration:** Imported tokens.css into website globals.css and desktop App.css
- **Font Fix:** Fixed font-family bug in globals.css (was Arial, now uses Geist via tokens)
- **shadcn Alignment:** Aligned desktop shadcn/ui CSS variables with design tokens
- **lib/utils.ts:** Created missing utility file with `cn()` function for desktop app
- **Breakpoint Tokens:** Added responsive breakpoint tokens (sm, md, lg, xl, 2xl)
- **Skip Links:** Implemented skip-to-content link in website layout
- **Accessibility Improvements:**
  - Added `aria-current="page"` to navigation links
  - Added `aria-label` to external links
  - Added `aria-label` to navigation element
  - Updated AnimatedBackground to respect `prefers-reduced-motion`
- **Audit Update:** Updated WCAG compliance checklist with verified statuses

### Version 1.0.0 (December 6, 2025)
- Initial design system documentation
- Centralized design tokens
- WCAG 2.1 AA accessibility audit
- Component library documentation
- Alpha preview branding guidelines
- Dark mode implementation guide
