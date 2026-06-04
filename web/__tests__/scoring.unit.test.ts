/**
 * web/__tests__/scoring.unit.test.ts
 *
 * Unit tests for pure scoring functions in web/lib/scoring.ts.
 * No React, no server — pure function tests.
 */

import { describe, expect, it } from 'vitest'

import {
  computeMetaScore,
  normalizeRank,
  scoreCurriculumCourses,
  scoreJointDegrees,
  scorePracticalRequirement,
  scorePressReleasePenalty,
} from '../lib/scoring'
import type { LawSchool } from '../lib/types'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeSchool(overrides: Partial<LawSchool> = {}): LawSchool {
  return {
    id: 'test',
    name: 'Test School',
    country: 'US',
    jurisdiction: null,
    url: 'https://example.com',
    last_researched: null,
    last_verified: null,
    accreditation: [],
    courses: [],
    programs: [],
    faculty: [],
    partnerships: [],
    student_orgs: [],
    press_release_gap: [],
    external_rankings: null,
    practical_skills_score: null,
    practical_skills_breakdown: null,
    meta_score: null,
    meta_rank: null,
    scores: null,
    ranking_tier: null,
    notes: null,
    ...overrides,
  }
}

// ---------------------------------------------------------------------------
// scoreCurriculumCourses
// ---------------------------------------------------------------------------

