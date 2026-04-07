/**
 * Application logger.
 *
 * Wraps the browser console with structured output and log levels.
 * In production builds, debug-level messages are silently dropped.
 *
 * Usage:
 *   import { logger } from '@/lib/logger'
 *   logger.info('User logged in', { userId: '42' })
 *   logger.error('Request failed', { url, status }, error)
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error'

export interface LogContext {
  [key: string]: unknown
}

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
}

/** Minimum level to emit. Promote to 'info' in production. */
const MIN_LEVEL: LogLevel =
  import.meta.env.PROD ? 'info' : 'debug'

function shouldLog(level: LogLevel): boolean {
  return LOG_LEVELS[level] >= LOG_LEVELS[MIN_LEVEL]
}

function formatMessage(level: LogLevel, message: string): string {
  const timestamp = new Date().toISOString()
  return `[${timestamp}] [${level.toUpperCase()}] ${message}`
}

function emit(
  level: LogLevel,
  message: string,
  context?: LogContext,
  error?: unknown,
): void {
  if (!shouldLog(level)) return

  const formatted = formatMessage(level, message)

  const args: unknown[] = [formatted]
  if (context && Object.keys(context).length > 0) args.push(context)
  if (error !== undefined) args.push(error)

  switch (level) {
    case 'debug':
      console.debug(...args)
      break
    case 'info':
      console.info(...args)
      break
    case 'warn':
      console.warn(...args)
      break
    case 'error':
      console.error(...args)
      break
  }
}

export const logger = {
  debug: (message: string, context?: LogContext) =>
    emit('debug', message, context),

  info: (message: string, context?: LogContext) =>
    emit('info', message, context),

  warn: (message: string, context?: LogContext, error?: unknown) =>
    emit('warn', message, context, error),

  error: (message: string, context?: LogContext, error?: unknown) =>
    emit('error', message, context, error),
}
