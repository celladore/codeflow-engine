'use client';

import Link from "next/link";
import AlphaBadge from "./AlphaBadge";
import ThemeToggle from "./ThemeToggle";

interface HeaderProps {
  currentPage?: 'home' | 'installation' | 'integration' | 'download' | 'login' | 'signup';
}

export default function Header({ currentPage = 'home' }: HeaderProps) {
  const navLinkClass = (page: string) =>
    currentPage === page
      ? "font-semibold text-slate-900 dark:text-slate-50"
      : "text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-50";

  const isCurrentPage = (page: string) => currentPage === page;

  return (
    <header className="border-b border-slate-200 bg-white/50 backdrop-blur-md dark:border-slate-700 dark:bg-slate-900/50">
      <nav
        className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4"
        aria-label="Main navigation"
      >
        <Link
          href="/"
          className="flex items-center text-2xl font-bold text-slate-900 dark:text-slate-50"
          aria-current={isCurrentPage('home') ? 'page' : undefined}
        >
          CodeFlow Engine
          <AlphaBadge />
        </Link>
        <div className="flex items-center gap-6">
          <Link
            href="/installation"
            className={navLinkClass('installation')}
            aria-current={isCurrentPage('installation') ? 'page' : undefined}
          >
            Installation
          </Link>
          <Link
            href="/integration"
            className={navLinkClass('integration')}
            aria-current={isCurrentPage('integration') ? 'page' : undefined}
          >
            Integration
          </Link>
          <Link
            href="/download"
            className={navLinkClass('download')}
            aria-current={isCurrentPage('download') ? 'page' : undefined}
          >
            Download
          </Link>
          <a
            href="https://github.com/celladore/codeflow-engine"
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-50"
            aria-label="View CodeFlow Engine on GitHub (opens in new tab)"
          >
            GitHub
          </a>
          <Link
            href="/login"
            className={navLinkClass('login')}
            aria-current={isCurrentPage('login') ? 'page' : undefined}
          >
            Sign in
          </Link>
          <Link
            href="/signup"
            className="rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-2 font-semibold text-white transition-all hover:from-blue-700 hover:to-purple-700 hover:shadow-lg"
            aria-current={isCurrentPage('signup') ? 'page' : undefined}
          >
            Sign up
          </Link>
          <ThemeToggle />
        </div>
      </nav>
    </header>
  );
}
