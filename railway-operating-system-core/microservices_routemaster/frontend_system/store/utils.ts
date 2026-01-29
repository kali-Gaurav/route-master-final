/**
 * Frontend System Utilities - Common helper functions and utilities
 */

import type { ApiError, Station, Train, Route, Booking } from '../types'

// ============================================================================
// Error Handling Utilities
// ============================================================================

export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    'message' in error &&
    'status' in error
  )
}

export function getErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    return error.message
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'An unknown error occurred'
}

export function isRetryableError(error: ApiError): boolean {
  // Retry on server errors (5xx) and rate limiting (429)
  return error.status >= 500 || error.status === 429
}

// ============================================================================
// Validation Utilities
// ============================================================================

export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

export function validatePassword(password: string): {
  isValid: boolean
  errors: string[]
} {
  const errors: string[] = []

  if (password.length < 8) {
    errors.push('Password must be at least 8 characters')
  }
  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain an uppercase letter')
  }
  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain a lowercase letter')
  }
  if (!/[0-9]/.test(password)) {
    errors.push('Password must contain a number')
  }
  if (!/[!@#$%^&*]/.test(password)) {
    errors.push('Password must contain a special character (!@#$%^&*)')
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}

export function validatePhoneNumber(phone: string): boolean {
  const phoneRegex = /^[\d\s\-\+\(\)]{10,}$/
  return phoneRegex.test(phone.replace(/\D/g, ''))
}

// ============================================================================
// Formatting Utilities
// ============================================================================

export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount)
}

