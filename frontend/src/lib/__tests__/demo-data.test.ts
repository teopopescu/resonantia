import { describe, it, expect } from 'vitest'
import { DEMO_SAMPLES } from '../demo-data'
import type { SampleType } from '../demo-data'

describe('DEMO_SAMPLES', () => {
  it('has entries with all required fields', () => {
    expect(DEMO_SAMPLES.length).toBeGreaterThan(0)
    for (const sample of DEMO_SAMPLES) {
      expect(sample).toHaveProperty('id')
      expect(sample).toHaveProperty('name')
      expect(sample).toHaveProperty('barcode')
      expect(sample).toHaveProperty('type')
      expect(sample).toHaveProperty('location')
      expect(sample).toHaveProperty('storageTemp')
      expect(sample).toHaveProperty('lotNumber')
      expect(sample).toHaveProperty('expiryDate')
      expect(sample).toHaveProperty('quantity')
      expect(sample).toHaveProperty('unit')
      expect(sample).toHaveProperty('status')
      expect(sample).toHaveProperty('addedDate')
    }
  })

  it('has all unique barcodes', () => {
    const barcodes = DEMO_SAMPLES.map((s) => s.barcode)
    const uniqueBarcodes = new Set(barcodes)
    expect(uniqueBarcodes.size).toBe(barcodes.length)
  })

  it('has some samples that are expiring (within 30 days)', () => {
    const expiringSamples = DEMO_SAMPLES.filter((s) => s.status === 'expiring')
    expect(expiringSamples.length).toBeGreaterThan(0)

    const thirtyDaysFromNow = new Date()
    thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30)

    for (const sample of expiringSamples) {
      const expiryDate = new Date(sample.expiryDate)
      expect(expiryDate.getTime()).toBeLessThanOrEqual(thirtyDaysFromNow.getTime())
    }
  })

  it('has some samples that are low stock', () => {
    const lowStockSamples = DEMO_SAMPLES.filter((s) => s.status === 'low_stock')
    expect(lowStockSamples.length).toBeGreaterThan(0)
  })

  it('includes antibody, cell_line, compound, media, and buffer types', () => {
    const requiredTypes: SampleType[] = ['antibody', 'cell_line', 'compound', 'media', 'buffer']
    const presentTypes = new Set(DEMO_SAMPLES.map((s) => s.type))

    for (const t of requiredTypes) {
      expect(presentTypes.has(t)).toBe(true)
    }
  })
})
