import type { Metadata } from "next";
import { getAllSchoolSummaries, getAllCountries } from "@/lib/data";
import { RankingTable } from "@/components/RankingTable";

export const metadata: Metadata = {
  title: "Global LegalTech Law School Rankings",
  description:
    "Sortable, filterable global ranking of law schools by genuine commitment to legal technology, AI, and tech-integrated legal practice.",
};

export default function RankingsPage() {
  const schools = getAllSchoolSummaries();
  const countries = getAllCountries();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Page header */}
      <div className="mb-8">
        <h1 className="font-serif text-3xl font-bold text-gray-900 dark:text-gray-100">
          Global LegalTech Law School Rankings
        </h1>
        <p className="mt-2 text-gray-500 dark:text-gray-400 max-w-2xl">
          {schools.length} schools indexed. Sort by score, filter by country or
          tier. Schools marked{" "}
          <span className="italic">Unverified</span> have not been reviewed by
          a human editor.{" "}
          <a href="/methodology" className="text-brand-600 dark:text-brand-400 hover:underline">
            See methodology →
          </a>
        </p>
      </div>

      {/* Tier legend */}
      <div className="mb-6 flex flex-wrap gap-3 text-sm">
        {[
          { tier: "S", label: "Exemplary (85–100)", color: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200" },
          { tier: "A", label: "Strong (70–84)", color: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" },
          { tier: "B", label: "Developing (50–69)", color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200" },
          { tier: "C", label: "Limited (30–49)", color: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200" },
          { tier: "D", label: "Absent (<30)", color: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" },
          { tier: "?", label: "Unranked", color: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400" },
        ].map(({ tier, label, color }) => (
          <span key={tier} className={`px-2 py-1 rounded font-mono font-semibold ${color}`}>
            {tier} <span className="font-normal font-sans text-xs opacity-75">{label}</span>
          </span>
        ))}
      </div>

      <RankingTable schools={schools} countries={countries} />

      {/* Disclaimer */}
      <div className="mt-10 p-4 rounded-lg bg-gray-100 dark:bg-gray-800 text-sm text-gray-500 dark:text-gray-400">
        <strong className="text-gray-700 dark:text-gray-300">Data freshness note:</strong>{" "}
        Schools with <code>last_verified: null</code> have not been verified by
        a human reviewer. Scores for these schools are computed from available
        data and should be treated as provisional. Schools with verified data
        older than 18 months are displayed with reduced confidence.{" "}
        <a
          href="https://github.com/your-org/tech-friendly-lawschool-ranking/issues/new?template=school-submission.md"
          target="_blank"
          rel="noopener noreferrer"
          className="text-brand-600 dark:text-brand-400 hover:underline"
        >
          Help us verify schools →
        </a>
      </div>
    </div>
  );
}
