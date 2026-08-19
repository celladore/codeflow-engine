import Header from "../components/Header";
import Footer from "../components/Footer";

export default function Installation() {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-slate-50/80 to-slate-100/50 dark:from-slate-900/80 dark:to-slate-950/50">
      <Header currentPage="installation" />

      <main className="flex-1">
        <section className="mx-auto max-w-4xl px-6 py-24">
          <h1 className="mb-6 text-4xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
            Installation Guide
          </h1>
          <p className="mb-12 text-xl text-slate-600 dark:text-slate-400">
            Get CodeFlow Engine up and running in minutes. Choose your preferred installation method.
          </p>

          <div className="space-y-8">
            {/* Quick Install */}
            <div className="rounded-lg border border-slate-200 bg-white/60 p-6 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/60">
              <h2 className="mb-4 text-2xl font-semibold text-slate-900 dark:text-slate-50">
                Quick Install (Recommended)
              </h2>
              <p className="mb-4 text-slate-600 dark:text-slate-400">
                Use our automated installation script for the fastest setup:
              </p>
              <div className="rounded-lg bg-slate-800 p-4 font-mono text-sm text-slate-50 dark:bg-slate-900">
                <code>curl -fsSL https://raw.githubusercontent.com/celladore/codeflow-engine/main/install.sh | bash</code>
              </div>
            </div>

            {/* Docker Install */}
            <div className="rounded-lg border border-slate-200 bg-white/60 p-6 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/60">
              <h2 className="mb-4 text-2xl font-semibold text-slate-900 dark:text-slate-50">
                Docker Installation
              </h2>
              <p className="mb-4 text-slate-600 dark:text-slate-400">
                Run CodeFlow Engine in a containerized environment:
              </p>
              <div className="space-y-2 rounded-lg bg-slate-800 p-4 font-mono text-sm text-slate-50 dark:bg-slate-900">
                <div>
                  <span className="text-slate-400"># Pull the image</span>
                </div>
                <div>
                  <code>docker pull ghcr.io/justaghost/codeflow-engine:latest</code>
                </div>
                <div className="mt-4">
                  <span className="text-slate-400"># Run the container</span>
                </div>
                <div>
                  <code>docker run -p 8000:8000 ghcr.io/justaghost/codeflow-engine:latest</code>
                </div>
              </div>
            </div>

            {/* Python Install */}
            <div className="rounded-lg border border-slate-200 bg-white/60 p-6 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/60">
              <h2 className="mb-4 text-2xl font-semibold text-slate-900 dark:text-slate-50">
                Python Installation
              </h2>
              <p className="mb-4 text-slate-600 dark:text-slate-400">
                Install from PyPI using pip:
              </p>
              <div className="space-y-2 rounded-lg bg-slate-800 p-4 font-mono text-sm text-slate-50 dark:bg-slate-900">
                <div>
                  <code>pip install codeflow-engine</code>
                </div>
                <div className="mt-4">
                  <span className="text-slate-400"># Or using Poetry</span>
                </div>
                <div>
                  <code>poetry add codeflow-engine</code>
                </div>
              </div>
            </div>

            {/* GitHub App Setup */}
            <div className="rounded-lg border border-slate-200 bg-white/60 p-6 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/60">
              <h2 className="mb-4 text-2xl font-semibold text-slate-900 dark:text-slate-50">
                GitHub App Setup
              </h2>
              <p className="mb-4 text-slate-600 dark:text-slate-400">
                Configure CodeFlow Engine as a GitHub App:
              </p>
              <ol className="list-decimal space-y-2 pl-6 text-slate-600 dark:text-slate-400">
                <li>Create a new GitHub App in your organization settings</li>
                <li>Set the webhook URL to your CodeFlow Engine instance</li>
                <li>Configure the required permissions (read/write access to PRs and issues)</li>
                <li>Install the app on your repositories</li>
                <li>Configure environment variables in your CodeFlow Engine instance</li>
              </ol>
            </div>
          </div>

          <div className="mt-12 rounded-lg bg-blue-50/90 p-6 backdrop-blur-sm dark:bg-blue-950/80">
            <h3 className="mb-2 text-lg font-semibold text-blue-900 dark:text-blue-50">
              Need Help?
            </h3>
            <p className="text-blue-800 dark:text-blue-200">
              Check out our{" "}
              <a
                href="https://github.com/celladore/codeflow-engine/blob/main/README.md"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:no-underline"
              >
                documentation
              </a>{" "}
              or open an issue on GitHub.
            </p>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}

