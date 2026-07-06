import { v4 as uuidv4 } from 'uuid'
import { sessionService } from '../services/SessionService.js'
import { presenceService } from '../services/PresenceService.js'
import { sanitizeString, sanitizeObject } from '../middleware/sanitize.js'
import { isValidUUID } from '../utils/validators.js'
import { logger } from '../utils/logger.js'

/**
 * Handle incoming WebSocket messages
 */
export async function handleMessage(ws, message, context) {
  let data
  try {
    data = JSON.parse(message)
  } catch {
    sendError(ws, 'Invalid JSON message')
    return
  }

  const { type, payload } = data

  switch (type) {
    case 'join':
      await handleJoin(ws, payload, context)
      break
    case 'cursor:move':
      handleCursorMove(ws, payload, context)
      break
    case 'annotation:add':
      await handleAnnotationAdd(ws, payload, context)
      break
    case 'annotation:update':
      await handleAnnotationUpdate(ws, payload, context)
      break
    case 'annotation:delete':
      await handleAnnotationDelete(ws, payload, context)
      break
    case 'ping':
      handlePing(ws, context)
      break
    case 'follow:start':
      handleFollowStart(ws, payload, context)
      break
    case 'follow:stop':
      handleFollowStop(ws, payload, context)
      break
    case 'viewport:update':
      handleViewportUpdate(ws, payload, context)
      break
    case 'filters:update':
      handleFiltersUpdate(ws, payload, context)
      break
    default:
      sendError(ws, `Unknown message type: ${type}`)
  }
}

/**
 * Handle participant joining a session
 */
async function handleJoin(ws, payload, context) {
  const { sessionId, displayName, participantId: clientParticipantId } = payload || {}

  if (!sessionId || !isValidUUID(sessionId)) {
    sendError(ws, 'Invalid session ID')
    return
  }

  // Verify session exists
  const exists = await sessionService.exists(sessionId)
  if (!exists) {
    sendError(ws, 'Session not found', 'SESSION_NOT_FOUND')
    return
  }

  // Use client-provided participant ID if valid, otherwise generate new one
  // This allows reconnection without creating duplicate participants
  const participantId = (clientParticipantId && isValidUUID(clientParticipantId))
    ? clientParticipantId
    : uuidv4()
  const sanitizedName = sanitizeString(displayName || 'Anonymous')

  // Join the session
  const participant = presenceService.join(sessionId, participantId, {
    displayName: sanitizedName,
    ws
  })

  // Store context for this connection
  context.sessionId = sessionId
  context.participantId = participantId

  // Send confirmation to the joining participant
  send(ws, {
    type: 'joined',
    payload: {
      participantId,
      displayName: participant.displayName,
      color: participant.color,
      sessionId
    }
  })

  // Send current participants list
  const participants = presenceService.getParticipants(sessionId)
  send(ws, {
    type: 'participants:list',
    payload: { participants }
  })

  // Send current follow state
  send(ws, {
    type: 'follow:state',
    payload: presenceService.getFollowState(sessionId)
  })

  // Only notify others if this is a new participant (not a reconnection)
  if (!participant.isReconnect) {
    presenceService.broadcast(sessionId, participantId, {
      type: 'participant:joined',
      payload: {
        id: participantId,
        displayName: participant.displayName,
        color: participant.color
      }
    })
  }

  logger.debug('Participant joined via WebSocket', { sessionId, participantId, isReconnect: !!participant.isReconnect })
}

/**
 * Handle cursor movement
 */
function handleCursorMove(ws, payload, context) {
  const { sessionId, participantId } = context
  if (!sessionId || !participantId) return

  const { x, y, pageIndex } = payload || {}
  if (typeof x !== 'number' || typeof y !== 'number') return

  const cursor = { x, y, pageIndex: pageIndex || 0 }
  presenceService.updateCursor(sessionId, participantId, cursor)

  // Broadcast cursor position to others
  presenceService.broadcast(sessionId, participantId, {
    type: 'cursor:update',
    payload: {
      participantId,
      cursor
    }
  })
}

/**
 * Handle annotation addition
 */
