"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import clsx from "clsx";
import type { SchoolSummary, RankingTier } from "@/lib/types";
import { ScoreBadge } from "./ScoreBadge";
import { PressReleaseGapAlert } from "./PressReleaseGapAlert";
import { getCountryName } from "@/lib/data";

interface RankingTableProps {
  schools: SchoolSummary[];
  countries: string[];
}

type SortKey = "meta_rank" | "rank" | "name" | "country" | "score" | "tier" | "prestige";
type SortDir = "asc" | "desc";

const TIER_ORDER: Record<string, number> = {
  S: 0, A: 1, B: 2, C: 3, D: 4, unranked: 5,
};

export function RankingTable({ schools, countries }: RankingTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("meta_rank");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [filterCountry, setFilterCountry] = useState<string>("");
  const [filterTier, setFilterTier] = useState<string>("");
  const [filterVerified, setFilterVerified] = useState<boolean>(false);
  const [search, setSearch] = useState<string>("");

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "name" || key === "country" ? "asc" : "asc");
    }
  };

  const filtered = useMemo(() => {
    return schools.filter((s) => {
      if (filterCountry && s.country !== filterCountry) return false;
      if (filterTier && (s.ranking_tier ?? "unranked") !== filterTier) return false;
      if (filterVerified && s.last_verified === null) return false;
      if (search) {
        const q = search.toLowerCase();
        if (!s.name.toLowerCase().includes(q) && !getCountryName(s.country).toLowerCase().includes(q)) {
          return false;
        }
      }
      return true;
    });
  }, [schools, filterCountry, filterTier, filterVerified, search]);

  const sorted = useMemo(() => {
    const data = [...filtered];
    data.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case "meta_rank":
          // Sort by meta_score descending; nulls last
          if (a.meta_score !== null && b.meta_score !== null) {
            cmp = b.meta_score - a.meta_score;
          } else if (a.meta_score !== null) {
            cmp = -1;
          } else if (b.meta_score !== null) {
            cmp = 1;
          }
          break;
        case "rank":
        case "score":
          cmp = (b.scores?.total ?? -1) - (a.scores?.total ?? -1);
          break;
        case "prestige":
          if (a.prestige_score !== null && b.prestige_score !== null) {
            cmp = b.prestige_score - a.prestige_score;
          } else if (a.prestige_score !== null) {
            cmp = -1;
          } else if (b.prestige_score !== null) {
            cmp = 1;
          }
          break;
        case "name":
          cmp = a.name.localeCompare(b.name);
          break;
        case "country":
          cmp = getCountryName(a.country).localeCompare(getCountryName(b.country));
          break;
        case "tier":
          cmp = (TIER_ORDER[a.ranking_tier ?? "unranked"] ?? 5) -
                (TIER_ORDER[b.ranking_tier ?? "unranked"] ?? 5);
          break;
      }
      return sortDir === "desc" ? -cmp : cmp;
    });
    return data;
  }, [filtered, sortKey, sortDir]);

  const SortIcon = ({ k }: { k: SortKey }) => {
    if (sortKey !== k) {
      return <span className="ml-1 text-gray-300 dark:text-gray-600">↕</span>;
    }
    return (
      <span className="ml-1 text-brand-500">
        {sortDir === "asc" ? "↑" : "↓"}
      </span>
    );
  };

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex flex-wrap gap-3 items-center">
        <input
          type="search"
          placeholder="Search schools…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 w-48"
        />

        <select
          value={filterCountry}
          onChange={(e) => setFilterCountry(e.target.value)}
          className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All countries</option>
          {countries.map((c) => (
            <option key={c} value={c}>
              {getCountryName(c)}
            </option>
          ))}
        </select>

        <select
          value={filterTier}
          onChange={(e) => setFilterTier(e.target.value)}
          className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All tiers</option>
          {["S", "A", "B", "C", "D", "unranked"].map((t) => (
            <option key={t} value={t}>
              Tier {t}
            </option>
          ))}
        </select>

        <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
          <input
            type="checkbox"
            checked={filterVerified}
            onChange={(e) => setFilterVerified(e.target.checked)}
            className="rounded border-gray-300 text-brand-500 focus:ring-brand-500"
          />
          Verified only
        </label>

        {/* Sort toggle */}
        <div className="flex items-center gap-1 ml-auto">
          <span className="text-xs text-gray-500 dark:text-gray-400 mr-1">Sort:</span>
          {(
            [
              { key: "meta_rank", label: "Meta Rank" },
              { key: "rank", label: "Tech Rank" },
              { key: "prestige", label: "Prestige" },
            ] as { key: SortKey; label: string }[]
          ).map(({ key, label }) => (
            <button
              key={key}
              onClick={() => handleSort(key)}
              className={clsx(
                "text-xs px-2 py-1 rounded-md font-medium transition-colors",
                sortKey === key
                  ? "bg-brand-600 text-white"
                  : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
              )}
            >
              {label}
            </button>
          ))}
        </div>

        <span className="text-xs text-gray-400 dark:text-gray-500">
          {sorted.length} school{sorted.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 dark:bg-gray-800 text-left">
              <th
                className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-900 dark:hover:text-gray-100 whitespace-nowrap"
                onClick={() => handleSort("meta_rank")}
              >
                Meta Rank <SortIcon k="meta_rank" />
              </th>
              <th
                className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-900 dark:hover:text-gray-100"
                onClick={() => handleSort("name")}
              >
                School <SortIcon k="name" />
              </th>
              <th
                className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-900 dark:hover:text-gray-100 whitespace-nowrap"
                onClick={() => handleSort("country")}
              >
                Country <SortIcon k="country" />
              </th>
              <th
                className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-900 dark:hover:text-gray-100 text-center"
                onClick={() => handleSort("tier")}
              >
                Tier <SortIcon k="tier" />
              </th>
              <th
                className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-900 dark:hover:text-gray-100 text-right whitespace-nowrap"
                onClick={() => handleSort("score")}
              >
                Tech Score <SortIcon k="score" />
              </th>
              <th
                className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-900 dark:hover:text-gray-100 text-right whitespace-nowrap"
                onClick={() => handleSort("prestige")}
              >
                Prestige <SortIcon k="prestige" />
              </th>
              <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400 text-center whitespace-nowrap">
                Features
              </th>
              <th className="px-4 py-3 font-semibold text-gray-600 dark:text-gray-400 text-center whitespace-nowrap">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {sorted.map((school, i) => (
              <TableRow key={school.id} school={school} rank={i + 1} />
            ))}
            {sorted.length === 0 && (
              <tr>
                <td
                  colSpan={8}
                  className="px-4 py-12 text-center text-gray-400 dark:text-gray-500"
                >
                  No schools match your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-gray-400 dark:text-gray-500">
        Scores marked{" "}
        <span className="italic">Unverified</span> are preliminary estimates
        computed from available data and have not been reviewed by a human editor.
        See{" "}
        <Link href="/methodology" className="underline hover:no-underline">
          methodology
        </Link>{" "}
        for scoring details.
      </p>
    </div>
  );
}

function TableRow({ school, rank }: { school: SchoolSummary; rank: number }) {
  return (
    <tr className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
      {/* Meta Rank */}
      <td className="px-4 py-3 text-center">
        {school.meta_score !== null ? (
          <div>
            <span className="font-mono text-xs text-gray-500 dark:text-gray-400">#{rank}</span>
            <div className="text-xs font-semibold text-brand-600 dark:text-brand-400">
              {school.meta_score.toFixed(0)}
            </div>
          </div>
        ) : (
          <span className="text-xs text-gray-300 dark:text-gray-600 italic">—</span>
        )}
      </td>
      <td className="px-4 py-3">
        <Link
          href={`/schools/${school.id}`}
          className="font-serif font-medium text-gray-900 dark:text-gray-100 hover:text-brand-600 dark:hover:text-brand-400 transition-colors"
        >
          {school.name}
        </Link>
        {school.press_release_gap_count > 0 && (
          <span className="ml-2 inline-flex items-center gap-0.5 text-xs text-red-600 dark:text-red-400 font-medium">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
                clipRule="evenodd"
              />
            </svg>
            {school.press_release_gap_count} gap{school.press_release_gap_count !== 1 ? "s" : ""}
          </span>
        )}
      </td>
      <td className="px-4 py-3 text-gray-500 dark:text-gray-400 whitespace-nowrap">
        {getCountryName(school.country)}
      </td>
      <td className="px-4 py-3 text-center">
        <ScoreBadge tier={school.ranking_tier} size="sm" />
      </td>
      {/* Tech Score */}
      <td className="px-4 py-3 text-right font-mono font-semibold text-gray-800 dark:text-gray-200">
        {school.scores?.total !== null && school.scores?.total !== undefined
          ? school.scores.total.toFixed(0)
          : "—"}
      </td>
      {/* Prestige Score */}
      <td className="px-4 py-3 text-right font-mono font-semibold text-indigo-700 dark:text-indigo-300">
        {school.prestige_score !== null && school.prestige_score !== undefined
          ? school.prestige_score.toFixed(0)
          : "—"}
      </td>
      <td className="px-4 py-3 text-center">
        <div className="flex items-center justify-center gap-1 flex-wrap">
          {school.has_legaltech_center && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-brand-100 text-brand-700 dark:bg-brand-900 dark:text-brand-300">
              Center
            </span>
          )}
          {school.has_joint_degree && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
              JD+
            </span>
          )}
          {school.course_count > 0 && (
            <span className="text-xs text-gray-400 dark:text-gray-500">
              {school.course_count}c
            </span>
          )}
        </div>
      </td>
      <td className="px-4 py-3 text-center">
        {school.last_verified ? (
          <span
            className="text-xs text-green-600 dark:text-green-400 font-medium"
            title={`Verified ${school.last_verified}`}
          >
            Verified
          </span>
        ) : (
          <span className="text-xs text-gray-400 dark:text-gray-500 italic">
            Unverified
          </span>
        )}
      </td>
    </tr>
  );
}