describe('scoreCurriculumCourses', () => {
  it('returns 0 for empty courses', () => {
    const [score] = scoreCurriculumCourses(makeSchool())
    expect(score).toBe(0)
  })

  it('gives 1 pt per elective', () => {
    const school = makeSchool({
      courses: [
        { id: 'c1', title: 'Tech Law', credits: 3, type: 'elective', topics: [], source_url: null, year_verified: 2024, notes: null },
      ],
    })
    const [score] = scoreCurriculumCourses(school)
    expect(score).toBe(1)
  })

  it('gives 2 pts per required course', () => {
    const school = makeSchool({
      courses: [
        { id: 'c1', title: 'AI Law', credits: 3, type: 'required', topics: [], source_url: null, year_verified: 2024, notes: null },
      ],
    })
    const [score] = scoreCurriculumCourses(school)
    expect(score).toBe(2)
  })

  it('gives 1 pt per certificate course', () => {
    const school = makeSchool({
      courses: [
        { id: 'c1', title: 'Data Law', credits: 2, type: 'certificate', topics: [], source_url: null, year_verified: 2024, notes: null },
      ],
    })
    const [score] = scoreCurriculumCourses(school)
    expect(score).toBe(1)
  })

  it('caps score at 20', () => {
    const courses = Array.from({ length: 15 }, (_, i) => ({
      id: `c${i}`,
      title: `Course ${i}`,
      credits: 3,
      type: 'required' as const,
      topics: [],
      source_url: null,
      year_verified: 2024,
      notes: null,
    }))
    const school = makeSchool({ courses })
    const [score] = scoreCurriculumCourses(school)
    expect(score).toBe(20)
  })

  it('does not count courses with year_verified=null', () => {
    const school = makeSchool({
      courses: [
        { id: 'c1', title: 'Unverified', credits: 3, type: 'required', topics: [], source_url: null, year_verified: null, notes: null },
        { id: 'c2', title: 'Verified', credits: 3, type: 'elective', topics: [], source_url: null, year_verified: 2024, notes: null },
      ],
    })
    const [score, notes] = scoreCurriculumCourses(school)
    expect(score).toBe(1) // only verified elective counts
    expect(notes.some(n => n.includes('UNVERIFIED'))).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// scorePracticalRequirement
// ---------------------------------------------------------------------------

describe('scorePracticalRequirement', () => {
  it('returns 10 for required tech course', () => {
    const school = makeSchool({
      courses: [
        { id: 'c1', title: 'Tech Law', credits: 3, type: 'required', topics: [], source_url: null, year_verified: 2024, notes: null },
      ],
    })
    const [score] = scorePracticalRequirement(school)
    expect(score).toBe(10)
  })

  it('returns 7 for tech clinic', () => {
    const school = makeSchool({
      programs: [
        { id: 'p1', name: 'Tech Clinic', type: 'clinic', description: null, tech_focus: true, practical_focus: null, source_url: null, year_verified: null, status: 'active', notes: null },
      ],
    })
    const [score] = scorePracticalRequirement(school)
    expect(score).toBe(7)
  })

  it('returns 4 for any active clinic (no tech focus)', () => {
    const school = makeSchool({
      programs: [
        { id: 'p1', name: 'General Clinic', type: 'clinic', description: null, tech_focus: false, practical_focus: null, source_url: null, year_verified: null, status: 'active', notes: null },
      ],
    })
    const [score] = scorePracticalRequirement(school)
    expect(score).toBe(4)
  })

  it('returns 0 when nothing present', () => {
    const [score] = scorePracticalRequirement(makeSchool())
    expect(score).toBe(0)
  })
})

// ---------------------------------------------------------------------------
// scoreJointDegrees
// ---------------------------------------------------------------------------

describe('scoreJointDegrees', () => {
  it('gives 5 pts for a qualifying joint degree', () => {
    const school = makeSchool({
      programs: [
        { id: 'p1', name: 'JD/MS Computer Science', type: 'joint_degree', description: null, tech_focus: true, practical_focus: null, source_url: null, year_verified: null, status: 'active', notes: null },
      ],
    })
    const [score] = scoreJointDegrees(school)
    expect(score).toBe(5)
  })

  it('caps at 10 for multiple qualifying joint degrees', () => {
    const programs = Array.from({ length: 4 }, (_, i) => ({
      id: `p${i}`,
      name: 'JD/Tech Degree',
      type: 'joint_degree' as const,
      description: null,
      tech_focus: true,
      practical_focus: null,
      source_url: null,
      year_verified: null,
      status: 'active' as const,
      notes: null,
    }))
    const school = makeSchool({ programs })
    const [score] = scoreJointDegrees(school)
    expect(score).toBe(10)
  })

  it('detects keywords like "data science"', () => {
    const school = makeSchool({
      programs: [
        { id: 'p1', name: 'JD/MS Data Science', type: 'joint_degree', description: null, tech_focus: false, practical_focus: null, source_url: null, year_verified: null, status: 'active', notes: null },
      ],
    })
    const [score] = scoreJointDegrees(school)
    expect(score).toBe(5)
  })

  it('returns 0 for non-tech joint degree (JD/MBA)', () => {
    const school = makeSchool({
      programs: [
        { id: 'p1', name: 'JD/MBA', type: 'joint_degree', description: 'Business joint degree', tech_focus: false, practical_focus: null, source_url: null, year_verified: null, status: 'active', notes: null },
      ],
    })
    const [score] = scoreJointDegrees(school)
    expect(score).toBe(0)
  })
})

// ---------------------------------------------------------------------------
// scorePressReleasePenalty
// ---------------------------------------------------------------------------

describe('scorePressReleasePenalty', () => {
  it('returns 0 for empty gaps', () => {
    const [score] = scorePressReleasePenalty(makeSchool())
    expect(score).toBe(0)
  })

  it('returns negative for gaps', () => {
    const school = makeSchool({
      press_release_gap: [
        { claimed: 'Great programs', reality: 'Not so great', evidence_url: null, current_url: null, year_claimed: null, year_verified: null, severity: 'minor', penalty_points: null },
      ],
    })
    const [score] = scorePressReleasePenalty(school)
    expect(score).toBe(-5)
  })

  it('uses penalty_points when provided', () => {
    const school = makeSchool({
      press_release_gap: [
        { claimed: 'Claim', reality: 'Reality', evidence_url: null, current_url: null, year_claimed: null, year_verified: null, severity: 'major', penalty_points: -15 },
      ],
    })
    const [score] = scorePressReleasePenalty(school)
    expect(score).toBe(-15)
  })

  it('caps penalty at -20', () => {
    const gaps = Array.from({ length: 5 }, (_, i) => ({
      claimed: `Claim ${i}`,
      reality: 'Reality',
      evidence_url: null,
      current_url: null,
      year_claimed: null,
      year_verified: null,
      severity: 'major' as const,
      penalty_points: null as null,
    }))
    const school = makeSchool({ press_release_gap: gaps })
    const [score] = scorePressReleasePenalty(school)
    expect(score).toBe(-20)
  })
})

// ---------------------------------------------------------------------------
// normalizeRank
// ---------------------------------------------------------------------------

describe('normalizeRank', () => {
  it('rank 1 is near 100', () => {
    expect(normalizeRank(1)).toBeGreaterThan(95)
  })

  it('rank 500 is near 0 (< 1)', () => {
    // log-scale formula: 100*(1 - log(500)/log(501)) ≈ 0.032
    expect(normalizeRank(500)).toBeLessThan(1)
  })

  it('rank > 500 returns 0', () => {
    expect(normalizeRank(501)).toBe(0)
    expect(normalizeRank(9999)).toBe(0)
  })

  it('is monotonically decreasing', () => {
    const ranks = [1, 5, 10, 50, 100, 250, 499, 500]
    const scores = ranks.map(normalizeRank)
    for (let i = 0; i < scores.length - 1; i++) {
      expect(scores[i]).toBeGreaterThan(scores[i + 1])
    }
  })
})

// ---------------------------------------------------------------------------
// computeMetaScore
// ---------------------------------------------------------------------------

describe('computeMetaScore', () => {
  it('returns null meta_score when no external rankings', () => {
    const school = makeSchool({ external_rankings: null })
    const result = computeMetaScore(school)
    expect(result.meta_score).toBeNull()
    expect(result.prestige_score).toBeNull()
  })

  it('returns null when all ranking ranks are null', () => {
    const school = makeSchool({
      external_rankings: {
        qs_law: { rank: null, year: 2024, url: null },
        the_law: null,
        arwu_law: null,
        usnews_law: null,
        usnews_global_law: null,
        vault_law: null,
      },
    })
    const result = computeMetaScore(school)
    expect(result.meta_score).toBeNull()
  })

  it('applies 50/30/20 formula when practical_skills_score is set', () => {
    const techTotal = 60
    const practical = 40
    const school = makeSchool({
      scores: {
        curriculum_courses: 0, curriculum_practical: 0, curriculum_clinics: 0,
        infrastructure_center: 10, infrastructure_joint_degrees: 5, infrastructure_partnerships: 10,
        faculty_expertise: 10, faculty_research: 7, community_orgs: 5, community_careers: 3,
        press_release_gap_penalty: 0, total: techTotal,
      },
      practical_skills_score: practical,
      external_rankings: {
        qs_law: { rank: 1, year: 2024, url: null },
        the_law: null,
        arwu_law: null,
        usnews_law: null,
        usnews_global_law: null,
        vault_law: null,
      },
    })
    const result = computeMetaScore(school)
    const prestige = normalizeRank(1)
    const expected = Math.round((techTotal * 0.50 + practical * 0.30 + prestige * 0.20) * 100) / 100
    expect(result.meta_score).not.toBeNull()
    expect(Math.abs(result.meta_score! - expected)).toBeLessThan(0.1)
  })

  it('uses 50/30/20 formula when practical_skills_score is stored (non-null)', () => {
    // The TS computeMetaScore always resolves practical (either stored or computed),
    // so the 62.5/37.5 null fallback is only relevant in the Python backend.
    // Here we verify that when practical_skills_score IS set, the formula applies correctly.
    const techTotal = 45
    const practical = 20
    const school = makeSchool({
      scores: {
        curriculum_courses: 0, curriculum_practical: 0, curriculum_clinics: 0,
        infrastructure_center: 10, infrastructure_joint_degrees: 0, infrastructure_partnerships: 10,
        faculty_expertise: 10, faculty_research: 7, community_orgs: 5, community_careers: 3,
        press_release_gap_penalty: 0, total: techTotal,
      },
      practical_skills_score: practical,
      external_rankings: {
        qs_law: { rank: 10, year: 2024, url: null },
        the_law: null,
        arwu_law: null,
        usnews_law: null,
        usnews_global_law: null,
        vault_law: null,
      },
    })
    const result = computeMetaScore(school)
    const prestige = normalizeRank(10)
    const expected = Math.round((techTotal * 0.50 + practical * 0.30 + prestige * 0.20) * 100) / 100
    expect(result.meta_score).not.toBeNull()
    expect(Math.abs(result.meta_score! - expected)).toBeLessThan(0.1)
  })
})
