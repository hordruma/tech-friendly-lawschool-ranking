import Link from "next/link";
import clsx from "clsx";
import type { SchoolSummary } from "@/lib/types";
import { ScoreBadge } from "./ScoreBadge";
import { PressReleaseGapAlert } from "./PressReleaseGapAlert";
import { getCountryName } from "@/lib/data";
import { getTierBorderColor } from "@/lib/scoring";

interface SchoolCardProps {
  school: SchoolSummary;
  rank?: number;
  className?: string;
}

export function SchoolCard({ school, rank, className }: SchoolCardProps) {
  const isVerified = school.last_verified !== null;
  const tier = school.ranking_tier ?? "unranked";

  return (
    <Link
      href={`/schools/${school.id}`}
      className={clsx(
        "block p-5 rounded-xl border-2 bg-white dark:bg-gray-900",
        "hover:shadow-md transition-shadow duration-150",
        "focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2",
        getTierBorderColor(school.ranking_tier),
        className
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          {/* Rank + name */}
          <div className="flex items-center gap-2">
            {rank !== undefined && (
              <span className="text-xs font-mono text-gray-400 dark:text-gray-500 flex-shrink-0">
                #{rank}
              </span>
            )}
            <h3 className="font-serif font-semibold text-gray-900 dark:text-gray-100 truncate text-lg leading-snug">
              {school.name}
            </h3>
          </div>

          {/* Country / jurisdiction */}
          <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
            {getCountryName(school.country)}
            {school.jurisdiction && `, ${school.jurisdiction}`}
          </p>
        </div>

        {/* Score badge */}
        <div className="flex-shrink-0">
          <ScoreBadge
            tier={school.ranking_tier}
            score={school.scores?.total}
            size="lg"
          />
        </div>
      </div>

      {/* Chips */}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {school.has_legaltech_center && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-brand-100 text-brand-800 dark:bg-brand-900 dark:text-brand-200">
            LegalTech Center
          </span>
        )}
        {school.has_joint_degree && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
            Joint Degree
          </span>
        )}
        {school.course_count > 0 && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
            {school.course_count} course{school.course_count !== 1 ? "s" : ""}
          </span>
        )}
        {!isVerified && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-500 italic">
            Unverified
          </span>
        )}
        {school.press_release_gap_count > 0 && (
          <PressReleaseGapAlert
            gaps={[]}
            schoolName={school.name}
            compact
          />
        )}
      </div>
    </Link>
  );
}
