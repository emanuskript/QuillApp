import { describe, expect, it, vi } from 'vitest'

vi.mock('../lib/prisma.js', () => ({
  prisma: {}
}))

const { normalizeSessionAnnotations } = await import('./SessionService.js')

describe('normalizeSessionAnnotations', () => {
  it('stores legacy measure annotations under the canonical angles key', () => {
    const normalized = normalizeSessionAnnotations({
      highlights: [{ id: 'h1' }],
      angles: [{ id: 'a1', label: 'T' }],
      measures: [
        { id: 'a1', label: 'duplicate T' },
        { id: 'a2', label: 'U' }
      ],
      settings: {
        angleLabels: ['T', 'U']
      }
    })

    expect(normalized.measures).toBeUndefined()
    expect(normalized.angles).toEqual([
      { id: 'a1', label: 'T' },
      { id: 'a2', label: 'U' }
    ])
    expect(normalized.settings.angleLabels).toEqual(['T', 'U'])
  })
})
