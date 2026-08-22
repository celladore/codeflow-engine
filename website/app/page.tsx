import Link from "next/link";
import Header from "./components/Header";
import Footer from "./components/Footer";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-slate-50/80 to-slate-100/50 dark:from-slate-900/80 dark:to-slate-950/50">
      <Header currentPage="home" />

      <main className="flex-1">
        <section className="mx-auto max-w-7xl px-6 py-24 text-center">
          <div className="mb-8 inline-block rounded-full bg-gradient-to-r from-amber-50 to-orange-50 px-6 py-2 text-sm font-semibold text-amber-900 dark:from-amber-950/80 dark:to-orange-950/80 dark:text-amber-100">
            🔒 Private Preview - Request early access →
          </div>
          <h1 className="mb-6 text-5xl font-bold tracking-tight text-slate-900 dark:text-slate-50 sm:text-6xl">
            Durable, multi-agent<br className="hidden sm:block" /> PR automation.
          </h1>
          <p className="mx-auto mb-10 max-w-2xl text-xl text-slate-600 dark:text-slate-400">
            CodeFlow runs automated pull-request generation, review, and merge-readiness
            workflows on Temporal — so a network drop or process restart never loses hours
            of in-flight agent work.
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <a
              href="https://github.com/celladore/codeflow-engine"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg bg-slate-900 px-7 py-3 text-base font-semibold text-white transition-colors hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200"
            >
              Request Private Preview
            </Link>
            <Link
              href="/installation"
              className="rounded-lg border border-slate-300 bg-white px-7 py-3 text-base font-semibold text-slate-900 transition-colors hover:border-slate-400 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-50 dark:hover:border-slate-500"
            >
              Installation guide
            </Link>
            <Link
              href="/integration"
              className="text-base font-medium text-blue-600 underline-offset-2 hover:underline dark:text-blue-400"
            >
              Integration docs →
            </Link>
          </div>
        </section>

        {/* How it works — workflow stages */}
        <section className="mx-auto max-w-5xl px-6 pb-24">
          <h2 className="mb-3 text-center text-2xl font-bold text-slate-900 dark:text-slate-50">
            How a PR moves through CodeFlow
          </h2>
          <p className="mb-12 text-center text-slate-500 dark:text-slate-400">
            Every stage is a durable Temporal activity — any crash or network drop is transparent.
          </p>
          <ol className="relative border-l border-slate-200 dark:border-slate-700 ml-4">
            {[
              {
                step: "01",
                label: "Webhook received",
                body: "GitHub App receives pull_request.opened or pull_request.synchronize and dispatches to the CodeFlow workflow engine.",
                tone: "blue",
              },
              {
                step: "02",
                label: "Temporal workflow started",
                body: "A durable workflow execution is created. From this point forward, any crash or network interruption is fully recoverable.",
                tone: "green",
              },
              {
                step: "03",
                label: "Multi-agent analysis crew",
                body: "CrewAI agents run architecture review, security scanning, and diff analysis in parallel — all LLM calls routed through Sluice for failover and cost tracking.",
                tone: "blue",
              },
              {
                step: "04",
                label: "Quality gate evaluation",
                body: "Security thresholds, coverage minimums, and custom gates evaluate the crew's output. A failure here emits quality.gate.failed and blocks merge readiness.",
                tone: "amber",
              },
              {
                step: "05",
                label: "Issue creation & annotation",
                body: "Findings are filed as GitHub issues. analysis.completed and issues.created events fire to connected Axolo / Slack channels.",
                tone: "green",
              },
              {
                step: "06",
                label: "Merge readiness signal",
                body: "PR is marked ready for maintainer merge. Status is reported back to Baton's task graph as a structured evidence receipt.",
                tone: "green",
              },
            ].map(({ step, label, body, tone }) => {
              const colors: Record<string, string> = {
                blue: "bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300",
                green: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300",
                amber: "bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300",
              };
              return (
                <li key={step} className="mb-10 ml-8">
                  <span className="absolute -left-3.5 flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 bg-white font-mono text-xs font-bold text-slate-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400">
                    {step}
                  </span>
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50">{label}</h3>
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${colors[tone]}`}>{tone === "amber" ? "gate check" : tone === "blue" ? "automated" : "emits event"}</span>
                  </div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{body}</p>
                </li>
              );
            })}
          </ol>
        </section>

        {/* Private Preview Section */}
        <section className="mx-auto max-w-7xl px-6 py-12">
          <div className="rounded-lg border-2 border-amber-500 bg-gradient-to-r from-amber-50/90 to-orange-50/90 p-8 text-center backdrop-blur-sm dark:from-amber-950/80 dark:to-orange-950/80">
            <div className="mb-2 text-sm font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-300">
              🔒 Private Preview
            </div>
            <h2 className="mb-4 text-2xl font-bold text-slate-900 dark:text-slate-50">
              Join the CodeFlow Engine Private Preview - Help Shape the Future!
            </h2>
            <p className="mb-6 text-lg text-slate-700 dark:text-slate-300">
              CodeFlow Engine is in active development. Join our private preview to experience the power
              of AI-powered PR automation and help us improve with your feedback.
            </p>
            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/login"
                className="inline-block rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-3 text-lg font-semibold text-white transition-all hover:from-blue-700 hover:to-purple-700 hover:shadow-lg"
              >
                Request Private Preview →
              </Link>
              <a
                href="https://github.com/celladore/codeflow-engine/discussions"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block rounded-lg border-2 border-amber-500 bg-white/50 px-8 py-3 text-lg font-semibold text-amber-700 backdrop-blur-sm transition-colors hover:bg-amber-100 dark:bg-slate-800/50 dark:text-amber-300 dark:hover:bg-amber-900/50"
              >
                Share Feedback
              </a>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="mx-auto max-w-7xl px-6 py-24">
          <div className="rounded-lg border border-slate-200 bg-gradient-to-r from-slate-100 to-slate-50 p-12 text-center dark:border-slate-700 dark:from-slate-800 dark:to-slate-900">
            <h2 className="mb-4 text-3xl font-bold text-slate-900 dark:text-white">
              Ready to Transform Your Workflow?
            </h2>
            <p className="mb-8 text-xl text-slate-600 dark:text-slate-300">
              Get started with the CodeFlow Engine private preview today and experience the future of PR automation.
            </p>
            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/login"
                className="inline-block rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 px-8 py-3 text-lg font-semibold text-white transition-all hover:from-blue-600 hover:to-purple-600 hover:shadow-lg"
              >
                Request Private Preview
              </Link>
              <Link
                href="/installation"
                className="inline-block rounded-lg border-2 border-slate-300 bg-white px-8 py-3 text-lg font-semibold text-slate-900 transition-colors hover:border-slate-400 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:hover:border-slate-500 dark:hover:bg-slate-700"
              >
                <a href={href} target="_blank" rel="noopener noreferrer" className="min-w-[80px] font-semibold text-blue-600 hover:underline dark:text-blue-400">
                  {name}
                </a>
                <span className="hidden min-w-[160px] font-mono text-xs text-slate-400 dark:text-slate-500 sm:block pt-0.5">
                  {rel}
                </span>
                <p className="text-sm text-slate-500 dark:text-slate-400">{desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Spec quick reference */}
        <section className="border-t border-slate-200 bg-slate-50 py-16 dark:border-slate-700 dark:bg-slate-800/40">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-8 text-xl font-bold text-slate-900 dark:text-slate-50">Quick reference</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { label: "Runtime", value: "Temporal + CrewAI / Python 3.12 + Node 22" },
                { label: "Deployment", value: "AKS / Azure Container Apps" },
                { label: "Triggers", value: "GitHub App webhooks — PR open / sync" },
                { label: "License", value: "MIT — github.com/celladore/codeflow-engine" },
              ].map(({ label, value }) => (
                <div key={label} className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
                  <div className="mb-1 font-mono text-xs font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">{label}</div>
                  <div className="text-sm font-medium text-slate-800 dark:text-slate-200">{value}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

      </main>

      <Footer />
    </div>
  );
}
