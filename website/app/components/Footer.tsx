export default function Footer() {
  const ecosystemLinks = [
    { name: "Baton", href: "https://baton.celladoresystems.com" },
    { name: "Retort", href: "https://retort.celladoresystems.com" },
    { name: "Sluice", href: "https://sluice.celladoresystems.com" },
    { name: "Docket", href: "https://docket.celladoresystems.com" },
    { name: "xtox", href: "https://xtox.celladoresystems.com" },
  ];

  const docsLinks = [
    { name: "Installation", href: "/installation" },
    { name: "Integration", href: "/integration" },
    { name: "Download", href: "/download" },
    { name: "GitHub", href: "https://github.com/celladore/codeflow-engine", external: true },
  ];

  return (
    <footer className="border-t border-slate-200 bg-white/60 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-900/60">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="grid gap-8 sm:grid-cols-3">
          {/* Brand */}
          <div>
            <a
              href="https://celladoresystems.com"
              className="mb-3 block text-sm font-semibold text-slate-900 hover:underline dark:text-slate-50"
            >
              Celladore Systems
            </a>
            <p className="text-xs leading-relaxed text-slate-500 dark:text-slate-400">
              CodeFlow is part of the Celladore ecosystem — one connected toolchain for
              AI-driven software delivery.
            </p>
          </div>

          {/* Ecosystem */}
          <div>
            <div className="mb-3 font-mono text-xs font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">
              Ecosystem
            </div>
            <ul className="space-y-2">
              {ecosystemLinks.map(({ name, href }) => (
                <li key={name}>
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-50"
                  >
                    {name}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Docs */}
          <div>
            <div className="mb-3 font-mono text-xs font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">
              CodeFlow
            </div>
            <ul className="space-y-2">
              {docsLinks.map(({ name, href, external }) => (
                <li key={name}>
                  <a
                    href={href}
                    {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
                    className="text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-50"
                  >
                    {name}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-10 border-t border-slate-200 pt-6 text-center text-xs text-slate-400 dark:border-slate-700 dark:text-slate-500">
          © {new Date().getFullYear()} Celladore Systems. CodeFlow Engine is MIT licensed.
        </div>
      </div>
    </footer>
  );
}
