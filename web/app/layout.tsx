import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Tech-Friendly Law School Ranking",
    template: "%s | Tech-Friendly Law School Ranking",
  },
  description:
    "A global, evidence-based ranking of law schools by genuine commitment to legal technology, artificial intelligence, and technology-integrated legal practice.",
  keywords: [
    "law school ranking",
    "legaltech",
    "legal technology",
    "AI law",
    "law school",
    "global ranking",
    "technology law education",
  ],
  openGraph: {
    type: "website",
    title: "Tech-Friendly Law School Ranking",
    description:
      "Global ranking of law schools by genuine legaltech commitment. Includes Press Release Gap accountability.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col">
        <Header />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}

function Header() {
  return (
    <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link
            href="/"
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          >
            <span className="font-serif font-bold text-lg text-gray-900 dark:text-gray-100">
              ⚖️ LegalTech Rankings
            </span>
          </Link>

          {/* Nav */}
          <nav className="hidden md:flex items-center gap-6">
            <NavLink href="/rankings">Rankings</NavLink>
            <NavLink href="/methodology">Methodology</NavLink>
            <NavLink href="/submit">Contribute</NavLink>
          </nav>

          {/* CTA */}
          <div className="flex items-center gap-3">
            <a
              href="https://github.com/your-org/tech-friendly-lawschool-ranking"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors hidden sm:block"
            >
              GitHub
            </a>
            <Link
              href="/submit"
              className="text-sm px-3 py-1.5 rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-colors font-medium"
            >
              Submit Data
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
    >
      {children}
    </Link>
  );
}

function Footer() {
  return (
    <footer className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
          <div>
            <h3 className="font-serif font-semibold text-gray-900 dark:text-gray-100 mb-3">
              LegalTech Rankings
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
              A global, evidence-based, community-maintained ranking of law
              schools by genuine legaltech commitment.
            </p>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
              Navigation
            </h4>
            <ul className="space-y-2 text-sm text-gray-500 dark:text-gray-400">
              <li><Link href="/rankings" className="hover:text-gray-900 dark:hover:text-gray-100">Rankings</Link></li>
              <li><Link href="/methodology" className="hover:text-gray-900 dark:hover:text-gray-100">Methodology</Link></li>
              <li><Link href="/submit" className="hover:text-gray-900 dark:hover:text-gray-100">Contribute</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
              Data & License
            </h4>
            <ul className="space-y-2 text-sm text-gray-500 dark:text-gray-400">
              <li>
                <a
                  href="https://github.com/your-org/tech-friendly-lawschool-ranking"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-gray-900 dark:hover:text-gray-100"
                >
                  GitHub Repository
                </a>
              </li>
              <li>Data: CC BY 4.0</li>
              <li>Code: MIT</li>
            </ul>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-gray-100 dark:border-gray-800 text-xs text-gray-400 dark:text-gray-500">
          This ranking is an independent project. We are not affiliated with any
          law school, rankings body, or legal publisher. Scores are based on
          publicly available information and community submissions.
        </div>
      </div>
    </footer>
  );
}
