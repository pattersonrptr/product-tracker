/** Plan and Subscription domain types — mirrors backend entities */

export interface Plan {
  id: string
  name: string
  displayName: string
  priceCents: number
  maxActiveAlerts: number | null
  minFrequencyMinutes: number
  priceHistoryDays: number | null
  maxSources: number | null
  hasPushNotifications: boolean
  hasWhatsappNotifications: boolean
  hasApiAccess: boolean
  isActive: boolean
}

export interface Subscription {
  id: string
  userId: number
  planId: number
  planName: string
  status: 'active' | 'canceled' | 'past_due'
  currentPeriodStart?: string | null
  currentPeriodEnd?: string | null
  canceledAt?: string | null
  createdAt?: string
  updatedAt?: string
}

export interface PlanLimits {
  planName: string
  maxActiveAlerts: number | null
  minFrequencyMinutes: number
  priceHistoryDays: number | null
  maxSources: number | null
}
