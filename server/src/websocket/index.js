import { WebSocketServer } from 'ws'
import { handleMessage, handleClose } from './handlers.js'
import { logger } from '../utils/logger.js'

let wss = null

/**
 * Initialize WebSocket server attached to HTTP server
 */
export function initWebSocket(server) {
  wss = new WebSocketServer({ server, path: '/ws' })

  wss.on('connection', (ws, req) => {
    const clientIp = req.socket.remoteAddress
    logger.debug('WebSocket connection established', { clientIp })

    // Connection context (will be populated on join)
    const context = {
      sessionId: null,
      participantId: null
    }

    ws.on('message', async (message) => {
      try {
        await handleMessage(ws, message.toString(), context)
      } catch (err) {
        logger.error('WebSocket message handler error', { error: err.message })
        ws.send(JSON.stringify({
          type: 'error',
          payload: { code: 'INTERNAL_ERROR', message: 'An error occurred' }
        }))
      }
    })

    ws.on('close', () => {
      handleClose(context)
    })

    ws.on('error', (err) => {
      logger.error('WebSocket error', { error: err.message })
      handleClose(context)
    })

    // Send welcome message
    ws.send(JSON.stringify({
      type: 'welcome',
      payload: { message: 'Connected to Seshat collaboration server' }
    }))
  })

  logger.info('WebSocket server initialized')
  return wss
}

/**
 * Get WebSocket server instance
 */
export function getWebSocketServer() {
  return wss
}

/**
 * Close WebSocket server
 */
export function closeWebSocket() {
  if (wss) {
    wss.close()
    logger.info('WebSocket server closed')
  }
}
