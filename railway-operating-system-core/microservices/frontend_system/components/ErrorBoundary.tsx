/**
 * Error Boundary Component - Catches React errors and displays fallback UI
 * Implements accessibility best practices for error states
 */

import React, { Component, ReactNode, ErrorInfo } from 'react'
import type { ErrorReport } from '../types'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  errorCount: number
}

export class ErrorBoundary extends Component<Props, State> {
  private errorReportQueue: ErrorReport[] = []

  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState((prevState) => ({
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }))

    // Report error to backend
    this.reportError(error, errorInfo)

    // Call custom error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error caught by boundary:', error, errorInfo)
    }
  }

  private async reportError(error: Error, errorInfo: ErrorInfo) {
    const errorReport: ErrorReport = {
      message: error.message,
      stack: error.stack || '',
      component: errorInfo.componentStack || 'Unknown Component',
      userId: this.getUserId(),
      sessionId: this.getSessionId(),
      timestamp: new Date().toISOString(),
      breadcrumbs: this.getBreadcrumbs(),
    }

    this.errorReportQueue.push(errorReport)

    // Send to error tracking service (Sentry, etc.)
    if (process.env.REACT_APP_ERROR_REPORTING_ENDPOINT) {
      try {
        await fetch(process.env.REACT_APP_ERROR_REPORTING_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(errorReport),
        })
      } catch (reportError) {
        console.error('Failed to report error:', reportError)
      }
    }
  }

  private getUserId(): string | undefined {
    try {
      const user = localStorage.getItem('auth_user')
      return user ? JSON.parse(user).id : undefined
    } catch {
      return undefined
    }
  }

  private getSessionId(): string {
    let sessionId = sessionStorage.getItem('session_id')
    if (!sessionId) {
      sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      sessionStorage.setItem('session_id', sessionId)
    }
    return sessionId
  }

  private getBreadcrumbs(): string[] {
    // In production: track user interactions, navigation, API calls
    return []
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div
            role="alert"
            aria-live="assertive"
            className="error-boundary-fallback"
            style={{
              padding: '20px',
              margin: '20px',
              border: '1px solid #dc3545',
              borderRadius: '4px',
              backgroundColor: '#f8d7da',
            }}
          >
            <h2 style={{ color: '#721c24', marginBottom: '10px' }}>Something went wrong</h2>
            <p style={{ color: '#721c24', marginBottom: '10px' }}>
              We're sorry, but something unexpected happened. Our team has been notified.
            </p>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details style={{ marginTop: '10px', color: '#721c24' }}>
                <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Error details</summary>
                <pre
                  style={{
                    backgroundColor: '#fff',
                    padding: '10px',
                    borderRadius: '4px',
                    overflow: 'auto',
                    marginTop: '10px',
                  }}
                >
                  {this.state.error.toString()}
                  {'\n\n'}
                  {this.state.errorInfo?.componentStack}
                </pre>
              </details>
            )}
            <button
              onClick={this.handleReset}
              style={{
                marginTop: '10px',
                padding: '10px 20px',
                backgroundColor: '#721c24',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
              aria-label="Try again after error"
            >
              Try again
            </button>
          </div>
        )
      )
    }

    return this.props.children
  }
}

// ============================================================================
// ErrorFallback - Reusable error fallback component
// ============================================================================

interface ErrorFallbackProps {
  error: Error
  resetError: () => void
}

export function ErrorFallback({ error, resetError }: ErrorFallbackProps) {
  return (
    <div
      role="alert"
      className="error-fallback"
      style={{
        padding: '20px',
        textAlign: 'center',
        backgroundColor: '#f8d7da',
        borderRadius: '4px',
      }}
    >
      <h2>Something went wrong</h2>
      <p>{error.message}</p>
      <button onClick={resetError} style={{ marginTop: '10px', padding: '10px 20px' }}>
        Try again
      </button>
    </div>
  )
}

// ============================================================================
// withErrorBoundary - HOC for wrapping components
// ============================================================================

export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode,
) {
  return function ErrorBoundaryWrapper(props: P) {
    return (
      <ErrorBoundary fallback={fallback}>
        <Component {...props} />
      </ErrorBoundary>
    )
  }
}
