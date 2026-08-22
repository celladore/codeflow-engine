import Link from "next/link";
import Header from "./components/Header";
import Footer from "./components/Footer";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-slate-50/80 to-slate-100/50 dark:from-slate-900/80 dark:to-slate-950/50">
      <Header currentPage="home" />

      <main className="flex-1">

        {/* Hero */}
        <section className="mx-auto max-w-5xl px-6 py-24 text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-1.5 text-sm font-medium text-blue-700 dark:border-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-500"></span>
            Open source · MIT · Alpha
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
              View on GitHub
            </a>
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
          <ol className="relative ml-4 border-l border-slate-200 dark:border-slate-700">
            {[
              {
                step: "01",
                label: "Webhook received",
                badge: "automated",
                body: "GitHub App receives pull_request.opened or pull_request.synchronize and dispatches to the CodeFlow workflow engine.",
                tone: "blue",
              },
              {
                step: "02",
                label: "Temporal workflow started",
                badge: "durable",
                body: "A durable workflow execution is created. From this point forward, any crash or network interruption is fully recoverable.",
                tone: "green",
              },
              {
                step: "03",
                label: "Multi-agent analysis crew",
                badge: "automated",
                body: "CrewAI agents run architecture review, security scanning, and diff analysis in parallel — with optional Sluice routing for failover and cost tracking.",
                tone: "blue",
              },
              {
                step: "04",
                label: "Quality gate evaluation",
                badge: "gate check",
                body: "Security thresholds, coverage minimums, and custom gates evaluate the crew\x27s output. A failure blocks merge readiness.",
                tone: "amber",
              },
              {
                step: "05",
                label: "Issue creation & annotation",
                badge: "automated",
                body: "Findings are filed as GitHub issues. Structured events (analysis.completed, issues.created) are emitted to configured notification channels.",
                tone: "blue",
              },
              {
                step: "06",
                label: "Merge readiness signal",
                badge: "complete",
                body: "PR is marked ready for maintainer merge. Status can be reported to a task tracker (e.g. Baton) if configured.",
                tone: "green",
              },
            ].map(({ step, label, badge, body, tone }) => {
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
                  <div className="mb-1 flex items-center gap-3">
                    <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50">{label}</h3>
                    <span className={ounded-full px-2 py-0.5 text-xs font-medium }>{badge}</span>
                  </div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{body}</p>
                </li>
              );
            })}
          </ol>
        </section>

        {/* Key capabilities */}
        <section className="border-y border-slate-200 bg-white/60 py-20 dark:border-slate-700 dark:bg-slate-800/30">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-12 text-center text-2xl font-bold text-slate-900 dark:text-slate-50">
              What makes it different
            </h2>
            <div className="grid gap-8 md:grid-cols-3">
              {[
                {
                  title: "Temporal state durability",
                  body: "Multi-hour pipelines survive network drops and process restarts. Workflows resume exactly where they left off — no lost work, no full restart.",
                },
                {
                  title: "GitHub App + webhook pipeline",
                  body: "Triggers on pull_request.opened and pull_request.synchronize. Emits structured events: analysis.completed, issues.created, security.alert, quality.gate.failed.",
                },
                {
                  title: "Declarative .codeflow.yml",
                  body: "Per-repo config controls AI provider, model, workflow triggers, quality gate thresholds, and notification channels. No code changes required.",
                },
                {
                  title: "Git worktree isolation",
                  body: "Automated refactors run in ephemeral, isolated worktrees — clean commits guaranteed, main working tree never contaminated.",
                },
                {
                  title: "Merge readiness verification",
                  body: "Test coverage, security scans, and gate approvals are verified before signaling PRs as ready — not just a diff someone has to eyeball.",
                },
                {
                  title: "Ecosystem-native",
                  body: "Sluice can handle model routing and failover (optional). Baton can receive PR status as evidence receipts when configured. Retort quality gates can trigger workflow dispatch.",
                },
              ].map(({ title, body }) => (
                <div key={title} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
                  <h3 className="mb-2 font-semibold text-slate-900 dark:text-slate-50">{title}</h3>
                  <p className="text-sm leading-relaxed text-slate-500 dark:text-slate-400">{body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Ecosystem */}
        <section className="mx-auto max-w-5xl px-6 py-20">
          <h2 className="mb-3 text-2xl font-bold text-slate-900 dark:text-slate-50">Part of the Celladore ecosystem</h2>
          <p className="mb-8 max-w-2xl text-slate-500 dark:text-slate-400">
            CodeFlow is a runtime execution layer — a distinct role from the other tools it coordinates with.
          </p>
          <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700">
            {[
              {
                name: "Baton",
                href: "https://baton.celladoresystems.com",
                rel: "Task graph (optional)",
                desc: "When configured, CodeFlow can report PR creation, review outcomes, and merge status back to Baton as structured evidence receipts on the originating task.",
              },
              {
                name: "Retort",
                href: "https://retort.celladoresystems.com",
                rel: "Quality gates → triggers",
                desc: "Outputs that pass Retort\x27s deterministic quality gates can trigger CodeFlow Temporal workflows for automated branch creation and PR synthesis.",
              },
              {
                name: "Sluice",
                href: "https://sluice.celladoresystems.com",
                rel: "Model gateway (optional)",
                desc: "CodeFlow can route LLM calls through Sluice for failover, rate limits, and cost attribution — or call providers directly if Sluice is not deployed.",
              },
              {
                name: "Docket",
                href: "https://docket.celladoresystems.com",
                rel: "Cost tracking",
                desc: "AutoPR AI spend is tracked per PR analysis run via Docket when Sluice is in the chain — so you know the cost of each automated review cycle.",
              },
            ].map(({ name, href, rel, desc }, i, arr) => (
              <div
                key={name}
                className={lex items-start gap-6 px-6 py-5 }
              >
                <a href={href} target="_blank" rel="noopener noreferrer" className="min-w-[80px] font-semibold text-blue-600 hover:underline dark:text-blue-400">
                  {name}
                </a>
                <span className="hidden min-w-[160px] pt-0.5 font-mono text-xs text-slate-400 dark:text-slate-500 sm:block">
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
                { label: "Runtime", value: "Temporal + CrewAI / Python 3.12 + Node.js 20.x" },
                { label: "Deployment", value: "Azure Static Web Apps (site) · Azure Container Apps (backend) · AKS (alt)" },
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