async function handleAnnotationAdd(ws, payload, context) {
  const { sessionId, participantId } = context
  if (!sessionId || !participantId) {
    sendError(ws, 'Not in a session')
    return
  }

  const { annotationType, annotation } = payload || {}
  if (!annotationType || !annotation) {
    sendError(ws, 'Missing annotation data')
    return
  }

  try {
    // Get current session
    const session = await sessionService.getById(sessionId)
    const annotations = { ...session.annotations }

    // Initialize array if doesn't exist
    if (!annotations[annotationType]) {
      annotations[annotationType] = []
    }

    // Sanitize annotation and add
    const sanitizedAnnotation = sanitizeObject(annotation)
    annotations[annotationType].push(sanitizedAnnotation)

    // Save to database
    await sessionService.updateAnnotations(sessionId, annotations)

    // Broadcast to all (including sender for confirmation)
    presenceService.broadcastAll(sessionId, {
      type: 'annotation:sync',
      payload: {
        action: 'add',
        annotationType,
        annotation: sanitizedAnnotation,
        participantId
      }
    })
  } catch (err) {
    logger.error('Failed to add annotation', { sessionId, error: err.message })
    sendError(ws, 'Failed to add annotation')
  }
}

/**
 * Handle annotation update
 */
async function handleAnnotationUpdate(ws, payload, context) {
  const { sessionId, participantId } = context
  if (!sessionId || !participantId) {
    sendError(ws, 'Not in a session')
    return
  }

  const { annotationType, annotationId, updates, pageIndex } = payload || {}
  if (!annotationType || !annotationId || !updates) {
    sendError(ws, 'Missing annotation data')
    return
  }

  try {
    // Get current session
    const session = await sessionService.getById(sessionId)
    const annotations = { ...session.annotations }

    if (!annotations[annotationType]) {
      sendError(ws, 'Annotation type not found')
      return
    }

    // Find and update the annotation
    const index = annotations[annotationType].findIndex(a => a.id === annotationId)
    if (index === -1) {
      sendError(ws, 'Annotation not found')
      return
    }

    const sanitizedUpdates = sanitizeObject(updates)
    annotations[annotationType][index] = {
      ...annotations[annotationType][index],
      ...sanitizedUpdates
    }

    // Save to database
    await sessionService.updateAnnotations(sessionId, annotations)

    // Broadcast to all
    presenceService.broadcastAll(sessionId, {
      type: 'annotation:sync',
      payload: {
        action: 'update',
        annotationType,
        annotationId,
        updates: sanitizedUpdates,
        pageIndex,
        participantId
      }
    })
  } catch (err) {
    logger.error('Failed to update annotation', { sessionId, error: err.message })
    sendError(ws, 'Failed to update annotation')
  }
}

/**
 * Handle annotation deletion
 */
async function handleAnnotationDelete(ws, payload, context) {
  const { sessionId, participantId } = context
  if (!sessionId || !participantId) {
    sendError(ws, 'Not in a session')
    return
  }

  const { annotationType, annotationId, pageIndex } = payload || {}
  if (!annotationType || !annotationId) {
    sendError(ws, 'Missing annotation data')
    return
  }

  try {
    // Get current session
    const session = await sessionService.getById(sessionId)
    const annotations = { ...session.annotations }

    if (!annotations[annotationType]) {
      sendError(ws, 'Annotation type not found')
      return
    }

    // Remove the annotation
    annotations[annotationType] = annotations[annotationType].filter(a => a.id !== annotationId)

    // Save to database
    await sessionService.updateAnnotations(sessionId, annotations)

    // Broadcast to all
    presenceService.broadcastAll(sessionId, {
      type: 'annotation:sync',
      payload: {
        action: 'delete',
        annotationType,
        annotationId,
        pageIndex,
        participantId
      }
    })
  } catch (err) {
    logger.error('Failed to delete annotation', { sessionId, error: err.message })
    sendError(ws, 'Failed to delete annotation')
  }
}

/**
 * Handle ping (heartbeat)
 */
function handlePing(ws, context) {
  const { sessionId, participantId } = context
  if (sessionId && participantId) {
    presenceService.heartbeat(sessionId, participantId)
  }
  send(ws, { type: 'pong' })
}

// ==================== FOLLOW MODE HANDLERS ====================

/**
 * Handle follow:start - participant wants to follow another
 */
