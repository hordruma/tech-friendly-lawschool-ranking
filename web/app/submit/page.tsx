import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Contribute Data — Submit a School or Correction",
  description:
    "Submit a new law school, correct existing data, or report a press release gap to the Tech-Friendly Law School Ranking.",
};

const GITHUB_ORG = "your-org";
const REPO = "tech-friendly-lawschool-ranking";
const BASE_URL = `https://github.com/${GITHUB_ORG}/${REPO}`;

function issueUrl(template: string, title?: string) {
  const params = new URLSearchParams({ template });
  if (title) params.set("title", title);
  return `${BASE_URL}/issues/new?${params.toString()}`;
}

export default function SubmitPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-400 dark:text-gray-500 flex items-center gap-2">
        <Link href="/" className="hover:text-gray-700 dark:hover:text-gray-300">Home</Link>
        <span>/</span>
        <span className="text-gray-600 dark:text-gray-400">Contribute</span>
      </nav>

      {/* Header */}
      <div>
        <h1 className="font-serif text-3xl font-bold text-gray-900 dark:text-gray-100">
          Contribute Data
        </h1>
        <p className="mt-3 text-gray-500 dark:text-gray-400 leading-relaxed">
          This ranking is only as good as its data. We actively welcome corrections,
          additions, and press release gap reports from anyone — students, faculty,
          practitioners, and members of the public.
        </p>
        <p className="mt-2 text-gray-500 dark:text-gray-400 leading-relaxed">
          All contributions are reviewed before publication. Accepted changes are
          merged via pull request and attributed in git history. There is no
          requirement to identify yourself.
        </p>
      </div>

      {/* Contribution types */}
      <div className="space-y-4">
        {/* New school */}
        <ContributionCard
          icon="🏫"
          title="Submit a New School"
          description="Know a law school with notable legaltech programs that isn't in the ranking yet? Submit it with as much evidence as you can gather."
          badge="New school"
          badgeColor="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
          href={issueUrl("school-submission.md", "[SCHOOL] New School — <School Name>")}
          cta="Open submission form →"
          fields={[
            "School name, country, jurisdiction, official URL",
            "LegalTech/AI courses (title, required/elective, credit hours, catalog URL)",
            "Programs: centers, joint degrees, clinics, incubators",
            "Faculty with tech expertise (name, title, appointment type, profile URL)",
            "Industry and institutional partnerships",
            "Student organizations",
          ]}
        />

        {/* Correction */}
        <ContributionCard
          icon="✏️"
          title="Correct an Existing Record"
          description="Something in our data is wrong or out of date? Please let us know. Include a source URL and the date you verified it."
          badge="Correction"
          badgeColor="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
          href={issueUrl("school-submission.md", "[SCHOOL] Correction — <School Name>")}
          cta="Submit a correction →"
          fields={[
            "The school ID from the ranking (e.g., harvard-law)",
            "Exactly what is incorrect and what the correct information is",
            "A source URL from the school's official website",
            "The date you verified the source",
          ]}
        />

        {/* Press Release Gap */}
        <div className="p-6 rounded-xl border-2 border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-950/30">
          <div className="flex items-start gap-3">
            <span className="text-2xl">⚠️</span>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <h3 className="font-serif font-semibold text-gray-900 dark:text-gray-100 text-lg">
                  Report a Press Release Gap
                </h3>
                <span className="text-xs px-2 py-0.5 rounded-full font-semibold bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                  Accountability feature
                </span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 leading-relaxed">
                A <strong>Press Release Gap</strong> is the gap between a law school&apos;s
                marketing claims and current reality. If you&apos;ve found a school
                marketing a program that no longer exists, this is the most impactful
                contribution you can make to this ranking.
              </p>
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-4 space-y-1">
                <p className="font-medium text-gray-700 dark:text-gray-300">
                  What to include:
                </p>
                <ul className="space-y-1 ml-4 list-disc">
                  <li>The original claim (URL to press release, website, or archive.org)</li>
                  <li>The current reality (URL to current catalog or absence thereof)</li>
                  <li>When the claim was made (approximate year)</li>
                  <li>Whether the claim is still being circulated</li>
                </ul>
              </div>
              <a
                href={issueUrl("press-release-gap.md", "[PRG] <School Name> — <Description>")}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block text-sm px-4 py-2 bg-red-700 text-white rounded-lg hover:bg-red-800 transition-colors font-medium"
              >
                Report a Press Release Gap →
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Pull request guide */}
      <section>
        <h2 className="font-serif text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Contributing via Pull Request
        </h2>
        <div className="space-y-3 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <p>
            For technical contributors, the most direct way to improve the data is
            to submit a pull request against the{" "}
            <a
              href={`${BASE_URL}/tree/main/data/schools`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand-600 dark:text-brand-400 hover:underline"
            >
              <code>data/schools/</code>
            </a>{" "}
            directory.
          </p>
          <ol className="list-decimal ml-5 space-y-2">
            <li>
              Fork the repository on{" "}
              <a href={BASE_URL} target="_blank" rel="noopener noreferrer" className="text-brand-600 dark:text-brand-400 hover:underline">
                GitHub
              </a>
            </li>
            <li>
              Edit or add JSON files in <code>data/schools/</code> following the{" "}
              <a
                href={`${BASE_URL}/blob/main/data/schema/school.schema.json`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-600 dark:text-brand-400 hover:underline"
              >
                schema
              </a>
            </li>
            <li>
              Add <code>source_url</code> and <code>year_verified</code> for every
              field you add or change
            </li>
            <li>Open a pull request with a clear description of your changes</li>
          </ol>
          <p>
            All merged PRs are credited in git history. If you prefer to stay
            anonymous, use a GitHub account that doesn&apos;t identify you.
          </p>
        </div>
      </section>

      {/* What we don't accept */}
      <section>
        <h2 className="font-serif text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Submission Standards
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div className="p-4 rounded-lg bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800">
            <h4 className="font-semibold text-green-800 dark:text-green-200 mb-2">We accept</h4>
            <ul className="space-y-1.5 text-green-700 dark:text-green-300">
              <li>✓ Direct links to official school websites</li>
              <li>✓ Links to current course catalogs</li>
              <li>✓ Official faculty profile pages</li>
              <li>✓ Archive.org links to historical pages</li>
              <li>✓ Published academic papers and reports</li>
              <li>✓ Regulatory filings and official publications</li>
            </ul>
          </div>
          <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800">
            <h4 className="font-semibold text-red-800 dark:text-red-200 mb-2">We don&apos;t accept</h4>
            <ul className="space-y-1.5 text-red-700 dark:text-red-300">
              <li>✗ Claims without source URLs</li>
              <li>✗ Secondhand or hearsay information</li>
              <li>✗ Marketing materials without verification</li>
              <li>✗ Submissions from parties with undisclosed conflicts of interest</li>
              <li>✗ AI-generated content without primary source verification</li>
              <li>✗ PRG reports without original claim evidence</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}

function ContributionCard({
  icon,
  title,
  description,
  badge,
  badgeColor,
  href,
  cta,
  fields,
}: {
  icon: string;
  title: string;
  description: string;
  badge: string;
  badgeColor: string;
  href: string;
  cta: string;
  fields: string[];
}) {
  return (
    <div className="p-6 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
      <div className="flex items-start gap-3">
        <span className="text-2xl flex-shrink-0">{icon}</span>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <h3 className="font-serif font-semibold text-gray-900 dark:text-gray-100 text-lg">
              {title}
            </h3>
            <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${badgeColor}`}>
              {badge}
            </span>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">{description}</p>
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            <p className="font-medium text-gray-700 dark:text-gray-300 mb-1">What to include:</p>
            <ul className="space-y-1 ml-4 list-disc">
              {fields.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          </div>
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-brand-600 dark:text-brand-400 hover:underline font-medium"
          >
            {cta}
          </a>
        </div>
      </div>
    </div>
  );
}
