import test from 'node:test'
import assert from 'node:assert/strict'

import {
  PDF_EXPORT_SCOPE,
  formatPageCount,
  pageHasExportableAnnotations,
  selectPdfExportPages,
} from './pdfExportUtils.mjs'

test('annotated scope returns only annotated pages in document order', () => {
  const pages = selectPdfExportPages(
    6,
    {
      annotationsByPage: [[], [{ type: 'highlight' }], [], [], [], [{ type: 'trace' }]],
      commentsByPage: [[], [], [], [{ text: 'note' }]],
      lengthMeasurements: {},
    },
    PDF_EXPORT_SCOPE.ANNOTATED
  )

  assert.deepEqual(pages, [1, 3, 5])
})

test('length bands count as annotations even though they use a separate store', () => {
  const state = {
    annotationsByPage: [],
    commentsByPage: [],
    lengthMeasurements: {
      ascenders: { 2: [{ width: 100, height: 20 }] },
      internalMargin: {},
    },
  }

  assert.equal(pageHasExportableAnnotations(2, state), true)
  assert.deepEqual(selectPdfExportPages(4, state), [2])
})

test('empty, sparse, null, and malformed stores are handled safely', () => {
  const state = {
    annotationsByPage: [null, [null], 'invalid'],
    commentsByPage: undefined,
    lengthMeasurements: {
      malformed: null,
      empty: { 1: [] },
    },
  }

  assert.deepEqual(selectPdfExportPages(5, state), [])
  assert.equal(pageHasExportableAnnotations(-1, state), false)
  assert.equal(pageHasExportableAnnotations(1.5, state), false)
})

test('all scope includes every document page regardless of annotation state', () => {
  assert.deepEqual(
    selectPdfExportPages(4, {}, PDF_EXPORT_SCOPE.ALL),
    [0, 1, 2, 3]
  )
})

test('page count is normalized and unsupported scopes are rejected', () => {
  assert.deepEqual(selectPdfExportPages(2.9, {}, PDF_EXPORT_SCOPE.ALL), [0, 1])
  assert.deepEqual(selectPdfExportPages(-3, {}, PDF_EXPORT_SCOPE.ALL), [])
  assert.deepEqual(selectPdfExportPages(Number.NaN, {}, PDF_EXPORT_SCOPE.ALL), [])
  assert.throws(
    () => selectPdfExportPages(1, {}, 'selection'),
    /Unsupported PDF export scope/
  )
})

test('page-count messages use correct singular and plural forms', () => {
  assert.equal(formatPageCount(0), '0 pages')
  assert.equal(formatPageCount(1), '1 page')
  assert.equal(formatPageCount(2), '2 pages')
})
