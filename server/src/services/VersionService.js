import { prisma } from '../lib/prisma.js'
import { NotFoundError, ValidationError } from '../utils/errors.js'
import { config } from '../config/env.js'
import { logger } from '../utils/logger.js'

export const versionService = {
  /**
   * Create a new version checkpoint
   */
  async create(sessionId, { name, description, createdBy }) {
    // Get current session to snapshot annotations
    const session = await prisma.session.findUnique({
      where: { id: sessionId },
      select: { annotations: true }
    })

    if (!session) {
      throw new NotFoundError(`Session not found: ${sessionId}`)
    }

    // Check version limit
    const versionCount = await prisma.version.count({
      where: { sessionId }
    })

    if (versionCount >= config.session.maxVersionsPerSession) {
      throw new ValidationError(`Maximum of ${config.session.maxVersionsPerSession} versions per session reached`)
    }

    // Get next version number
    const lastVersion = await prisma.version.findFirst({
      where: { sessionId },
      orderBy: { versionNumber: 'desc' },
      select: { versionNumber: true }
    })

    const versionNumber = (lastVersion?.versionNumber || 0) + 1

    const version = await prisma.version.create({
      data: {
        sessionId,
        name: name.trim(),
        description: description?.trim() || null,
        createdBy: createdBy?.trim() || 'Anonymous',
        annotations: session.annotations,
        versionNumber
      }
    })

    logger.info('Version created', { sessionId, versionId: version.id, versionNumber })
    return version
  },

  /**
   * List all versions for a session
   */
  async listBySession(sessionId) {
    // Verify session exists
    const sessionExists = await prisma.session.count({
      where: { id: sessionId }
    })

    if (!sessionExists) {
      throw new NotFoundError(`Session not found: ${sessionId}`)
    }

    const versions = await prisma.version.findMany({
      where: { sessionId },
      orderBy: { versionNumber: 'desc' },
      select: {
        id: true,
        name: true,
        description: true,
        createdBy: true,
        versionNumber: true,
        createdAt: true
      }
    })

    return versions
  },

  /**
   * Get a specific version with full annotations
   */
  async getById(sessionId, versionId) {
    const version = await prisma.version.findFirst({
      where: {
        id: versionId,
        sessionId
      }
    })

    if (!version) {
      throw new NotFoundError(`Version not found: ${versionId}`)
    }

    return version
  },

  /**
   * Check if there are unsaved changes since last checkpoint
   */
  async checkUnsavedChanges(sessionId) {
    // Get current session annotations
    const session = await prisma.session.findUnique({
      where: { id: sessionId },
      select: { annotations: true }
    })

    if (!session) {
      throw new NotFoundError(`Session not found: ${sessionId}`)
    }

    // Get most recent version
    const lastVersion = await prisma.version.findFirst({
      where: { sessionId },
      orderBy: { versionNumber: 'desc' },
      select: { id: true, name: true, versionNumber: true, annotations: true }
    })

    // If no versions exist, check if there are any annotations
    if (!lastVersion) {
      const hasAnnotations = Object.entries(session.annotations || {})
        .some(([key, value]) => {
          if (key === 'settings') {
            return value && typeof value === 'object' && Object.keys(value).length > 0
          }
          return Array.isArray(value) && value.length > 0
        })
      return { hasUnsavedChanges: hasAnnotations, lastVersion: null }
    }

    // Compare using JSON stringify
    const hasUnsavedChanges = JSON.stringify(session.annotations) !==
                              JSON.stringify(lastVersion.annotations)

    return {
      hasUnsavedChanges,
      lastVersion: {
        id: lastVersion.id,
        name: lastVersion.name,
        versionNumber: lastVersion.versionNumber
      }
    }
  },

  /**
   * Restore session to a previous version
   * Creates a checkpoint marking the restore point
   */
  async restore(sessionId, versionId) {
    // Get the version to restore
    const version = await this.getById(sessionId, versionId)

    // Restore annotations to session
    const updatedSession = await prisma.session.update({
      where: { id: sessionId },
      data: {
        annotations: version.annotations,
        lastActiveAt: new Date()
      }
    })

    // Create a checkpoint marking the restore
    const lastVersion = await prisma.version.findFirst({
      where: { sessionId },
      orderBy: { versionNumber: 'desc' },
      select: { versionNumber: true }
    })

    const newVersionNumber = (lastVersion?.versionNumber || 0) + 1

    const restoreCheckpoint = await prisma.version.create({
      data: {
        sessionId,
        name: `Restored from v${version.versionNumber}`,
        description: `Restored to: ${version.name}`,
        createdBy: 'System',
        annotations: version.annotations,
        versionNumber: newVersionNumber
      }
    })

    logger.info('Version restored', {
      sessionId,
      restoredVersionId: versionId,
      restoredVersionNumber: version.versionNumber,
      newCheckpointId: restoreCheckpoint.id
    })

    return {
      session: updatedSession,
      restoredFrom: version,
      newVersion: restoreCheckpoint
    }
  },

  /**
   * Delete a specific version
   */
  async delete(sessionId, versionId) {
    const version = await prisma.version.findFirst({
      where: {
        id: versionId,
        sessionId
      }
    })

    if (!version) {
      throw new NotFoundError(`Version not found: ${versionId}`)
    }

    await prisma.version.delete({
      where: { id: versionId }
    })

    logger.info('Version deleted', { sessionId, versionId })
  }
}
