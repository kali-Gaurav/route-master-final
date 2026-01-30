/**
 * State Management - Redux-like store with reducers and middleware
 */

import React, { createContext, useContext, ReactNode } from 'react'
import type { StoreState, StoreAction, ToastMessage, User } from '../types'

// ============================================================================
// Initial State
// ============================================================================

export const initialState: StoreState = {
  auth: {
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
  },
  ui: {
    sidebarOpen: true,
    theme: 'light',
    locale: 'en-US',
    toasts: [],
  },
  data: {
    stations: [],
    trains: [],
    routes: [],
    bookings: [],
  },
  cache: {
    lastFetch: {},
    ttl: 5 * 60 * 1000, // 5 minutes
  },
}

// ============================================================================
// Reducer
// ============================================================================

export function storeReducer(state: StoreState, action: StoreAction): StoreState {
  switch (action.type) {
    case 'SET_AUTH': {
      const user = action.payload as User | null
      return {
        ...state,
        auth: {
          user,
          token: state.auth.token,
          isAuthenticated: !!user,
          isLoading: false,
          error: null,
        },
      }
    }

    case 'SET_TOKEN': {
      const token = action.payload as string
      return {
        ...state,
        auth: {
          ...state.auth,
          token,
          isAuthenticated: !!state.auth.user && !!token,
        },
      }
    }

    case 'LOGOUT': {
      return {
        ...state,
        auth: {
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        },
        data: {
          stations: [],
          trains: [],
          routes: [],
          bookings: [],
        },
      }
    }

    case 'TOGGLE_SIDEBAR': {
      return {
        ...state,
        ui: {
          ...state.ui,
          sidebarOpen: !state.ui.sidebarOpen,
        },
      }
    }

    case 'SET_THEME': {
      const theme = action.payload as 'light' | 'dark'
      return {
        ...state,
        ui: {
          ...state.ui,
          theme,
        },
      }
    }

    case 'ADD_TOAST': {
      const toast = action.payload as ToastMessage
      return {
        ...state,
        ui: {
          ...state.ui,
          toasts: [...state.ui.toasts, toast],
        },
      }
    }

    case 'REMOVE_TOAST': {
      const toastId = action.payload as string
      return {
        ...state,
        ui: {
          ...state.ui,
          toasts: state.ui.toasts.filter((t) => t.id !== toastId),
        },
      }
    }

    case 'SET_STATIONS': {
      const stations = action.payload as any
      return {
        ...state,
        data: {
          ...state.data,
          stations,
        },
        cache: {
          ...state.cache,
          lastFetch: {
            ...state.cache.lastFetch,
            stations: new Date().toISOString(),
          },
        },
      }
    }

    case 'SET_TRAINS': {
      const trains = action.payload as any
      return {
        ...state,
        data: {
          ...state.data,
          trains,
        },
        cache: {
          ...state.cache,
          lastFetch: {
            ...state.cache.lastFetch,
            trains: new Date().toISOString(),
          },
        },
      }
    }

    case 'SET_ROUTES': {
      const routes = action.payload as any
      return {
        ...state,
        data: {
          ...state.data,
          routes,
        },
        cache: {
          ...state.cache,
          lastFetch: {
            ...state.cache.lastFetch,
            routes: new Date().toISOString(),
          },
        },
      }
    }

    case 'SET_BOOKINGS': {
      const bookings = action.payload as any
      return {
        ...state,
        data: {
          ...state.data,
          bookings,
        },
        cache: {
          ...state.cache,
          lastFetch: {
            ...state.cache.lastFetch,
            bookings: new Date().toISOString(),
          },
        },
      }
    }

    default:
      return state
  }
}

// ============================================================================
// Store Context & Hooks
// ============================================================================

interface StoreContextValue {
  state: StoreState
  dispatch: (action: StoreAction) => void
}

const StoreContext = createContext<StoreContextValue | null>(null)

export function StoreProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = React.useReducer(storeReducer, initialState)

  return <StoreContext.Provider value={{ state, dispatch }}>{children}</StoreContext.Provider>
}

export function useStore() {
  const context = useContext(StoreContext)
  if (!context) {
    throw new Error('useStore must be used within StoreProvider')
  }
  return context
}

// Convenience hooks for common store access patterns
export function useAuthStore() {
  const { state } = useStore()
  return state.auth
}

export function useUIStore() {
  const { state } = useStore()
  return state.ui
}

export function useDataStore() {
  const { state } = useStore()
  return state.data
}

export function useToasts() {
  const { state, dispatch } = useStore()

  const addToast = (toast: Omit<ToastMessage, 'id'>) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const toastWithId: ToastMessage = { ...toast, id }

    dispatch({ type: 'ADD_TOAST', payload: toastWithId })

    // Auto-remove after duration
    if (toast.duration !== Infinity) {
      setTimeout(() => {
        dispatch({ type: 'REMOVE_TOAST', payload: id })
      }, toast.duration || 3000)
    }

    return id
  }

  const removeToast = (id: string) => {
    dispatch({ type: 'REMOVE_TOAST', payload: id })
  }

  return {
    toasts: state.ui.toasts,
    addToast,
    removeToast,
    success: (message: string, duration?: number) =>
      addToast({ type: 'success', message, duration }),
    error: (message: string, duration?: number) =>
      addToast({ type: 'error', message, duration }),
    warning: (message: string, duration?: number) =>
      addToast({ type: 'warning', message, duration }),
    info: (message: string, duration?: number) =>
      addToast({ type: 'info', message, duration }),
  }
}

// ============================================================================
// Selectors - Memoized state queries
// ============================================================================

export function selectIsAuthenticated(state: StoreState): boolean {
  return state.auth.isAuthenticated
}

export function selectCurrentUser(state: StoreState) {
  return state.auth.user
}

export function selectHasPermission(state: StoreState, resource: string, action: string): boolean {
  if (!state.auth.user) return false
  if (state.auth.user.roles.includes('admin')) return true

  // Role-based permission check
  const permissions: Record<string, string[]> = {
    admin: ['read', 'write', 'delete'],
    power_user: ['read', 'write'],
    analyst: ['read'],
    viewer: ['read'],
    system: ['read', 'write', 'delete'],
  }

  const userRole = state.auth.user.roles[0]
  return permissions[userRole]?.includes(action) ?? false
}

export function selectCacheNeedsRefresh(state: StoreState, key: string): boolean {
  const lastFetch = state.cache.lastFetch[key]
  if (!lastFetch) return true

  const elapsed = Date.now() - new Date(lastFetch).getTime()
  return elapsed > state.cache.ttl
}
