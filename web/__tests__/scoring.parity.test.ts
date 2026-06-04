/**
 * web/__tests__/scoring.parity.test.ts
 *
 * Cross-language parity tests: verifies that TypeScript scoring output
 * matches the Python-generated golden file in tests/golden/scores.json.
 *
 * If Python scoring changes and golden is regenerated with
 *   python scripts/regenerate_golden.py
 * this test will fail until the TypeScript scoring is updated to match.
 */

import { describe, expect, it } from 'vitest'
import { readFileSync } from 'fs'
import { resolve, join } from 'path'

import { computePracticalSkillsScore, computeScores } from '../lib/scoring'
import type { LawSchool } from '../lib/types'

// ---------------------------------------------------------------------------
// Load golden data and school JSON files at module level
// ---------------------------------------------------------------------------

const REPO_ROOT = resolve(__dirname, '..', '..')
const GOLDEN_PATH = join(REPO_ROOT, 'tests', 'golden', 'scores.json')
const SCHOOLS_DIR = join(REPO_ROOT, 'data', 'schools')

interface GoldenEntry {
  tech_total: number
  practical_total: number
  tier: string
  tech_subscores: Record<string, number>
  practical_breakdown: Record<string, number>
}

const golden: Record<string, GoldenEntry> = JSON.parse(
  readFileSync(GOLDEN_PATH, 'utf-8')
)

function loadSchool(schoolId: string): LawSchool {
  const path = join(SCHOOLS_DIR, `${schoolId}.json`)
  return JSON.parse(readFileSync(path, 'utf-8')) as LawSchool
}

// ---------------------------------------------------------------------------
// Parity tests
// ---------------------------------------------------------------------------

describe('TypeScript / Python scoring parity', () => {
  for (const [schoolId, expected] of Object.entries(golden)) {
    describe(schoolId, () => {
      it('tech_total matches golden (within 0.1)', () => {
        const school = loadSchool(schoolId)
        const result = computeScores(school)
        expect(Math.abs(result.scores.total! - expected.tech_total)).toBeLessThan(0.1)
      })

      it('practical_total matches golden (within 0.1)', () => {
        const school = loadSchool(schoolId)
        const result = computePracticalSkillsScore(school)
        expect(Math.abs(result.practical_skills_score - expected.practical_total)).toBeLessThan(0.1)
      })

      it('tier matches golden', () => {
        const school = loadSchool(schoolId)
        const result = computeScores(school)
        expect(result.ranking_tier).toBe(expected.tier)
      })

      it('tech subscores match golden', () => {
        const school = loadSchool(schoolId)
        const result = computeScores(school)
        for (const [key, goldenValue] of Object.entries(expected.tech_subscores)) {
          const actual = result.scores[key as keyof typeof result.scores]
          expect(
            Math.abs((actual as number) - goldenValue),
            `subscore ${key}: expected ${goldenValue}, got ${actual}`
          ).toBeLessThan(0.1)
        }
      })

      it('practical breakdown matches golden', () => {
        const school = loadSchool(schoolId)
        const result = computePracticalSkillsScore(school)
        for (const [key, goldenValue] of Object.entries(expected.practical_breakdown)) {
          const actual = result.breakdown[key as keyof typeof result.breakdown]
          expect(
            Math.abs((actual as number) - goldenValue),
            `practical ${key}: expected ${goldenValue}, got ${actual}`
          ).toBeLessThan(0.1)
        }
      })
    })
  }
})
