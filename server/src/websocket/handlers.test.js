import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => {
  const mergeAnnotationArrays = (primary = [], alias = []) => {
    const merged = Array.isArray(primary) ? [...primary] : []
    const seenIds = new Set(merged.map(item => item?.id).filter(Boolean))

    ;(Array.isArray(alias) ? alias : []).forEach(item => {
      if (item?.id && seenIds.has(item.id)) return
      if (item?.id) seenIds.add(item.id)
      merged.push(item)
    })

    return merged
  }

  const normalizeSessionAnnotations = (annotations = {}) => {
    if (!annotations || typeof annotations !== 'object' || Array.isArray(annotations)) return {}
    const normalized = { ...annotations }
    if (Array.isArray(normalized.measures)) {
      normalized.angles = mergeAnnotationArrays(normalized.angles, normalized.measures)
      delete normalized.measures
    }
    return normalized
  }

  return {
    broadcasts: [],
    storedAnnotations: {},
    normalizeSessionAnnotations,
    sessionService: {
      getById: vi.fn(async () => ({ annotations: mocks.storedAnnotations })),
      updateAnnotations: vi.fn(async (_sessionId, annotations) => {
        mocks.storedAnnotations = normalizeSessionAnnotations(annotations)
        return { annotations: mocks.storedAnnotations }
      })
    },
    presenceService: {
      broadcastAll: vi.fn((sessionId, message) => {
        mocks.broadcasts.push({ sessionId, message })
      })
    }
  }
})

vi.mock('../services/SessionService.js', () => ({
  sessionService: mocks.sessionService,
  normalizeSessionAnnotations: mocks.normalizeSessionAnnotations
}))

vi.mock('../services/PresenceService.js', () => ({
  presenceService: mocks.presenceService
}))

const { handleMessage } = await import('./handlers.js')

const context = {
  sessionId: '11111111-1111-4111-8111-111111111111',
  participantId: '22222222-2222-4222-8222-222222222222'
}

function makeSocket() {
  return {
    sent: [],
    send(message) {
      this.sent.push(JSON.parse(message))
    }
  }
}

describe('collaboration websocket handlers', () => {
  beforeEach(() => {
    mocks.broadcasts = []
    mocks.storedAnnotations = {}
    vi.clearAllMocks()
  })

  it('canonicalizes angle additions from measures to angles', async () => {
    await handleMessage(
      makeSocket(),
      JSON.stringify({
        type: 'annotation:add',
        payload: {
          annotationType: 'measures',
          annotation: {
            id: 'angle-1',
            pageIndex: 0,
            label: 'T',
            points: [{ x: 1, y: 1 }, { x: 2, y: 2 }, { x: 3, y: 1 }]
          }
        }
      }),
      { ...context }
    )

    expect(mocks.storedAnnotations.measures).toBeUndefined()
    expect(mocks.storedAnnotations.angles).toHaveLength(1)
    expect(mocks.storedAnnotations.angles[0].label).toBe('T')
    expect(mocks.broadcasts.at(-1).message).toMatchObject({
      type: 'annotation:sync',
      payload: {
        action: 'add',
        annotationType: 'angles',
        participantId: context.participantId
      }
    })
  })

  it('shares distance additions as distance annotations', async () => {
    await handleMessage(
      makeSocket(),
      JSON.stringify({
        type: 'annotation:add',
        payload: {
          annotationType: 'distances',
          annotation: {
            id: 'distance-1',
            pageIndex: 0,
            type: 'distance',
            label: 'stroke thickness',
            points: [{ x: 10, y: 10 }, { x: 25, y: 14 }],
            lengthPx: 15.52
          }
        }
      }),
      { ...context }
    )

    expect(mocks.storedAnnotations.distances).toHaveLength(1)
    expect(mocks.storedAnnotations.distances[0].label).toBe('stroke thickness')
    expect(mocks.broadcasts.at(-1).message).toMatchObject({
      type: 'annotation:sync',
      payload: {
        action: 'add',
        annotationType: 'distances',
        participantId: context.participantId
      }
    })
  })

  it('broadcasts shared settings without replacing annotation rows', async () => {
    mocks.storedAnnotations = {
      angles: [{ id: 'angle-1', pageIndex: 0, label: 'T' }],
      settings: { angleLabels: ['T'] }
    }

    await handleMessage(
      makeSocket(),
      JSON.stringify({
        type: 'settings:update',
        payload: {
          settings: {
            angleLabels: ['T', 'U'],
            angleLabelPositions: { 'angle-1': { x: 10, y: 20 } },
            labelPositions: { band1: { x: 5, y: 6 } },
            measurementScalesByPage: [{ source: 'user', pixelsPerCmX: 12, pixelsPerCmY: 13 }],
            imageFiltersByPage: { 0: { brightness: 10 } },
            showMeasurementsInCm: true
          }
        }
      }),
      { ...context }
    )

    expect(mocks.storedAnnotations.angles).toEqual([{ id: 'angle-1', pageIndex: 0, label: 'T' }])
    expect(mocks.storedAnnotations.settings).toMatchObject({
      angleLabels: ['T', 'U'],
      angleLabelPositions: { 'angle-1': { x: 10, y: 20 } },
      labelPositions: { band1: { x: 5, y: 6 } },
      measurementScalesByPage: [{ source: 'user', pixelsPerCmX: 12, pixelsPerCmY: 13 }],
      imageFiltersByPage: { 0: { brightness: 10 } },
      showMeasurementsInCm: true
    })
    expect(mocks.broadcasts.at(-1).message).toMatchObject({
      type: 'settings:sync',
      payload: {
        participantId: context.participantId,
        settings: {
          angleLabels: ['T', 'U'],
          showMeasurementsInCm: true
        }
      }
    })
  })
})