export function formatDate(date: string | Date, format: 'short' | 'long' = 'short'): string {
  const d = typeof date === 'string' ? new Date(date) : date

  if (format === 'short') {
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return d.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

export function formatTime(date: string | Date, format: '12h' | '24h' = '12h'): string {
  const d = typeof date === 'string' ? new Date(date) : date

  if (format === '12h') {
    return d.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  return d.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`
  return `${Math.round(seconds / 3600)}h ${Math.round((seconds % 3600) / 60)}m`
}

export function truncateString(str: string, maxLength: number, suffix = '...'): string {
  if (str.length <= maxLength) return str
  return str.substring(0, maxLength - suffix.length) + suffix
}

// ============================================================================
// Array & Object Utilities
// ============================================================================

export function groupBy<T>(items: T[], key: keyof T): Record<string, T[]> {
  return items.reduce(
    (acc, item) => {
      const groupKey = String(item[key])
      if (!acc[groupKey]) {
        acc[groupKey] = []
      }
      acc[groupKey].push(item)
      return acc
    },
    {} as Record<string, T[]>,
  )
}

export function sortBy<T>(items: T[], key: keyof T, order: 'asc' | 'desc' = 'asc'): T[] {
  return [...items].sort((a, b) => {
    const aVal = a[key]
    const bVal = b[key]

    if (aVal < bVal) return order === 'asc' ? -1 : 1
    if (aVal > bVal) return order === 'asc' ? 1 : -1
    return 0
  })
}

export function unique<T>(items: T[], key?: keyof T): T[] {
  if (!key) {
    return Array.from(new Set(items))
  }

  const seen = new Set()
  return items.filter((item) => {
    const value = item[key]
    if (seen.has(value)) return false
    seen.add(value)
    return true
  })
}

export function paginate<T>(items: T[], page: number, pageSize: number): T[] {
  const start = (page - 1) * pageSize
  return items.slice(start, start + pageSize)
}

// ============================================================================
// Railway Domain Utilities
// ============================================================================

export function getTrainStatusColor(status: Train['status']): string {
  const colors = {
    running: '#28a745',    // green
    delayed: '#ffc107',    // amber
    cancelled: '#dc3545',  // red
    maintenance: '#6c757d', // gray
  }
  return colors[status]
}

export function getTrainStatusLabel(status: Train['status']): string {
  const labels = {
    running: 'Running',
    delayed: 'Delayed',
    cancelled: 'Cancelled',
    maintenance: 'Maintenance',
  }
  return labels[status]
}

export function getBookingStatusColor(status: Booking['status']): string {
  const colors = {
    confirmed: '#28a745',  // green
    pending: '#ffc107',    // amber
    cancelled: '#dc3545',  // red
  }
  return colors[status]
}

export function getStationTierLabel(tier: Station['tier']): string {
  const labels = {
    major: 'Major Hub',
    secondary: 'Secondary',
    minor: 'Minor',
  }
  return labels[tier]
}

export function calculateRouteDuration(route: Route): string {
  const start = new Date(route.departure_time)
  const end = new Date(route.arrival_time)
  const seconds = (end.getTime() - start.getTime()) / 1000
  return formatDuration(seconds)
}

export function getRouteStops(route: Route): string {
  return route.stops.map((s) => s.code).join(' → ')
}

export function isUpcomingRoute(route: Route, hoursAhead = 24): boolean {
  const departure = new Date(route.departure_time)
  const now = new Date()
  const hoursUntilDeparture = (departure.getTime() - now.getTime()) / (1000 * 60 * 60)
  return hoursUntilDeparture > 0 && hoursUntilDeparture <= hoursAhead
}

// ============================================================================
// Local Storage Utilities
// ============================================================================

export function setLocalStorage(key: string, value: unknown, expiresIn?: number): void {
  try {
    const item = {
      value,
      expiresAt: expiresIn ? Date.now() + expiresIn * 1000 : null,
    }
    localStorage.setItem(key, JSON.stringify(item))
  } catch (error) {
    console.error('Error setting localStorage:', error)
  }
}

export function getLocalStorage<T>(key: string, defaultValue?: T): T | null {
  try {
    const item = localStorage.getItem(key)
    if (!item) return defaultValue || null

    const parsed = JSON.parse(item)

    // Check expiration
    if (parsed.expiresAt && Date.now() > parsed.expiresAt) {
      localStorage.removeItem(key)
      return defaultValue || null
    }

    return parsed.value as T
  } catch (error) {
    console.error('Error getting localStorage:', error)
    return defaultValue || null
  }
}

export function removeLocalStorage(key: string): void {
  try {
    localStorage.removeItem(key)
  } catch (error) {
    console.error('Error removing localStorage:', error)
  }
}

// ============================================================================
// Analytics Utilities
// ============================================================================

export function trackEvent(eventName: string, properties?: Record<string, unknown>): void {
  try {
    // In production: send to analytics service (Google Analytics, Mixpanel, etc.)
    if (window.gtag) {
      window.gtag('event', eventName, properties)
    }
  } catch (error) {
    console.error('Error tracking event:', error)
  }
}

export function trackPageView(pageName: string, properties?: Record<string, unknown>): void {
  trackEvent('page_view', { page_name: pageName, ...properties })
}

export function trackError(error: Error, context?: Record<string, unknown>): void {
  trackEvent('error', {
    message: error.message,
    stack: error.stack,
    ...context,
  })
}

// ============================================================================
// Performance Utilities
// ============================================================================

export function measurePerformance(label: string, fn: () => void): number {
  const start = performance.now()
  fn()
  const end = performance.now()
  const duration = end - start

  if (process.env.NODE_ENV === 'development') {
    console.debug(`[Performance] ${label}: ${duration.toFixed(2)}ms`)
  }

  return duration
}

export async function measureAsyncPerformance<T>(
  label: string,
  fn: () => Promise<T>,
): Promise<{ result: T; duration: number }> {
  const start = performance.now()
  const result = await fn()
  const end = performance.now()
  const duration = end - start

  if (process.env.NODE_ENV === 'development') {
    console.debug(`[Performance] ${label}: ${duration.toFixed(2)}ms`)
  }

  return { result, duration }
}

// Declare gtag for TypeScript
declare global {
  interface Window {
    gtag?: (command: string, ...args: unknown[]) => void
  }
}
