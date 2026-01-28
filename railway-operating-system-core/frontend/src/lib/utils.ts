import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
/**
 * Get the API URL for a given path
 * Uses relative paths in production, localhost in development
 * Respects VITE_API_URL environment variable if set
 */
export const getApiUrl = (path: string): string => {
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return `http://localhost:8000${path}`;
  }
  // In production, use relative path or environment variable
  const apiBase = import.meta.env.VITE_API_URL || '';
  return `${apiBase}${path}`;
};