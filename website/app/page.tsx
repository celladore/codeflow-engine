import Link from "next/link";
import Header from "./components/Header";
import Footer from "./components/Footer";
import { FeatureCard } from "./components/FeatureCard";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-slate-50/80 to-slate-100/50 dark:from-slate-900/80 dark:to-slate-950/50">
      {/* Header */}
      <Header currentPage="home" />

      {/* Hero Section */}
      <main className="flex-1">
        <section className="mx-auto max-w-7xl px-6 py-24 text-center">
          <div className="mb-8 inline-block rounded-full bg-gradient-to-r from-amber-50 to-orange-50 px-6 py-2 text-sm font-semibold text-amber-900 dark:from-amber-950/80 dark:to-orange-950/80 dark:text-amber-100">
            🔒 Private Preview - Request early access →
          </div>
          <h1 className="mb-6 text-5xl font-bold tracking-tight text-slate-900 dark:text-slate-50 sm:text-6xl">
            AI-Powered GitHub PR Automation
          </h1>
          <p className="mx-auto mb-12 max-w-2xl text-xl text-slate-600 dark:text-slate-400">
            Transform your GitHub pull request workflows through intelligent analysis,
            issue creation, and multi-agent collaboration.
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/login"
              className="rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-3 text-lg font-semibold text-white transition-all hover:from-blue-700 hover:to-purple-700 hover:shadow-lg"
            >
              Request Private Preview
            </Link>
            <Link
              href="/signup"
              className="rounded-lg bg-slate-800 px-8 py-3 text-lg font-semibold text-white transition-colors hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200"
            >
              Get Started
            </Link>
            <Link
              href="/download"
              className="rounded-lg border-2 border-slate-300 bg-white/50 px-8 py-3 text-lg font-semibold text-slate-900 backdrop-blur-sm transition-colors hover:border-slate-400 dark:border-slate-600 dark:bg-slate-800/50 dark:text-slate-50 dark:hover:border-slate-500"
            >
              Download
            </Link>
          </div>
        </section>

        {/* Features Section */}
        <section className="mx-auto max-w-7xl px-6 py-24">
          <h2 className="mb-12 text-center text-3xl font-bold text-slate-900 dark:text-slate-50">
            Key Features
          </h2>
          <div className="grid gap-8 md:grid-cols-3">
            <FeatureCard
              icon="🤖"
              title="AI-Powered Analysis"
              description="Intelligent code analysis using GPT-4, Claude, and other leading AI models to provide comprehensive PR reviews."
            />
            <FeatureCard
              icon="🔄"
              title="Automated Workflows"
              description="Create custom workflows to automate issue creation, code reviews, and deployment processes."
            />
            <FeatureCard
              icon="🚀"
              title="Multi-Agent Collaboration"
              description="Leverage multiple AI agents working together to handle complex development tasks efficiently."
            />
          </div>
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
                Install Now
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
