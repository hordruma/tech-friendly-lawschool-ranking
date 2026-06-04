"use client";

import clsx from "clsx";
import type { PressReleaseGap } from "@/lib/types";

interface PressReleaseGapAlertProps {
  gaps: PressReleaseGap[];
  schoolName: string;
  compact?: boolean;
  className?: string;
}

const SEVERITY_LABELS: Record<string, string> = {
  minor: "Minor",
  moderate: "Moderate",
  major: "Major",
  egregious: "Egregious",
};

const SEVERITY_COLORS: Record<string, string> = {
  minor: "border-yellow-400 bg-yellow-50 dark:bg-yellow-950 dark:border-yellow-600",
  moderate: "border-orange-400 bg-orange-50 dark:bg-orange-950 dark:border-orange-600",
  major: "border-red-500 bg-red-50 dark:bg-red-950 dark:border-red-600",
  egregious: "border-red-700 bg-red-100 dark:bg-red-950 dark:border-red-700",
};

const BADGE_COLORS: Record<string, string> = {
  minor: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  moderate: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  major: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  egregious: "bg-red-200 text-red-900 dark:bg-red-900 dark:text-red-100",
};

export function PressReleaseGapAlert({
  gaps,
  schoolName,
  compact = false,
  className,
}: PressReleaseGapAlertProps) {
  if (gaps.length === 0) return null;

  // Compact mode: just show a count badge with a tooltip-style summary
  if (compact) {
    return (
      <span
        className={clsx(
          "inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-semibold",
          "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
          className
        )}
        title={`${gaps.length} press release gap${gaps.length !== 1 ? "s" : ""} documented`}
      >
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
            clipRule="evenodd"
          />
        </svg>
        {gaps.length} gap{gaps.length !== 1 ? "s" : ""}
      </span>
    );
  }

  const totalPenalty = gaps.reduce((sum, g) => sum + (g.penalty_points ?? -5), 0);

  return (
    <div className={clsx("space-y-4", className)}>
      {/* Header banner */}
      <div className="flex items-start gap-3 p-4 rounded-lg border-2 border-red-400 bg-red-50 dark:bg-red-950 dark:border-red-600">
        <svg
          className="w-5 h-5 mt-0.5 flex-shrink-0 text-red-600 dark:text-red-400"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
            clipRule="evenodd"
          />
        </svg>
        <div>
          <h3 className="font-semibold text-red-800 dark:text-red-200">
            Press Release Gap{gaps.length !== 1 ? "s" : ""} Documented — {schoolName}
          </h3>
          <p className="mt-1 text-sm text-red-700 dark:text-red-300">
            {gaps.length} gap{gaps.length !== 1 ? "s" : ""} documented between publicly marketed
            programs and current verified offerings.
            {totalPenalty < 0 && (
              <span className="ml-1 font-semibold">
                Score penalty: {totalPenalty} points.
              </span>
            )}
          </p>
          <p className="mt-1 text-xs text-red-600 dark:text-red-400">
            A Press Release Gap occurs when a school has publicly marketed a program that no
            longer exists or no longer functions as described.{" "}
            <a
              href="/methodology#press-release-gap"
              className="underline hover:no-underline"
            >
              Learn more about our methodology.
            </a>
          </p>
        </div>
      </div>

      {/* Individual gaps */}
      {gaps.map((gap, i) => {
        const sev = gap.severity ?? "minor";
        return (
          <div
            key={i}
            className={clsx(
              "rounded-lg border-l-4 p-4",
              SEVERITY_COLORS[sev] ?? SEVERITY_COLORS.minor
            )}
          >
            <div className="flex items-center gap-2 mb-2">
              <span
                className={clsx(
                  "text-xs font-semibold px-1.5 py-0.5 rounded",
                  BADGE_COLORS[sev] ?? BADGE_COLORS.minor
                )}
              >
                {SEVERITY_LABELS[sev] ?? "Unverified"}
              </span>
              {gap.year_claimed && (
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  Claimed: {gap.year_claimed}
                </span>
              )}
              {gap.penalty_points !== null && (
                <span className="text-xs font-mono text-red-600 dark:text-red-400 ml-auto">
                  {gap.penalty_points} pts
                </span>
              )}
            </div>

            <div className="space-y-2 text-sm">
              <div>
                <span className="font-semibold text-gray-800 dark:text-gray-200">
                  Claimed:{" "}
                </span>
                <span className="text-gray-700 dark:text-gray-300">{gap.claimed}</span>
                {gap.evidence_url && (
                  <a
                    href={gap.evidence_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-1 text-xs text-brand-600 dark:text-brand-400 underline hover:no-underline"
                  >
                    [source]
                  </a>
                )}
              </div>
              <div>
                <span className="font-semibold text-gray-800 dark:text-gray-200">
                  Current reality:{" "}
                </span>
                <span className="text-gray-700 dark:text-gray-300">{gap.reality}</span>
                {gap.current_url && (
                  <a
                    href={gap.current_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-1 text-xs text-brand-600 dark:text-brand-400 underline hover:no-underline"
                  >
                    [current]
                  </a>
                )}
              </div>
            </div>

            {gap.year_verified && (
              <p className="mt-2 text-xs text-gray-400 dark:text-gray-500">
                Verified {gap.year_verified}
              </p>
            )}
          </div>
        );
      })}

      {/* Report link */}
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Know about another gap at this school?{" "}
        <a
          href={`https://github.com/your-org/tech-friendly-lawschool-ranking/issues/new?template=press-release-gap.md&title=[PRG]+${encodeURIComponent(schoolName)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-brand-600 dark:text-brand-400 underline hover:no-underline"
        >
          Submit a report
        </a>
        .
      </p>
    </div>
  );
}
