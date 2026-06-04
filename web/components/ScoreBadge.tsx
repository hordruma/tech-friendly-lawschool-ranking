"use client";

import clsx from "clsx";
import type { RankingTier } from "@/lib/types";
import { getTierColor, TIER_LABELS } from "@/lib/scoring";

interface ScoreBadgeProps {
  tier: RankingTier;
  score?: number | null;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  className?: string;
}

export function ScoreBadge({
  tier,
  score,
  size = "md",
  showLabel = false,
  className,
}: ScoreBadgeProps) {
  const t = tier ?? "unranked";

  const sizeClasses = {
    sm: "text-xs px-1.5 py-0.5 font-semibold",
    md: "text-sm px-2 py-1 font-bold",
    lg: "text-base px-3 py-1.5 font-bold",
  };

  const tierChar = t === "unranked" ? "?" : t;
  const label = showLabel ? TIER_LABELS[t] : tierChar;

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded font-mono",
        sizeClasses[size],
        getTierColor(tier),
        className
      )}
      title={TIER_LABELS[t]}
    >
      <span>{label}</span>
      {score !== undefined && score !== null && (
        <span className="opacity-70 font-normal">
          {score.toFixed(0)}
          <span className="text-xs opacity-60">/100</span>
        </span>
      )}
    </span>
  );
}

interface ScoreBarProps {
  score: number | null;
  max: number;
  label?: string;
  className?: string;
  color?: string;
}

export function ScoreBar({ score, max, label, className, color }: ScoreBarProps) {
  const pct = score !== null && max > 0 ? Math.max(0, Math.min(100, (score / max) * 100)) : 0;
  const isNegative = (score ?? 0) < 0;

  return (
    <div className={clsx("space-y-1", className)}>
      {label && (
        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>{label}</span>
          <span className={clsx("font-mono font-medium", isNegative ? "text-red-600 dark:text-red-400" : "text-gray-700 dark:text-gray-300")}>
            {score !== null ? (isNegative ? score.toFixed(0) : `${score.toFixed(0)}/${max}`) : "—"}
          </span>
        </div>
      )}
      <div className="h-1.5 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={clsx(
            "h-full rounded-full transition-all duration-500",
            color ?? (isNegative ? "bg-red-500" : "bg-brand-500")
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
