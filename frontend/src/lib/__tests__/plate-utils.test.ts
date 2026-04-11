import { describe, it, expect } from 'vitest'
import {
  generateWellLabels,
  wellToCoords,
  coordsToWell,
  generateCherryPickMapping,
  generateSerialDilution,
  wellColor,
} from '../plate-utils'

describe('generateWellLabels', () => {
  it('generates correct labels for a 96-well plate (8x12)', () => {
    const labels = generateWellLabels(8, 12)
    expect(labels).toHaveLength(96)
    expect(labels[0]).toBe('A1')
    expect(labels[1]).toBe('A2')
    expect(labels[11]).toBe('A12')
    expect(labels[12]).toBe('B1')
    expect(labels[95]).toBe('H12')
  })

  it('generates correct labels for a 384-well plate (16x24)', () => {
    const labels = generateWellLabels(16, 24)
    expect(labels).toHaveLength(384)
    expect(labels[0]).toBe('A1')
    expect(labels[23]).toBe('A24')
    expect(labels[24]).toBe('B1')
    expect(labels[383]).toBe('P24')
  })
})

describe('wellToCoords', () => {
  it('converts A1 to {row: 0, col: 0}', () => {
    expect(wellToCoords('A1')).toEqual({ row: 0, col: 0 })
  })

  it('converts H12 to {row: 7, col: 11}', () => {
    expect(wellToCoords('H12')).toEqual({ row: 7, col: 11 })
  })

  it('converts B3 to {row: 1, col: 2}', () => {
    expect(wellToCoords('B3')).toEqual({ row: 1, col: 2 })
  })

  it('converts P24 to {row: 15, col: 23}', () => {
    expect(wellToCoords('P24')).toEqual({ row: 15, col: 23 })
  })

  it('throws on invalid well label', () => {
    expect(() => wellToCoords('Z1')).toThrow('Invalid well label')
    expect(() => wellToCoords('')).toThrow('Invalid well label')
  })
})

describe('coordsToWell', () => {
  it('converts (0, 0) to A1', () => {
    expect(coordsToWell(0, 0)).toBe('A1')
  })

  it('converts (7, 11) to H12', () => {
    expect(coordsToWell(7, 11)).toBe('H12')
  })

  it('converts (1, 2) to B3', () => {
    expect(coordsToWell(1, 2)).toBe('B3')
  })

  it('is the inverse of wellToCoords', () => {
    const wells = ['A1', 'C5', 'H12', 'D7']
    for (const well of wells) {
      const coords = wellToCoords(well)
      expect(coordsToWell(coords.row, coords.col)).toBe(well)
    }
  })
})

describe('generateCherryPickMapping', () => {
  it('creates correct source to dest mappings starting at A1', () => {
    const sources = ['C3', 'D5', 'E7']
    const mappings = generateCherryPickMapping(sources, 'A1')
    expect(mappings).toHaveLength(3)
    expect(mappings[0]).toEqual({ sourceWell: 'C3', destWell: 'A1' })
    expect(mappings[1]).toEqual({ sourceWell: 'D5', destWell: 'A2' })
    expect(mappings[2]).toEqual({ sourceWell: 'E7', destWell: 'A3' })
  })

  it('wraps to the next row when reaching end of columns', () => {
    const sources = ['A1', 'A2', 'A3']
    const mappings = generateCherryPickMapping(sources, 'A11')
    expect(mappings).toHaveLength(3)
    expect(mappings[0]).toEqual({ sourceWell: 'A1', destWell: 'A11' })
    expect(mappings[1]).toEqual({ sourceWell: 'A2', destWell: 'A12' })
    expect(mappings[2]).toEqual({ sourceWell: 'A3', destWell: 'B1' })
  })

  it('stops when exceeding plate rows', () => {
    // Start near the end of a 96-well plate (col < 12 means 96-well config, 8 rows)
    const sources = Array.from({ length: 20 }, (_, i) => `A${i + 1}`)
    const mappings = generateCherryPickMapping(sources, 'H10')
    // From H10 we can fit H10, H11, H12 = 3 wells before exceeding rows
    expect(mappings.length).toBeLessThanOrEqual(3)
  })
})

describe('generateSerialDilution', () => {
  it('generates correct horizontal dilution series', () => {
    const result = generateSerialDilution('A1', 'horizontal', 4, 2)
    expect(result).toHaveLength(4)
    expect(result[0]).toEqual({ well: 'A1', dilution: 1 })
    expect(result[1]).toEqual({ well: 'A2', dilution: 0.5 })
    expect(result[2]).toEqual({ well: 'A3', dilution: 0.25 })
    expect(result[3]).toEqual({ well: 'A4', dilution: 0.125 })
  })

  it('generates correct vertical dilution series', () => {
    const result = generateSerialDilution('A1', 'vertical', 3, 10)
    expect(result).toHaveLength(3)
    expect(result[0]).toEqual({ well: 'A1', dilution: 1 })
    expect(result[1]).toEqual({ well: 'B1', dilution: 0.1 })
    expect(result[2].dilution).toBeCloseTo(0.01)
    expect(result[2].well).toBe('C1')
  })

  it('stops at plate boundary', () => {
    const result = generateSerialDilution('P1', 'vertical', 5, 2)
    // P is row 15, max row is 15, so only 1 step fits
    expect(result).toHaveLength(1)
    expect(result[0].well).toBe('P1')
  })
})

describe('wellColor', () => {
  it('returns correct hex for sample', () => {
    expect(wellColor('sample')).toBe('#5B8FB9')
  })

  it('returns correct hex for control-positive', () => {
    expect(wellColor('control-positive')).toBe('#6BAF6B')
  })

  it('returns correct hex for control-negative', () => {
    expect(wellColor('control-negative')).toBe('#C45B5B')
  })

  it('returns correct hex for compound', () => {
    expect(wellColor('compound')).toBe('#8B6BAF')
  })

  it('returns correct hex for empty', () => {
    expect(wellColor('empty')).toBe('#E8E4DF')
  })
})
