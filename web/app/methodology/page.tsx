import type { Metadata } from "next";
import Link from "next/link";
import { getCriteriaMarkdown } from "@/lib/data";

export const metadata: Metadata = {
  title: "Methodology — How We Rank Law Schools on LegalTech",
  description:
    "Full public methodology for the Tech-Friendly Law School Ranking, including the complete scoring rubric, data collection process, and the Press Release Gap accountability mechanism.",
};

// Simple markdown-to-HTML renderer (avoids heavy remark dep for simple cases)
function markdownToHtml(markdown: string): string {
  let html = markdown;

  // Headers
  html = html.replace(/^#### (.+)$/gm, "<h4>$1</h4>");
  html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

  // Horizontal rules
  html = html.replace(/^---$/gm, "<hr>");

  // Tables (basic)
  const tableRegex = /\|(.+)\|\n\|[-\s|]+\|\n((?:\|.+\|\n?)+)/g;
  html = html.replace(tableRegex, (match, header, body) => {
    const headers = header.split("|").map((h: string) => h.trim()).filter(Boolean);
    const rows = body.trim().split("\n").map((row: string) => {
      const cells = row.split("|").map((c: string) => c.trim()).filter(Boolean);
      return `<tr>${cells.map((c: string) => `<td>${c}</td>`).join("")}</tr>`;
    });
    const thead = `<thead><tr>${headers.map((h: string) => `<th>${h}</th>`).join("")}</tr></thead>`;
    const tbody = `<tbody>${rows.join("")}</tbody>`;
    return `<div class="overflow-x-auto"><table class="min-w-full">${thead}${tbody}</table></div>`;
  });

  // Bold and italic
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
  html = html.replace(/_(.+?)_/g, "<em>$1</em>");
  html = html.replace(/`(.+?)`/g, "<code>$1</code>");

  // Links
  html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2">$1</a>');

  // Bullet lists
  html = html.replace(/((?:^- .+$\n?)+)/gm, (match) => {
    const items = match.trim().split("\n").map((line: string) =>
      `<li>${line.replace(/^- /, "")}</li>`
    );
    return `<ul>${items.join("")}</ul>`;
  });

  // Numbered lists
  html = html.replace(/((?:^\d+\. .+$\n?)+)/gm, (match) => {
    const items = match.trim().split("\n").map((line: string) =>
      `<li>${line.replace(/^\d+\. /, "")}</li>`
    );
    return `<ol>${items.join("")}</ol>`;
  });

  // Paragraphs (lines not starting with tags)
  const lines = html.split("\n");
  const processed: string[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i].trim();
    if (line === "" || line.startsWith("<")) {
      processed.push(line);
    } else {
      processed.push(`<p>${line}</p>`);
    }
    i++;
  }

  return processed.join("\n");
}

export default function MethodologyPage() {
  const markdown = getCriteriaMarkdown();

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-400 dark:text-gray-500 flex items-center gap-2 mb-8">
        <Link href="/" className="hover:text-gray-700 dark:hover:text-gray-300">Home</Link>
        <span>/</span>
        <span className="text-gray-600 dark:text-gray-400">Methodology</span>
      </nav>

      {/* Intro banner */}
      <div className="mb-8 p-5 rounded-xl bg-brand-50 dark:bg-brand-950/30 border border-brand-200 dark:border-brand-800">
        <h2 className="font-serif font-semibold text-brand-900 dark:text-brand-200 mb-2">
          Public Methodology — Version 1.0
        </h2>
        <p className="text-sm text-brand-700 dark:text-brand-300">
          This document describes exactly how scores are calculated. Every scoring decision
          is traceable to this document. Methodology changes are versioned in git and schools
          are notified before scores are updated.
        </p>
        <div className="mt-3 flex flex-wrap gap-3">
          <a
            href="https://github.com/your-org/tech-friendly-lawschool-ranking/blob/main/CRITERIA.md"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-brand-600 dark:text-brand-400 hover:underline"
          >
            View on GitHub (with history) →
          </a>
          <Link
            href="/submit"
            className="text-sm text-brand-600 dark:text-brand-400 hover:underline"
          >
            Suggest a methodology change →
          </Link>
        </div>
      </div>

      {/* Quick navigation */}
      <div className="mb-8 p-4 rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Sections</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-1 text-sm">
          {[
            ["Purpose & Scope", "#1-purpose-and-scope"],
            ["What We Measure", "#2-what-we-measure-and-why"],
            ["Curriculum (40 pts)", "#31-curriculum-40-points"],
            ["Infrastructure (30 pts)", "#32-infrastructure-30-points"],
            ["Faculty & Research (20 pts)", "#33-faculty--research-20-points"],
            ["Community (10 pts)", "#34-community--career-10-points"],
            ["Press Release Gap ⚠️", "#35-press-release-gap--5-to--20-points"],
            ["Tiers", "#4-ranking-tiers"],
            ["Data Collection", "#5-data-collection-and-verification"],
            ["How to Submit", "#6-how-to-submit-corrections"],
          ].map(([label, href]) => (
            <a
              key={href}
              href={href}
              className="text-brand-600 dark:text-brand-400 hover:underline py-0.5"
            >
              {label}
            </a>
          ))}
        </div>
      </div>

      {/* Rendered criteria */}
      <article
        className="prose prose-gray dark:prose-invert max-w-none
          prose-headings:font-serif prose-headings:font-semibold
          prose-h1:text-3xl prose-h2:text-2xl prose-h3:text-xl prose-h4:text-lg
          prose-a:text-brand-600 dark:prose-a:text-brand-400 prose-a:no-underline hover:prose-a:underline
          prose-code:text-sm prose-code:bg-gray-100 dark:prose-code:bg-gray-800 prose-code:px-1 prose-code:rounded
          prose-table:text-sm
          prose-strong:text-gray-900 dark:prose-strong:text-gray-100
          "
        dangerouslySetInnerHTML={{ __html: markdownToHtml(markdown) }}
      />

      {/* Footer CTA */}
      <div className="mt-12 p-5 rounded-xl bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
        <h3 className="font-serif font-semibold text-gray-900 dark:text-gray-100 mb-2">
          Questions about the methodology?
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          Open a GitHub issue to suggest improvements or flag edge cases we
          haven&apos;t addressed.
        </p>
        <a
          href="https://github.com/your-org/tech-friendly-lawschool-ranking/issues/new"
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-brand-600 dark:text-brand-400 hover:underline"
        >
          Open an issue →
        </a>
      </div>
    </div>
  );
}
