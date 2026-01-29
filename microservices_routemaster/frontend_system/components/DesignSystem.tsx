/**
 * Design System Components - Accessible, reusable UI components
 * Follows WCAG 2.1 AA accessibility standards
 */

import React, { forwardRef } from 'react'
import type { ButtonProps, InputProps, ModalProps } from '../types'

interface StyledButtonProps extends ButtonProps {
  children: React.ReactNode
}

// ============================================================================
// Button Component
// ============================================================================

export const Button = forwardRef<HTMLButtonElement, StyledButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      disabled = false,
      loading = false,
      onClick,
      type = 'button',
      ariaLabel,
      children,
      ...props
    }: StyledButtonProps,
    ref: React.ForwardedRef<HTMLButtonElement>,
  ) => {
    const baseStyles = `
      font-weight: 600;
      border-radius: 4px;
      cursor: ${disabled || loading ? 'not-allowed' : 'pointer'};
      opacity: ${disabled ? 0.6 : 1};
      transition: all 200ms ease;
      border: none;
      font-family: inherit;
    `

    const sizeStyles: Record<string, string> = {
      sm: 'padding: 8px 12px; font-size: 12px;',
      md: 'padding: 10px 16px; font-size: 14px;',
      lg: 'padding: 12px 20px; font-size: 16px;',
    }

    const variantStyles: Record<string, string> = {
      primary: 'background-color: #007bff; color: white;',
      secondary: 'background-color: #6c757d; color: white;',
      danger: 'background-color: #dc3545; color: white;',
      ghost: 'background-color: transparent; color: #007bff; border: 1px solid #007bff;',
    }

    const style = baseStyles + sizeStyles[size] + variantStyles[variant]

    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled || loading}
        onClick={onClick}
        aria-label={ariaLabel}
        aria-busy={loading}
        style={{ ...typeof style === 'string' ? {} : style }}
        {...props}
      >
        {loading ? '...' : children}
      </button>
    )
  },
)
Button.displayName = 'Button'

// ============================================================================
// Input Component
// ============================================================================

interface StyledInputProps extends InputProps {
  onChange?: (value: string) => void
}

export const Input = forwardRef<HTMLInputElement, StyledInputProps>(
  (
    {
      type = 'text',
      placeholder,
      value,
      onChange,
      error,
      disabled = false,
      required = false,
      ariaLabel,
      ariaDescribedBy,
      ...props
    }: StyledInputProps,
    ref: React.ForwardedRef<HTMLInputElement>,
  ) => {
    const errorId = ariaDescribedBy || (error ? `${ariaLabel}-error` : undefined)

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <input
          ref={ref}
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => onChange?.(e.target.value)}
          disabled={disabled}
          required={required}
          aria-label={ariaLabel}
          aria-describedby={errorId}
          aria-invalid={!!error}
          style={{
            padding: '10px',
            borderRadius: '4px',
            border: `1px solid ${error ? '#dc3545' : '#ddd'}`,
            fontSize: '14px',
            fontFamily: 'inherit',
            backgroundColor: disabled ? '#f5f5f5' : 'white',
          }}
          {...props}
        />
        {error && (
          <span
            id={errorId}
            style={{
              color: '#dc3545',
              fontSize: '12px',
              marginTop: '2px',
            }}
            role="alert"
          >
            {error}
          </span>
        )}
      </div>
    )
  },
)
Input.displayName = 'Input'

// ============================================================================
// Modal Component
// ============================================================================

interface StyledModalProps extends ModalProps {
  children: React.ReactNode
}

export function Modal({
  isOpen,
  title,
  onClose,
  size = 'md',
  isDismissible = true,
  ariaLabelledBy,
  children,
}: StyledModalProps) {
  if (!isOpen) return null

  const sizeStyles: Record<string, string> = {
    sm: 'width: 400px;',
    md: 'width: 600px;',
    lg: 'width: 800px;',
  }

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isDismissible && e.target === e.currentTarget) {
      onClose()
    }
  }

  return (
    <div
      role="presentation"
      onClick={handleBackdropClick}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={ariaLabelledBy}
        style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          width: size === 'sm' ? '400px' : size === 'lg' ? '800px' : '600px',
          maxHeight: '90vh',
          overflow: 'auto',
          padding: '24px',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px',
          }}
        >
          <h2 id={ariaLabelledBy} style={{ margin: 0, fontSize: '20px', fontWeight: 600 }}>
            {title}
          </h2>
          {isDismissible && (
            <button
              onClick={onClose}
              aria-label="Close modal"
              style={{
                background: 'none',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer',
                color: '#666',
              }}
            >
              ×
            </button>
          )}
        </div>
        {children}
      </div>
    </div>
  )
}

