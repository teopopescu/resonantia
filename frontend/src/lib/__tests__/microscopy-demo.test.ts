import { describe, it, expect } from 'vitest'
import { CHANNELS, seedForWellFov, wellLabel } from '../microscopy-demo'

// generateCells is not exported, so we test the seeded random behavior
// indirectly via seedForWellFov and the exported utilities

describe('seedForWellFov', () => {
  it('produces deterministic seeds for the same inputs', () => {
    const seed1 = seedForWellFov(0, 1, 2, 3)
    const seed2 = seedForWellFov(0, 1, 2, 3)
    expect(seed1).toBe(seed2)
  })

  it('produces different seeds for different inputs', () => {
    const seed1 = seedForWellFov(0, 0, 0, 0)
    const seed2 = seedForWellFov(0, 0, 0, 1)
    const seed3 = seedForWellFov(1, 0, 0, 0)
    expect(seed1).not.toBe(seed2)
    expect(seed1).not.toBe(seed3)
  })
})

describe('wellLabel', () => {
  it('generates correct well labels', () => {
    expect(wellLabel(0, 1)).toBe('A1')
    expect(wellLabel(7, 12)).toBe('H12')
    expect(wellLabel(3, 6)).toBe('D6')
  })
})

describe('CHANNELS', () => {
  it('has 5 channel configurations', () => {
    expect(CHANNELS).toHaveLength(5)
  })

  it('each channel has required properties', () => {
    for (const ch of CHANNELS) {
      expect(ch).toHaveProperty('id')
      expect(ch).toHaveProperty('label')
      expect(ch).toHaveProperty('color')
      expect(ch).toHaveProperty('rgb')
      expect(ch.rgb).toHaveLength(3)
    }
  })

  it('includes dapi, gfp, mcherry, brightfield, and phase', () => {
    const ids = CHANNELS.map((c) => c.id)
    expect(ids).toContain('dapi')
    expect(ids).toContain('gfp')
    expect(ids).toContain('mcherry')
    expect(ids).toContain('brightfield')
    expect(ids).toContain('phase')
  })
})

// Test the seeded random determinism by verifying seed generation is consistent
describe('deterministic seed generation', () => {
  it('same plate/row/col/fov always yields the same seed', () => {
    const results = Array.from({ length: 10 }, () => seedForWellFov(2, 3, 5, 1))
    const allSame = results.every((r) => r === results[0])
    expect(allSame).toBe(true)
  })

  it('different fov values produce different seeds', () => {
    const seeds = new Set(
      Array.from({ length: 10 }, (_, i) => seedForWellFov(0, 0, 0, i))
    )
    expect(seeds.size).toBe(10)
  })
})
