import Header from "../components/Header";
import Footer from "../components/Footer";

export default function Download() {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-slate-50/80 to-slate-100/50 dark:from-slate-900/80 dark:to-slate-950/50">
      <Header currentPage="download" />

      <main className="flex-1">
        <section className="mx-auto max-w-4xl px-6 py-24">
          <h1 className="mb-6 text-4xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
            Download CodeFlow Engine
          </h1>
          <p className="mb-12 text-xl text-slate-600 dark:text-slate-400">
            Choose your preferred download method and platform.
          </p>

          <div className="space-y-6">
            {/* GitHub Releases */}
            <div className="rounded-lg border border-slate-200 bg-white/60 p-6 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/60">
              <h2 className="mb-4 text-2xl font-semibold text-slate-900 dark:text-slate-50">
                GitHub Releases
              </h2>
              <p className="mb-4 text-slate-600 dark:text-slate-400">
                Download the latest stable release from GitHub:
              </p>
              <a
                href="https://github.com/celladore/codeflow-engine/releases/latest"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block rounded-lg bg-slate-800 px-6 py-3 font-semibold text-white transition-colors hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200"
              >
                View Releases →
              </a>
            </div>

            {/* PyPI */}
            <div className="rounded-lg border border-slate-200 bg-white/60 p-6 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/60">
              <h2 className="mb-4 text-2xl font-semibold text-slate-900 dark:text-slate-50">
                PyPI Package
              </h2>
              <p className="mb-4 text-slate-600 dark:text-slate-400">
                Install from Python Package Index:
              </p>
              <div className="rounded-lg bg-slate-800 p-4 font-mono text-sm text-slate-50 dark:bg-slate-900">
                <code>pip install codeflow-engine</code>
              </div>
              <a
                href="https://pypi.org/project/codeflow-engine/"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 inline-block text-blue-600 hover:underline dark:text-blue-400"
              >
                View on PyPI →
              </a>
            </div>

            {/* Docker Hub */}
            <div className="rounded-lg border border-slate-200 bg-white/60 p-6 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/60">
              <h2 className="mb-4 text-2xl font-semibold text-slate-900 dark:text-slate-50">
                Docker Image
              </h2>
              <p className="mb-4 text-slate-600 dark:text-slate-400">
                Pull from GitHub Container Registry:
              </p>
              <div className="rounded-lg bg-slate-800 p-4 font-mono text-sm text-slate-50 dark:bg-slate-900">
                <code>docker pull ghcr.io/justaghost/codeflow-engine:latest</code>
              </div>
              <a
                href="https://github.com/celladore/codeflow-engine/pkgs/container/codeflow-engine"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 inline-block text-blue-600 hover:underline dark:text-blue-400"
              >
                View Container Registry →
              </a>
            </div>

            {/* Source Code */}
            <div className="rounded-lg border border-slate-200 bg-white/60 p-6 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/60">
              <h2 className="mb-4 text-2xl font-semibold text-slate-900 dark:text-slate-50">
                Source Code
              </h2>
              <p className="mb-4 text-slate-600 dark:text-slate-400">
                Clone the repository to build from source:
              </p>
              <div className="rounded-lg bg-slate-800 p-4 font-mono text-sm text-slate-50 dark:bg-slate-900">
                <code>git clone https://github.com/celladore/codeflow-engine.git</code>
              </div>
            </div>
          </div>

          <div className="mt-12 rounded-lg bg-slate-100/90 p-6 backdrop-blur-sm dark:bg-slate-800/80">
            <h3 className="mb-2 text-lg font-semibold text-slate-900 dark:text-slate-50">
              System Requirements
            </h3>
            <ul className="list-disc space-y-1 pl-6 text-slate-600 dark:text-slate-400">
              <li>Python 3.8+ (for Python installation)</li>
              <li>Docker (for containerized deployment)</li>
              <li>Git (for source code installation)</li>
              <li>GitHub account with appropriate permissions</li>
            </ul>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

