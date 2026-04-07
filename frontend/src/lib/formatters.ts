/**
 * Date and currency formatters used across the application.
 */

/** Format a date string to Brazilian short date: "01/03/2026" */
export function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString('en-US', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

/** Format a date string to short label for charts: "Mar 1" */
export function formatChartDateLabel(isoString: string): string {
  return new Date(isoString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })
}

/** Format a date string to full datetime: "03/01/2026 14:30:00" */
export function formatDateTime(isoString: string): string {
  return new Date(isoString).toLocaleString('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

/** Format a number as currency: "R$ 1.234,56" */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}