function handleFollowStart(ws, payload, context) {
  const { sessionId, participantId } = context
  if (!sessionId || !participantId) {
    sendError(ws, 'Not in a session')
    return
  }

  const { targetParticipantId } = payload || {}
  if (!targetParticipantId || !isValidUUID(targetParticipantId)) {
    sendError(ws, 'Invalid target participant ID')
    return
  }

  // Can't follow yourself
  if (targetParticipantId === participantId) {
    sendError(ws, 'Cannot follow yourself', 'SELF_FOLLOW')
    return
  }

  // Check if target exists
  const target = presenceService.getParticipant(sessionId, targetParticipantId)
  if (!target) {
    sendError(ws, 'Target participant not found', 'TARGET_NOT_FOUND')
    return
  }

  // Prevent circular follow (A follows B, B can't follow A)
  const targetFollowing = presenceService.getFollowing(sessionId, targetParticipantId)
  if (targetFollowing === participantId) {
    sendError(ws, 'Cannot follow someone who is following you', 'CIRCULAR_FOLLOW')
    return
  }

  // Set the follow relationship
  presenceService.setFollowing(sessionId, participantId, targetParticipantId)

  // Broadcast updated follow state to all participants
  presenceService.broadcastAll(sessionId, {
    type: 'follow:state',
    payload: presenceService.getFollowState(sessionId)
  })

  // Send current viewport/filters of target to the new follower
  const targetViewport = presenceService.getViewport(sessionId, targetParticipantId)
  const targetFilters = presenceService.getFilters(sessionId, targetParticipantId)

  if (targetViewport) {
    send(ws, {
      type: 'viewport:sync',
      payload: {
        ...targetViewport,
        fromParticipantId: targetParticipantId
      }
    })
  }

  if (targetFilters) {
    send(ws, {
      type: 'filters:sync',
      payload: {
        ...targetFilters,
        fromParticipantId: targetParticipantId
      }
    })
  }

  logger.debug('Follow started', { sessionId, participantId, targetParticipantId })
}

/**
 * Handle follow:stop - participant stops following
 */
function handleFollowStop(ws, payload, context) {
  const { sessionId, participantId } = context
  if (!sessionId || !participantId) {
    sendError(ws, 'Not in a session')
    return
  }

  // Clear the follow relationship
  presenceService.setFollowing(sessionId, participantId, null)

  // Broadcast updated follow state to all participants
  presenceService.broadcastAll(sessionId, {
    type: 'follow:state',
    payload: presenceService.getFollowState(sessionId)
  })

  logger.debug('Follow stopped', { sessionId, participantId })
}

/**
 * Handle viewport:update - participant changed their viewport
 */
function handleViewportUpdate(ws, payload, context) {
  const { sessionId, participantId } = context
  if (!sessionId || !participantId) return

  const { pageIndex, zoom, bounds } = payload || {}
  if (typeof pageIndex !== 'number') return

  // Store viewport state
  const viewport = { pageIndex, zoom, bounds }
  presenceService.setViewport(sessionId, participantId, viewport)

  // Find all followers and send them the viewport sync
  const followers = presenceService.getFollowersOf(sessionId, participantId)
  followers.forEach(followerId => {
    presenceService.sendToParticipant(sessionId, followerId, {
      type: 'viewport:sync',
      payload: {
        pageIndex,
        zoom,
        bounds,
        fromParticipantId: participantId
      }
    })
  })

  // Also broadcast page update to all for page indicators
  presenceService.broadcast(sessionId, participantId, {
    type: 'participant:viewport',
    payload: {
      participantId,
      pageIndex
    }
  })
}

/**
 * Handle filters:update - participant changed their image filters
 */
function handleFiltersUpdate(ws, payload, context) {
  const { sessionId, participantId } = context
  if (!sessionId || !participantId) return

  const { pageIndex, filters } = payload || {}
  if (typeof pageIndex !== 'number' || !filters) return

  // Store filters state
  presenceService.setFilters(sessionId, participantId, { pageIndex, filters })

  // Find all followers and send them the filters sync
  const followers = presenceService.getFollowersOf(sessionId, participantId)
  followers.forEach(followerId => {
    presenceService.sendToParticipant(sessionId, followerId, {
      type: 'filters:sync',
      payload: {
        pageIndex,
        filters,
        fromParticipantId: participantId
      }
    })
  })
}

/**
 * Handle connection close
 */
export function handleClose(context) {
  const { sessionId, participantId } = context
  if (!sessionId || !participantId) return

  // Clear follow relationships before leaving
  const affectedFollowers = presenceService.clearFollowRelationships(sessionId, participantId)

  const participant = presenceService.leave(sessionId, participantId)

  if (participant) {
    // Notify others about the participant leaving
    presenceService.broadcast(sessionId, participantId, {
      type: 'participant:left',
      payload: {
        participantId,
        displayName: participant.displayName
      }
    })

    // If there were followers, broadcast updated follow state
    if (affectedFollowers.length > 0) {
      presenceService.broadcastAll(sessionId, {
        type: 'follow:state',
        payload: presenceService.getFollowState(sessionId)
      })
    }
  }

  logger.debug('Participant disconnected', { sessionId, participantId })
}

// Helper functions
function send(ws, message) {
  if (ws.readyState === 1) {
    ws.send(JSON.stringify(message))
  }
}

function sendError(ws, message, code = 'ERROR') {
  send(ws, {
    type: 'error',
    payload: { code, message }
  })
}