// ============================================================================
// Spinner Component - Loading indicator
// ============================================================================

export function Spinner({
  size = 'md',
  ariaLabel = 'Loading',
}: {
  size?: 'sm' | 'md' | 'lg'
  ariaLabel?: string
}): JSX.Element {
  const sizeMap: Record<string, string> = { sm: '24px', md: '40px', lg: '56px' }

  return (
    <div
      role="status"
      aria-label={ariaLabel}
      style={{
        width: sizeMap[size],
        height: sizeMap[size],
        border: '3px solid #f3f3f3',
        borderTop: '3px solid #007bff',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
      }}
    >
      <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

// ============================================================================
// Alert Component
// ============================================================================

export function Alert({
  type = 'info',
  message,
  onDismiss,
}: {
  type?: 'success' | 'error' | 'warning' | 'info'
  message: string
  onDismiss?: () => void
}): JSX.Element {
  const colors: Record<string, { bg: string; border: string; text: string }> = {
    success: { bg: '#d4edda', border: '#c3e6cb', text: '#155724' },
    error: { bg: '#f8d7da', border: '#f5c6cb', text: '#721c24' },
    warning: { bg: '#fff3cd', border: '#ffeaa7', text: '#856404' },
    info: { bg: '#d1ecf1', border: '#bee5eb', text: '#0c5460' },
  }

  const color = colors[type]

  return (
    <div
      role="alert"
      style={{
        padding: '12px 16px',
        borderRadius: '4px',
        backgroundColor: color.bg,
        border: `1px solid ${color.border}`,
        color: color.text,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '12px',
      }}
    >
      <span>{message}</span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          aria-label="Dismiss alert"
          style={{
            background: 'none',
            border: 'none',
            color: 'inherit',
            cursor: 'pointer',
            fontSize: '16px',
          }}
        >
          ×
        </button>
      )}
    </div>
  )
}

// ============================================================================
// Tooltip Component
// ============================================================================

export function Tooltip({
  content,
  children,
  position = 'top',
}: {
  content: string
  children: React.ReactNode
  position?: 'top' | 'bottom' | 'left' | 'right'
}): JSX.Element {
  const [isVisible, setIsVisible] = React.useState(false)

  const positionStyles: Record<string, string> = {
    top: 'bottom: 100%; left: 50%; transform: translateX(-50%); marginBottom: 8px;',
    bottom: 'top: 100%; left: 50%; transform: translateX(-50%); marginTop: 8px;',
    left: 'right: 100%; top: 50%; transform: translateY(-50%); marginRight: 8px;',
    right: 'left: 100%; top: 50%; transform: translateY(-50%); marginLeft: 8px;',
  }

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        role="presentation"
      >
        {children}
      </div>
      {isVisible && (
        <div
          role="tooltip"
          style={{
            position: 'absolute',
            bottom: position === 'top' ? '100%' : position === 'bottom' ? 'auto' : 'auto',
            top: position === 'bottom' ? '100%' : position === 'top' ? 'auto' : '50%',
            left: position === 'right' ? 'auto' : position === 'left' ? 'auto' : '50%',
            right: position === 'left' ? '100%' : 'auto',
            transform: position === 'top' || position === 'bottom' ? 'translateX(-50%)' : position === 'left' || position === 'right' ? 'translateY(-50%)' : 'translate(-50%, -50%)',
            marginBottom: position === 'top' ? '8px' : 'auto',
            marginTop: position === 'bottom' ? '8px' : 'auto',
            marginRight: position === 'left' ? '8px' : 'auto',
            marginLeft: position === 'right' ? '8px' : 'auto',
            backgroundColor: '#333',
            color: '#fff',
            padding: '8px 12px',
            borderRadius: '4px',
            fontSize: '12px',
            whiteSpace: 'nowrap',
            zIndex: 999,
            pointerEvents: 'none',
          }}
        >
          {content}
        </div>
      )}
    </div>
  )
}

// ============================================================================
// Badge Component
// ============================================================================

export function Badge({
  variant = 'default',
  children,
}: {
  variant?: 'default' | 'success' | 'error' | 'warning' | 'info'
  children: React.ReactNode
}): JSX.Element {
  const variants: Record<string, string> = {
    default: 'background-color: #e9ecef; color: #495057;',
    success: 'background-color: #d4edda; color: #155724;',
    error: 'background-color: #f8d7da; color: #721c24;',
    warning: 'background-color: #fff3cd; color: #856404;',
    info: 'background-color: #d1ecf1; color: #0c5460;',
  }

  return (
    <span
      style={{
        display: 'inline-block',
        padding: '4px 8px',
        borderRadius: '12px',
        fontSize: '12px',
        fontWeight: 600,
      } as React.CSSProperties}
    >
      {children}
    </span>
  )
}
