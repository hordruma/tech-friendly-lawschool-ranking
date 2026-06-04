import Link from "next/link";
import type { Metadata } from "next";
import { getAllSchoolSummaries } from "@/lib/data";
import { SchoolCard } from "@/components/SchoolCard";
import { ScoreBadge } from "@/components/ScoreBadge";

export const metadata: Metadata = {
  title: "Tech-Friendly Law School Ranking — Global LegalTech Rankings",
};

export default function HomePage() {
  const schools = getAllSchoolSummaries();
  const topSchools = schools.filter((s) => s.scores?.total !== null).slice(0, 3);
  const totalSchools = schools.length;
  const verifiedSchools = schools.filter((s) => s.last_verified !== null).length;
  const prGapSchools = schools.filter((s) => s.press_release_gap_count > 0).length;

  return (
    <div>
      {/* Hero */}
      <section className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 text-xs font-semibold text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-950 px-3 py-1 rounded-full mb-6 uppercase tracking-wide">
              Global · Evidence-Based · Open Source
            </div>
            <h1 className="font-serif text-4xl sm:text-5xl font-bold text-gray-900 dark:text-gray-100 leading-tight">
              Which law schools{" "}
              <em className="not-italic text-brand-600 dark:text-brand-400">
                actually
              </em>{" "}
              embrace legal technology?
            </h1>
            <p className="mt-5 text-lg text-gray-500 dark:text-gray-400 leading-relaxed">
              Most law school rankings measure prestige. This one measures
              something different: whether a school genuinely prepares students
              for technology-integrated legal practice — through curriculum,
              infrastructure, faculty, and community. And whether its marketing
              matches reality.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/rankings"
                className="px-5 py-2.5 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors"
              >
                View Rankings →
              </Link>
              <Link
                href="/methodology"
                className="px-5 py-2.5 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                Read Methodology
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats bar */}
      <section className="bg-gray-50 dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-wrap gap-8">
            <Stat value={totalSchools} label="Schools indexed" />
            <Stat value={verifiedSchools} label="Human-verified" />
            <Stat value={prGapSchools} label="Press release gaps found" highlight />
          </div>
        </div>
      </section>

      {/* Top schools */}
      {topSchools.length > 0 && (
        <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-serif text-2xl font-semibold text-gray-900 dark:text-gray-100">
              Top Ranked Schools
            </h2>
            <Link
              href="/rankings"
              className="text-sm text-brand-600 dark:text-brand-400 hover:underline"
            >
              View all →
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {topSchools.map((school, i) => (
              <SchoolCard key={school.id} school={school} rank={i + 1} />
            ))}
          </div>
        </section>
      )}

      {/* Preview table — all schools stub */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-serif text-2xl font-semibold text-gray-900 dark:text-gray-100">
            All Schools
          </h2>
          <Link
            href="/rankings"
            className="text-sm text-brand-600 dark:text-brand-400 hover:underline"
          >
            Sortable table →
          </Link>
        </div>
        <div className="rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-800 text-left">
                <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">#</th>
                <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">School</th>
                <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Country</th>
                <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400 text-center">Tier</th>
                <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400 text-right">Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {schools.map((school, i) => (
                <tr key={school.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                  <td className="px-4 py-3 text-xs text-gray-400 font-mono">#{i + 1}</td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/schools/${school.id}`}
                      className="font-medium text-gray-900 dark:text-gray-100 hover:text-brand-600 dark:hover:text-brand-400"
                    >
                      {school.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-500 dark:text-gray-400">
                    {school.country}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <ScoreBadge tier={school.ranking_tier} size="sm" />
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-gray-700 dark:text-gray-300">
                    {school.scores?.total !== null && school.scores?.total !== undefined
                      ? school.scores.total.toFixed(0)
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Press Release Gap feature callout */}
      <section className="bg-red-50 dark:bg-red-950/30 border-y border-red-200 dark:border-red-900">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center text-xl">
              ⚠️
            </div>
            <div>
              <h2 className="font-serif text-xl font-semibold text-red-900 dark:text-red-200 mb-2">
                The Press Release Gap
              </h2>
              <p className="text-red-800 dark:text-red-300 leading-relaxed max-w-2xl">
                A Press Release Gap occurs when a law school publicly markets a
                program, center, or initiative that no longer exists or no
                longer functions as described. It&apos;s the gap between what
                the school&apos;s PR team announces and what students actually
                find on day one.
              </p>
              <p className="mt-2 text-red-700 dark:text-red-400 text-sm">
                We document these gaps, apply score penalties (−5 to −20
                points), and publish the evidence. Schools may dispute our
                findings — see our{" "}
                <Link href="/methodology" className="underline hover:no-underline font-medium">
                  methodology
                </Link>{" "}
                for the process.
              </p>
              <div className="mt-4">
                <Link
                  href="https://github.com/your-org/tech-friendly-lawschool-ranking/issues/new?template=press-release-gap.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm px-4 py-2 bg-red-700 text-white rounded-lg hover:bg-red-800 transition-colors font-medium inline-block"
                >
                  Report a Press Release Gap
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h2 className="font-serif text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-8">
          How We Score
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <CriterionCard
            title="Curriculum (40 pts)"
            description="How many legaltech/AI courses are offered? Are they required or elective? Is there a practical tech requirement? Are there tech-integrated clinics?"
            points={40}
          />
          <CriterionCard
            title="Infrastructure (30 pts)"
            description="Does the school have a dedicated legaltech center? Joint degrees (JD/CS, JD/Data Science)? Formal industry partnerships?"
            points={30}
          />
          <CriterionCard
            title="Faculty & Research (20 pts)"
            description="How many full-time faculty have genuine technology expertise? How much legaltech research is being produced?"
            points={20}
          />
          <CriterionCard
            title="Community & Career (10 pts)"
            description="Are there active student legaltech organizations? Is there documented career placement in legaltech roles?"
            points={10}
          />
        </div>
        <p className="mt-6 text-sm text-gray-500 dark:text-gray-400">
          All scoring criteria are publicly documented.{" "}
          <Link href="/methodology" className="text-brand-600 dark:text-brand-400 hover:underline">
            Read the full methodology →
          </Link>
        </p>
      </section>
    </div>
  );
}

function Stat({
  value,
  label,
  highlight,
}: {
  value: number;
  label: string;
  highlight?: boolean;
}) {
  return (
    <div>
      <div
        className={`text-3xl font-serif font-bold ${
          highlight ? "text-red-600 dark:text-red-400" : "text-gray-900 dark:text-gray-100"
        }`}
      >
        {value}
      </div>
      <div className="text-sm text-gray-500 dark:text-gray-400">{label}</div>
    </div>
  );
}

function CriterionCard({
  title,
  description,
  points,
}: {
  title: string;
  description: string;
  points: number;
}) {
  return (
    <div className="p-5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-serif font-semibold text-gray-900 dark:text-gray-100">
          {title}
        </h3>
        <span className="text-sm font-mono text-brand-600 dark:text-brand-400 font-semibold">
          {points} pts
        </span>
      </div>
      <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
        {description}
      </p>
    </div>
  );
}
