'use client';

export default function PromoBanner() {
  return (
    <div className="border-b border-blue-200 bg-blue-50 py-2 text-center dark:border-blue-900 dark:bg-blue-950/40">
      <div className="mx-auto max-w-7xl px-6">
        <p className="text-xs font-medium text-blue-700 dark:text-blue-300">
          Open source alpha — MIT licensed.
          <a
            href="https://github.com/celladore/codeflow-engine"
            target="_blank"
            rel="noopener noreferrer"
            className="ml-2 underline underline-offset-2 hover:no-underline"
          >
            Star on GitHub →
          </a>
        </p>
      </div>
    </div>
  );
}
