/**
 * Utility functions for the Currency Intelligence Platform
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number, decimals: number = 4): string {
  return value.toFixed(decimals);
}

export function formatPercentage(value: number, decimals: number = 2): string {
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateShort(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    year: 'numeric',
  });
}

export function getDirectionColor(direction: string): string {
  switch (direction) {
    case 'Rising':
      return 'text-success';
    case 'Falling':
      return 'text-danger';
    default:
      return 'text-sapphire-gray';
  }
}

export function getDirectionIcon(direction: string): string {
  switch (direction) {
    case 'Rising':
      return '↑';
    case 'Falling':
      return '↓';
    default:
      return '→';
  }
}

export function getChangeColor(value: number | null): string {
  if (value === null) return 'text-sapphire-gray';
  if (value > 0) return 'text-success';
  if (value < 0) return 'text-danger';
  return 'text-sapphire-gray';
}

export function getCurrencyColor(currency: string): string {
  const colors: Record<string, string> = {
    EUR: '#0052FF',
    GBP: '#DC2626',
    CAD: '#16A34A',
  };
  return colors[currency] || '#6B7280';
}

export function getCurrencyName(currency: string): string {
  const names: Record<string, string> = {
    EUR: 'Euro',
    GBP: 'British Pound',
    CAD: 'Canadian Dollar',
  };
  return names[currency] || currency;
}

export function calculateMovingAverage(data: number[], window: number): number[] {
  const result: number[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < window - 1) {
      result.push(NaN);
    } else {
      const sum = data.slice(i - window + 1, i + 1).reduce((a, b) => a + b, 0);
      result.push(sum / window);
    }
  }
  return result;
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}


