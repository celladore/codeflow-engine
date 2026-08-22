'use client';

export default function PromoBanner() {
  return (
    <div className="border-b border-blue-200 bg-blue-50 py-2 text-center dark:border-blue-900 dark:bg-blue-950/40">
      <div className="mx-auto max-w-7xl px-6">
        <p className="text-sm font-semibold text-white">
          <span className="mr-2">🔒 Private Preview:</span>
          CodeFlow Engine is currently in private preview. Features may change and some functionality may be limited.
          <a
            href="https://github.com/celladore/codeflow-engine/discussions"
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
