import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getAllSchoolIds, getSchoolById, getCountryName } from "@/lib/data";
import { computeScores, computeMetaScore } from "@/lib/scoring";
import { ScoreBadge, ScoreBar } from "@/components/ScoreBadge";
import { PressReleaseGapAlert } from "@/components/PressReleaseGapAlert";
import type { Course, Program, Faculty, Partnership, StudentOrg, ExternalRankings } from "@/lib/types";
import { EXTERNAL_RANKING_LABELS, EXTERNAL_RANKING_URLS } from "@/lib/types";

interface Props {
  params: { id: string };
}

export async function generateStaticParams() {
  return getAllSchoolIds().map((id) => ({ id }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const school = getSchoolById(params.id);
  if (!school) return { title: "School Not Found" };

  return {
    title: `${school.name} — LegalTech Ranking`,
    description: `LegalTech ranking profile for ${school.name}. Scores, programs, courses, faculty, and press release gap analysis.`,
  };
}

export default function SchoolPage({ params }: Props) {
  const school = getSchoolById(params.id);

  if (!school) notFound();

  // Compute scores (use stored scores if available, otherwise compute live)
  const computed = computeScores(school);
  const scores = school.scores ?? computed.scores;
  const tier = school.ranking_tier ?? computed.ranking_tier;
  const criteria = computed.criteria;

  // Compute meta score
  const metaComputed = computeMetaScore(school);
  const metaScore = school.meta_score ?? metaComputed.meta_score;
  const prestigeScore = metaComputed.prestige_score;
  const externalScoresNormalized = metaComputed.external_scores_normalized;

  const isVerified = school.last_verified !== null;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-400 dark:text-gray-500 flex items-center gap-2">
        <Link href="/" className="hover:text-gray-700 dark:hover:text-gray-300">Home</Link>
        <span>/</span>
        <Link href="/rankings" className="hover:text-gray-700 dark:hover:text-gray-300">Rankings</Link>
        <span>/</span>
        <span className="text-gray-600 dark:text-gray-400">{school.name}</span>
      </nav>

      {/* School header */}
      <div className="flex flex-col sm:flex-row sm:items-start gap-4 sm:gap-6">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="font-serif text-3xl font-bold text-gray-900 dark:text-gray-100">
              {school.name}
            </h1>
            <ScoreBadge tier={tier} score={scores?.total} size="lg" />
          </div>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500 dark:text-gray-400">
            <span>{getCountryName(school.country)}{school.jurisdiction && `, ${school.jurisdiction}`}</span>
            <a
              href={school.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand-600 dark:text-brand-400 hover:underline"
            >
              Official website ↗
            </a>
            {isVerified ? (
              <span className="text-green-600 dark:text-green-400">
                ✓ Verified {school.last_verified}
              </span>
            ) : (
              <span className="italic text-amber-600 dark:text-amber-400">
                ⚠ Not yet human-verified — scores are provisional
              </span>
            )}
          </div>

          {/* Accreditation */}
          {school.accreditation.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {school.accreditation.map((acc, i) => (
                <span
                  key={i}
                  className="text-xs px-2 py-0.5 rounded-full border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400"
                >
                  {acc.body} ({acc.jurisdiction})
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Press Release Gaps — show prominently if any */}
      {school.press_release_gap.length > 0 && (
        <PressReleaseGapAlert
          gaps={school.press_release_gap}
          schoolName={school.name}
        />
      )}

      {/* Notes */}
      {school.notes && (
        <div className="p-4 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-sm text-amber-800 dark:text-amber-300">
          <strong>Editorial note:</strong> {school.notes}
        </div>
      )}

      {/* Score breakdown */}
      <section>
        <SectionHeader title="Score Breakdown" />
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {criteria.map((c) => {
            if (c.key === "press_release_gap_penalty") return null;
            return (
              <div key={c.key} className="p-4 rounded-lg bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
                <ScoreBar
                  score={c.score}
                  max={c.max}
                  label={c.label}
                  color={c.score === c.max ? "bg-green-500" : undefined}
                />
              </div>
            );
          })}
        </div>

        {/* Total */}
        <div className="mt-4 p-4 rounded-lg bg-gray-900 dark:bg-gray-800 text-white flex items-center justify-between">
          <div>
            <div className="text-sm text-gray-400 mb-0.5">Total Score</div>
            <div className="text-3xl font-serif font-bold">
              {scores?.total?.toFixed(0) ?? "—"}
              <span className="text-lg text-gray-400 font-normal">/100</span>
            </div>
            {(scores?.press_release_gap_penalty ?? 0) < 0 && (
              <div className="text-sm text-red-400 mt-1">
                Includes {scores?.press_release_gap_penalty} press release gap penalty
              </div>
            )}
          </div>
          <ScoreBadge tier={tier} size="lg" showLabel />
        </div>

        {!isVerified && (
          <p className="mt-3 text-xs text-amber-600 dark:text-amber-400">
            These scores have not been reviewed by a human editor. Data marked
            without <code>year_verified</code> is excluded from scoring.{" "}
            <a
              href="https://github.com/your-org/tech-friendly-lawschool-ranking/issues/new?template=school-submission.md"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:no-underline"
            >
              Help verify this record
            </a>
            .
          </p>
        )}
      </section>

      {/* Meta Score & External Rankings */}
      <section>
        <SectionHeader title="Global Prestige & Meta Rank" />
        <div className="mt-4 p-4 rounded-lg bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800">
          <p className="text-xs text-indigo-700 dark:text-indigo-300 mb-4">
            <strong>Meta rank = 50% tech friendliness + 50% global prestige.</strong>{" "}
            Prestige is a normalized composite of major global law school rankings.
            Missing rankings are excluded from the average, not zeroed.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
            <div className="p-3 rounded-lg bg-white dark:bg-gray-900 border border-indigo-100 dark:border-indigo-900 text-center">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">Tech Score</div>
              <div className="text-2xl font-serif font-bold text-gray-900 dark:text-gray-100">
                {scores?.total?.toFixed(0) ?? "—"}
                <span className="text-sm font-normal text-gray-400">/100</span>
              </div>
            </div>
            <div className="p-3 rounded-lg bg-white dark:bg-gray-900 border border-indigo-100 dark:border-indigo-900 text-center">
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5">Prestige Score</div>
              <div className="text-2xl font-serif font-bold text-indigo-700 dark:text-indigo-300">
                {prestigeScore !== null ? prestigeScore.toFixed(1) : "—"}
                <span className="text-sm font-normal text-gray-400">/100</span>
              </div>
            </div>
            <div className="p-3 rounded-lg bg-indigo-600 dark:bg-indigo-800 text-white text-center">
              <div className="text-xs text-indigo-200 mb-0.5">Meta Score</div>
              <div className="text-2xl font-serif font-bold">
                {metaScore !== null ? metaScore.toFixed(1) : "—"}
                <span className="text-sm font-normal text-indigo-300">/100</span>
              </div>
            </div>
          </div>
        </div>

        {/* External Rankings table */}
        {school.external_rankings && (
          <div className="mt-4">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              External Ranking Positions (2024)
            </h3>
            <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-gray-800">
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 dark:text-gray-400">Ranking</th>
                    <th className="px-4 py-2 text-center text-xs font-semibold text-gray-500 dark:text-gray-400">Rank</th>
                    <th className="px-4 py-2 text-center text-xs font-semibold text-gray-500 dark:text-gray-400">Normalized (0–100)</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 dark:text-gray-400">Source</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  <ExternalRankingRows
                    rankings={school.external_rankings}
                    normalizedScores={externalScoresNormalized}
                  />
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>

      {/* Courses */}
      {school.courses.length > 0 && (
        <section>
          <SectionHeader
            title="LegalTech & AI Courses"
            count={school.courses.length}
          />
          <div className="mt-4 space-y-2">
            {school.courses.map((course) => (
              <CourseRow key={course.id} course={course} />
            ))}
          </div>
        </section>
      )}

      {/* Programs */}
      {school.programs.length > 0 && (
        <section>
          <SectionHeader title="Programs, Centers & Joint Degrees" count={school.programs.length} />
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
            {school.programs.map((program) => (
              <ProgramCard key={program.id} program={program} />
            ))}
          </div>
        </section>
      )}

      {/* Faculty */}
      {school.faculty.length > 0 && (
        <section>
          <SectionHeader title="Tech-Expert Faculty" count={school.faculty.length} />
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
            {school.faculty.map((f, i) => (
              <FacultyCard key={i} faculty={f} />
            ))}
          </div>
        </section>
      )}

      {/* Partnerships */}
      {school.partnerships.length > 0 && (
        <section>
          <SectionHeader title="Industry & Institutional Partnerships" count={school.partnerships.length} />
          <div className="mt-4 space-y-2">
            {school.partnerships.map((p, i) => (
              <PartnershipRow key={i} partnership={p} />
            ))}
          </div>
        </section>
      )}

      {/* Student Orgs */}
      {school.student_orgs.length > 0 && (
        <section>
          <SectionHeader title="Student Organizations" count={school.student_orgs.length} />
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
            {school.student_orgs.map((org, i) => (
              <OrgCard key={i} org={org} />
            ))}
          </div>
        </section>
      )}

      {/* Contribute */}
      <section className="p-5 rounded-xl bg-brand-50 dark:bg-brand-950/30 border border-brand-200 dark:border-brand-800">
        <h3 className="font-serif font-semibold text-brand-900 dark:text-brand-200 mb-2">
          Is this record inaccurate or incomplete?
        </h3>
        <p className="text-sm text-brand-700 dark:text-brand-300 mb-4">
          All data comes from public sources. If you can provide better evidence,
          we want to hear from you. Corrections are merged via GitHub pull request.
        </p>
        <div className="flex flex-wrap gap-3">
          <a
            href={`https://github.com/your-org/tech-friendly-lawschool-ranking/issues/new?template=school-submission.md&title=[SCHOOL]+${encodeURIComponent(school.name)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors"
          >
            Submit a correction
          </a>
          <a
            href={`https://github.com/your-org/tech-friendly-lawschool-ranking/issues/new?template=press-release-gap.md&title=[PRG]+${encodeURIComponent(school.name)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm px-4 py-2 border border-red-300 dark:border-red-700 text-red-700 dark:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
          >
            Report a press release gap
          </a>
        </div>
      </section>
    </div>
  );
}

function SectionHeader({ title, count }: { title: string; count?: number }) {
  return (
    <div className="flex items-center gap-3 border-b border-gray-200 dark:border-gray-700 pb-3">
      <h2 className="font-serif text-xl font-semibold text-gray-900 dark:text-gray-100">
        {title}
      </h2>
      {count !== undefined && (
        <span className="text-sm text-gray-400 dark:text-gray-500">({count})</span>
      )}
    </div>
  );
}

function CourseRow({ course }: { course: Course }) {
  const typeColors = {
    required: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    elective: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
    certificate: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  };

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-600 transition-colors">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium text-gray-900 dark:text-gray-100 text-sm">
            {course.title}
          </span>
          <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${typeColors[course.type] ?? ""}`}>
            {course.type}
          </span>
          {course.year_verified === null && (
            <span className="text-xs text-amber-500 dark:text-amber-400 italic">unverified</span>
          )}
        </div>
        {course.topics.length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {course.topics.map((t) => (
              <span key={t} className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400">
                {t.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        )}
        {course.notes && (
          <p className="mt-1 text-xs text-gray-400 dark:text-gray-500 italic">{course.notes}</p>
        )}
      </div>
      <div className="flex-shrink-0 text-right">
        {course.credits && (
          <span className="text-xs text-gray-400 font-mono">{course.credits}cr</span>
        )}
        {course.source_url && (
          <div>
            <a
              href={course.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-brand-600 dark:text-brand-400 hover:underline"
            >
              source ↗
            </a>
          </div>
        )}
      </div>
    </div>
  );
}

function ProgramCard({ program }: { program: Program }) {
  const statusColors = {
    active: "text-green-600 dark:text-green-400",
    inactive: "text-red-600 dark:text-red-400",
    unknown: "text-gray-400 dark:text-gray-500",
  };

  return (
    <div className="p-4 rounded-lg bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h4 className="font-medium text-gray-900 dark:text-gray-100 text-sm leading-snug">
            {program.name}
          </h4>
          <div className="mt-1 flex items-center gap-2 flex-wrap">
            <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
              {program.type.replace(/_/g, " ")}
            </span>
            {program.tech_focus && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-brand-100 dark:bg-brand-900 text-brand-700 dark:text-brand-300">
                Tech focus
              </span>
            )}
            <span className={`text-xs ${statusColors[program.status] ?? statusColors.unknown}`}>
              ● {program.status}
            </span>
          </div>
        </div>
        {program.source_url && (
          <a
            href={program.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-brand-600 dark:text-brand-400 hover:underline flex-shrink-0"
          >
            ↗
          </a>
        )}
      </div>
      {program.description && (
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400 leading-relaxed line-clamp-3">
          {program.description}
        </p>
      )}
      {program.notes && (
        <p className="mt-2 text-xs text-amber-600 dark:text-amber-400 italic">{program.notes}</p>
      )}
    </div>
  );
}

function FacultyCard({ faculty }: { faculty: Faculty }) {
  return (
    <div className="p-4 rounded-lg bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h4 className="font-medium text-gray-900 dark:text-gray-100 text-sm">
            {faculty.profile_url ? (
              <a
                href={faculty.profile_url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-brand-600 dark:hover:text-brand-400 hover:underline"
              >
                {faculty.name} ↗
              </a>
            ) : faculty.name}
          </h4>
          {faculty.title && (
            <p className="text-xs text-gray-500 dark:text-gray-400">{faculty.title}</p>
          )}
        </div>
        {faculty.appointment_type && (
          <span className="text-xs text-gray-400 dark:text-gray-500 capitalize flex-shrink-0">
            {faculty.appointment_type.replace(/_/g, " ")}
          </span>
        )}
      </div>
      {faculty.tech_expertise.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {faculty.tech_expertise.slice(0, 4).map((e) => (
            <span key={e} className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
              {e.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function PartnershipRow({ partnership }: { partnership: Partnership }) {
  return (
    <div className="flex items-start gap-3 px-3 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
      <div className="flex-1">
        <span className="font-medium text-sm text-gray-800 dark:text-gray-200">
          {partnership.org}
        </span>
        {partnership.type && (
          <span className="ml-2 text-xs text-gray-400 dark:text-gray-500 capitalize">
            {partnership.type.replace(/_/g, " ")}
          </span>
        )}
        {partnership.description && (
          <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">{partnership.description}</p>
        )}
      </div>
      <div className="flex-shrink-0 flex items-center gap-2">
        {partnership.active === true && (
          <span className="text-xs text-green-600 dark:text-green-400">Active</span>
        )}
        {partnership.source_url && (
          <a
            href={partnership.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-brand-600 dark:text-brand-400 hover:underline"
          >
            source ↗
          </a>
        )}
      </div>
    </div>
  );
}

function ExternalRankingRows({
  rankings,
  normalizedScores,
}: {
  rankings: ExternalRankings;
  normalizedScores: Record<string, number | null>;
}) {
  const keys = Object.keys(EXTERNAL_RANKING_LABELS) as (keyof ExternalRankings)[];

  return (
    <>
      {keys.map((key) => {
        const entry = rankings[key];
        const normalized = normalizedScores[key] ?? null;
        const label = EXTERNAL_RANKING_LABELS[key];
        const sourceUrl = entry?.url ?? EXTERNAL_RANKING_URLS[key];

        return (
          <tr key={key} className={entry === null || entry.rank === null ? "opacity-40" : ""}>
            <td className="px-4 py-2 text-gray-800 dark:text-gray-200">
              <a
                href={sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-brand-600 dark:hover:text-brand-400 hover:underline"
              >
                {label} ↗
              </a>
            </td>
            <td className="px-4 py-2 text-center font-mono text-gray-700 dark:text-gray-300">
              {entry?.rank !== null && entry?.rank !== undefined ? `#${entry.rank}` : "—"}
            </td>
            <td className="px-4 py-2 text-center font-mono text-indigo-700 dark:text-indigo-300">
              {normalized !== null ? normalized.toFixed(1) : "—"}
            </td>
            <td className="px-4 py-2">
              {entry?.year ? (
                <span className="text-xs text-gray-400 dark:text-gray-500">{entry.year}</span>
              ) : null}
            </td>
          </tr>
        );
      })}
    </>
  );
}

function OrgCard({ org }: { org: StudentOrg }) {
  return (
    <div className="p-3 rounded-lg bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between gap-2">
        <h4 className="font-medium text-sm text-gray-900 dark:text-gray-100">
          {org.url ? (
            <a
              href={org.url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-brand-600 dark:hover:text-brand-400 hover:underline"
            >
              {org.name} ↗
            </a>
          ) : org.name}
        </h4>
        {org.active === true && (
          <span className="text-xs text-green-600 dark:text-green-400 flex-shrink-0">Active</span>
        )}
      </div>
      {org.focus && (
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{org.focus}</p>
      )}
    </div>
  );
}
