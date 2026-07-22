import { JSDOM } from 'jsdom'
import DOMPurify from 'dompurify'

// Create a DOMPurify instance with jsdom
const window = new JSDOM('').window
const purify = DOMPurify(window)

/**
 * Sanitize a string value to prevent XSS
 */
export function sanitizeString(value) {
  if (typeof value !== 'string') return value
  return purify.sanitize(value, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] })
}

/**
 * Recursively sanitize all string values in an object
 */
export function sanitizeObject(obj) {
  if (obj === null || obj === undefined) return obj
  if (typeof obj === 'string') return sanitizeString(obj)
  if (typeof obj !== 'object') return obj
  if (Array.isArray(obj)) return obj.map(sanitizeObject)

  const sanitized = {}
  for (const [key, value] of Object.entries(obj)) {
    sanitized[key] = sanitizeObject(value)
  }
  return sanitized
}

/**
 * Express middleware to sanitize request body
 */
export function sanitizeBody(req, res, next) {
  if (req.body && typeof req.body === 'object') {
    // Sanitize specific text fields that could contain user input
    if (req.body.displayName) {
      req.body.displayName = sanitizeString(req.body.displayName)
    }
    if (req.body.name) {
      req.body.name = sanitizeString(req.body.name)
    }
    if (req.body.description) {
      req.body.description = sanitizeString(req.body.description)
    }
    if (req.body.createdBy) {
      req.body.createdBy = sanitizeString(req.body.createdBy)
    }
    if (req.body.documentName) {
      req.body.documentName = sanitizeString(req.body.documentName)
    }

    // Sanitize text fields within annotations
    if (req.body.annotations) {
      req.body.annotations = sanitizeAnnotations(req.body.annotations)
    }
  }
  next()
}

/**
 * Sanitize annotation objects
 * Only sanitizes text content fields, preserves coordinates and other data
 */
function sanitizeAnnotations(annotations) {
  if (!annotations || typeof annotations !== 'object') return annotations

  const sanitized = { ...annotations }

  if (sanitized.settings && typeof sanitized.settings === 'object') {
    sanitized.settings = sanitizeObject(sanitized.settings)
  }

  // Sanitize comment texts
  if (Array.isArray(sanitized.comments)) {
    sanitized.comments = sanitized.comments.map(comment => ({
      ...comment,
      text: comment.text ? sanitizeString(comment.text) : comment.text,
      name: comment.name ? sanitizeString(comment.name) : comment.name,
      createdBy: comment.createdBy ? sanitizeString(comment.createdBy) : comment.createdBy
    }))
  }

  // Sanitize createdBy fields in all annotation types
  const annotationTypes = ['highlights', 'underlines', 'traces', 'angles', 'measures', 'distances', 'horizontalBands', 'verticalBands']
  annotationTypes.forEach(type => {
    if (Array.isArray(sanitized[type])) {
      sanitized[type] = sanitized[type].map(item => ({
        ...item,
        label: item.label ? sanitizeString(item.label) : item.label,
        name: item.name ? sanitizeString(item.name) : item.name,
        createdBy: item.createdBy ? sanitizeString(item.createdBy) : item.createdBy
      }))
    }
  })

  return sanitized
}
