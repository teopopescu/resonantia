import { describe, it, expect, beforeEach } from 'vitest'
import { useSampleStore } from '../sample-store'
import { DEMO_SAMPLES } from '@/lib/demo-data'
import type { Sample } from '@/lib/demo-data'

describe('useSampleStore', () => {
  beforeEach(() => {
    useSampleStore.setState({
      samples: [...DEMO_SAMPLES],
      filters: { type: 'all', status: 'all', location: '', search: '' },
      selectedSamples: [],
      modalOpen: false,
      editingSample: null,
      scannerMode: null,
    })
  })

  it('initial state can be reset with demo samples for demo-mode tests', () => {
    const state = useSampleStore.getState()
    expect(state.samples).toHaveLength(DEMO_SAMPLES.length)
    expect(state.samples[0].id).toBe(DEMO_SAMPLES[0].id)
  })

  it('addSample adds a sample to the beginning of the array', () => {
    const newSample: Sample = {
      id: 'test-1',
      name: 'Test Sample',
      barcode: 'RES-TEST-0001',
      type: 'buffer',
      location: 'Shelf-A',
      storageTemp: 'RT',
      lotNumber: 'TEST-001',
      expiryDate: '2025-12-31',
      quantity: 100,
      unit: 'mL',
      status: 'active',
      addedDate: '2025-01-01',
    }

    useSampleStore.getState().addSample(newSample)
    const state = useSampleStore.getState()
    expect(state.samples).toHaveLength(DEMO_SAMPLES.length + 1)
    expect(state.samples[0].id).toBe('test-1')
    expect(state.samples[0].name).toBe('Test Sample')
  })

  it('setFilters updates filter state', () => {
    useSampleStore.getState().setFilters({ type: 'antibody' })
    expect(useSampleStore.getState().filters.type).toBe('antibody')
    // Other filters remain unchanged
    expect(useSampleStore.getState().filters.status).toBe('all')
    expect(useSampleStore.getState().filters.search).toBe('')
  })

  it('setFilters can update multiple filters at once', () => {
    useSampleStore.getState().setFilters({ type: 'compound', status: 'expired' })
    const filters = useSampleStore.getState().filters
    expect(filters.type).toBe('compound')
    expect(filters.status).toBe('expired')
  })

  it('setFilters updates search filter', () => {
    useSampleStore.getState().setFilters({ search: 'GFP' })
    expect(useSampleStore.getState().filters.search).toBe('GFP')
  })
})
