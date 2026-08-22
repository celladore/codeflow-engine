import Header from "../components/Header";
import Footer from "../components/Footer";
import { APP_URL, API_URL } from "../config/constants";

export default function Integration() {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-slate-50/80 to-slate-100/50 dark:from-slate-900/80 dark:to-slate-950/50">
      <Header currentPage="integration" />

      <main className="flex-1">
        <section className="mx-auto max-w-4xl px-6 py-24">
          <h1 className="mb-6 text-4xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
            Integrate with CodeFlow
          </h1>
          <p className="mb-12 text-xl text-slate-600 dark:text-slate-400">
            Connect your GitHub repositories to our deployed CodeFlow instance.
          </p>

          <div className="space-y-8">
            {/* Step 1: Access the Deployed Instance */}
            <div className="rounded-lg border border-slate-200 bg-white/60 p-6 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/60">
              <div className="mb-4 flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
                  1
                </span>
                <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
                  Access the Deployed Instance
                </h2>
              </div>
              <p className="mb-4 text-slate-600 dark:text-slate-400">
                Navigate to our hosted CodeFlow instance and sign in with your
                GitHub account:
              </p>
              <a
                href={APP_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-3 font-semibold text-white transition-all hover:from-blue-700 hover:to-purple-700 hover:shadow-lg"
              >
                Open CodeFlow Engine →
              </a>
            </div>

            {/* Step 2: Authorize GitHub Access */}
            <div className="rounded-lg border border-slate-200 bg-white/60 p-6 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/60">
              <div className="mb-4 flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
                  2
                </span>
                <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
                  Authorize GitHub Access
                </h2>
              </div>
              <p className="mb-4 text-slate-600 dark:text-slate-400">
                When prompted, authorize CodeFlow to access your GitHub
                repositories. The following permissions are required:
              </p>
              <ul className="list-disc space-y-2 pl-6 text-slate-600 dark:text-slate-400">
                <li>
                  <strong>Read access</strong> to repository code and metadata
                </li>
                <li>
                  <strong>Read/Write access</strong> to pull requests and issues
                </li>
                <li>
                  <strong>Webhook access</strong> for PR events
                </li>
              </ul>
            </div>

            {/* Step 3: Install the GitHub App */}
            <div className="rounded-lg border border-slate-200 bg-white/60 p-6 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/60">
              <div className="mb-4 flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
                  3
                </span>
                <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
                  Install the GitHub App
                </h2>
              </div>
              <p className="mb-4 text-slate-600 dark:text-slate-400">
                Install the CodeFlow GitHub App on your organization or personal
                repositories:
              </p>
              <ol className="list-decimal space-y-2 pl-6 text-slate-600 dark:text-slate-400">
                <li>
                  Go to{" "}
                  <a
                    href="https://github.com/apps/codeflow-engine"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline dark:text-blue-400"
                  >
                    github.com/apps/codeflow-engine
                  </a>
                </li>
                <li>
                  Click <strong>Install</strong> or{" "}
                  <strong>Configure</strong>
                </li>
                <li>
                  Select the repositories you want CodeFlow to monitor
                </li>
                <li>Confirm the installation</li>
              </ol>
            </div>

            {/* Step 4: Configure Your Repositories */}
            <div className="rounded-lg border border-slate-200 bg-white/60 p-6 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/60">
              <div className="mb-4 flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
                  4
                </span>
                <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
                  Configure Your Repositories
                </h2>
              </div>
              <p className="mb-4 text-slate-600 dark:text-slate-400">
                In the CodeFlow dashboard, configure settings for each connected
                repository:
              </p>
              <ul className="list-disc space-y-2 pl-6 text-slate-600 dark:text-slate-400">
                <li>
                  <strong>AI Analysis Settings:</strong> Choose which AI models
                  to use for code review (GPT-4, Claude, etc.)
                </li>
                <li>
                  <strong>Workflow Rules:</strong> Define automation rules for
                  issue creation and labeling
                </li>
                <li>
                  <strong>Notification Preferences:</strong> Set up Slack,
                  Teams, or Discord notifications
                </li>
                <li>
                  <strong>Quality Gates:</strong> Configure thresholds for
                  security and performance checks
                </li>
              </ul>
            </div>

            {/* Step 5: Add Configuration File (Optional) */}
            <div className="rounded-lg border border-slate-200 bg-white/60 p-6 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/60">
              <div className="mb-4 flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
                  5
                </span>
                <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
                  Add Configuration File (Optional)
                </h2>
              </div>
              <p className="mb-4 text-slate-600 dark:text-slate-400">
                For advanced customization, add an <code>.codeflow.yml</code>{" "}
                configuration file to your repository:
              </p>
              <div className="rounded-lg bg-slate-800 p-4 font-mono text-sm text-slate-50 dark:bg-slate-900">
                <pre className="overflow-x-auto">{`# .codeflow.yml
version: 1
analysis:
  enabled: true
  ai_provider: openai
  model: gpt-4

workflows:
  - name: pr_review
    triggers:
      - pull_request.opened
      - pull_request.synchronize
    actions:
      - ai_analysis
      - security_scan
      - create_issues

notifications:
  slack:
    channel: "#pr-reviews"
  
quality_gates:
  security:
    block_on_critical: true
  coverage:
    minimum: 80`}</pre>
              </div>
            </div>

            {/* Step 6: Verify Integration */}
            <div className="rounded-lg border border-slate-200 bg-white/60 p-6 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/60">
              <div className="mb-4 flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
                  6
                </span>
                <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
                  Verify Integration
                </h2>
              </div>
              <p className="mb-4 text-slate-600 dark:text-slate-400">
                Test your integration by creating a pull request:
              </p>
              <ol className="list-decimal space-y-2 pl-6 text-slate-600 dark:text-slate-400">
                <li>Create a new branch and make some changes</li>
                <li>Open a pull request to your main branch</li>
                <li>
                  CodeFlow will automatically analyze the PR and post comments
                </li>
                <li>
                  Check the CodeFlow dashboard for detailed analysis results
                </li>
              </ol>
            </div>
          </div>

          {/* API Integration Section */}
          <div className="mt-12 rounded-lg border-2 border-blue-500 bg-gradient-to-r from-blue-50/90 to-purple-50/90 p-8 backdrop-blur-sm dark:from-blue-950/80 dark:to-purple-950/80">
            <h2 className="mb-4 text-2xl font-bold text-slate-900 dark:text-slate-50">
              API Integration
            </h2>
            <p className="mb-4 text-slate-700 dark:text-slate-300">
              For programmatic access, use the CodeFlow API to integrate with your
              existing workflows and tools:
            </p>
            <div className="rounded-lg bg-slate-800 p-4 font-mono text-sm text-slate-50 dark:bg-slate-900">
              <pre className="overflow-x-auto">{`# Example: Trigger analysis via API
curl -X POST ${API_URL}/v1/analyze \\
  -H "Authorization: Bearer YOUR_API_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "repository": "owner/repo",
    "pull_request": 123
  }'`}</pre>
            </div>
            <p className="mt-4 text-slate-600 dark:text-slate-400">
              Generate your API token from the{" "}
              <a
                href={`${APP_URL}/settings/api`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline dark:text-blue-400"
              >
                CodeFlow Dashboard Settings
              </a>
              .
            </p>
          </div>

          {/* Webhook Events */}
          <div className="mt-8 rounded-lg border border-slate-200 bg-white/60 p-6 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/60">
            <h2 className="mb-4 text-2xl font-semibold text-slate-900 dark:text-slate-50">
              Webhook Events
            </h2>
            <p className="mb-4 text-slate-600 dark:text-slate-400">
              CodeFlow can send webhook notifications to your systems when
              analysis is complete:
            </p>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-600">
                    <th className="px-4 py-2 text-left font-semibold text-slate-900 dark:text-slate-50">
                      Event
                    </th>
                    <th className="px-4 py-2 text-left font-semibold text-slate-900 dark:text-slate-50">
                      Description
                    </th>
                  </tr>
                </thead>
                <tbody className="text-slate-600 dark:text-slate-400">
                  <tr className="border-b border-slate-100 dark:border-slate-700">
                    <td className="px-4 py-2 font-mono">analysis.completed</td>
                    <td className="px-4 py-2">
                      Fired when PR analysis finishes
                    </td>
                  </tr>
                  <tr className="border-b border-slate-100 dark:border-slate-700">
                    <td className="px-4 py-2 font-mono">issues.created</td>
                    <td className="px-4 py-2">
                      Fired when CodeFlow creates new issues
                    </td>
                  </tr>
                  <tr className="border-b border-slate-100 dark:border-slate-700">
                    <td className="px-4 py-2 font-mono">security.alert</td>
                    <td className="px-4 py-2">
                      Fired when security vulnerabilities are detected
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2 font-mono">quality.gate.failed</td>
                    <td className="px-4 py-2">
                      Fired when a quality gate check fails
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Help Section */}
          <div className="mt-12 rounded-lg bg-blue-50/90 p-6 backdrop-blur-sm dark:bg-blue-950/80">
            <h3 className="mb-2 text-lg font-semibold text-blue-900 dark:text-blue-50">
              Need Help?
            </h3>
            <p className="text-blue-800 dark:text-blue-200">
              Check out our{" "}
              <a
                href="https://github.com/celladore/codeflow-engine/blob/main/docs/GITHUB_APP_QUICKSTART.md"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:no-underline"
              >
                GitHub App Quickstart Guide
              </a>{" "}
              or reach out on{" "}
              <a
                href="https://github.com/celladore/codeflow-engine/discussions"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:no-underline"
              >
                GitHub Discussions
              </a>
              .
            </p>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
