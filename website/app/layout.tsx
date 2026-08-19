import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import PromoBanner from "./components/PromoBanner";
import { ThemeProvider } from "./components/ThemeProvider";
import AnimatedBackground from "./components/AnimatedBackground";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
  display: "swap",
  fallback: ["system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "Helvetica Neue", "Arial", "sans-serif"],
});

const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
  display: "swap",
  fallback: ["ui-monospace", "SFMono-Regular", "SF Mono", "Menlo", "Consolas", "Liberation Mono", "monospace"],
});

export const metadata: Metadata = {
  title: "CodeFlow - AI-Powered GitHub PR Automation (Private Preview)",
  description: "Transform your GitHub pull request workflows through intelligent analysis, issue creation, and multi-agent collaboration. Currently in private preview.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ThemeProvider>
          {/* Skip link for keyboard/screen reader accessibility */}
          <a href="#main-content" className="skip-link">
            Skip to main content
          </a>
          <AnimatedBackground />
          <PromoBanner />
          <main id="main-content" className="relative z-10" role="main">
            {children}
          </main>
        </ThemeProvider>
      </body>
    </html>
  );
}
