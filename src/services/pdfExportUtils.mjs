export const PDF_EXPORT_SCOPE = Object.freeze({
  ANNOTATED: 'annotated',
  ALL: 'all',
})

function hasEntries(value) {
  return Array.isArray(value) && value.some(Boolean)
}

/**
 * Return whether a document page contains at least one exportable annotation.
 * All annotation stores are checked because length bands live outside the main
 * per-page annotation array.
 */
export function pageHasExportableAnnotations(
  pageIndex,
  {
    annotationsByPage = [],
    commentsByPage = [],
    lengthMeasurements = {},
  } = {}
) {
  if (!Number.isInteger(pageIndex) || pageIndex < 0) return false

  if (hasEntries(annotationsByPage?.[pageIndex])) return true
  if (hasEntries(commentsByPage?.[pageIndex])) return true

  if (!lengthMeasurements || typeof lengthMeasurements !== 'object') return false
  return Object.values(lengthMeasurements).some((pages) =>
    hasEntries(pages?.[pageIndex])
  )
}

/**
 * Build a stable, document-ordered list of page indexes for PDF export.
 */
export function selectPdfExportPages(
  totalPages,
  annotationState = {},
  scope = PDF_EXPORT_SCOPE.ANNOTATED
) {
  const parsedTotal = Number(totalPages)
  const pageCount = Number.isFinite(parsedTotal)
    ? Math.max(0, Math.floor(parsedTotal))
    : 0

  if (!Object.values(PDF_EXPORT_SCOPE).includes(scope)) {
    throw new Error(`Unsupported PDF export scope: ${scope}`)
  }

  const pages = Array.from({ length: pageCount }, (_, pageIndex) => pageIndex)
  if (scope === PDF_EXPORT_SCOPE.ALL) return pages

  return pages.filter((pageIndex) =>
    pageHasExportableAnnotations(pageIndex, annotationState)
  )
}

export function formatPageCount(count) {
  const safeCount = Number.isFinite(Number(count))
    ? Math.max(0, Math.floor(Number(count)))
    : 0
  return `${safeCount} page${safeCount === 1 ? '' : 's'}`
}
