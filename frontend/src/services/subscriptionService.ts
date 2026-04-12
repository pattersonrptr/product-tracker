/**
 * Subscription service.
 * Manages user subscriptions and plan limits.
 */

import { apiClient } from '@/api/client'
import { ENDPOINTS } from '@/api/endpoints'
import { unwrapSingle } from '@/api/jsonapi'
import { logger } from '@/lib/logger'
import type { Subscription, PlanLimits } from '@/types/plan'

interface RawSubscriptionAttributes {
  user_id: number
  plan_id: number
  plan_name: string
  status: 'active' | 'canceled' | 'past_due'
  current_period_start?: string | null
  current_period_end?: string | null
  canceled_at?: string | null
  created_at?: string
  updated_at?: string
}

interface RawPlanLimitsAttributes {
  plan_name: string
  max_active_alerts: number | null
  min_frequency_minutes: number
  price_history_days: number | null
  max_sources: number | null
}

function toSubscription(
  raw: RawSubscriptionAttributes & { id: string },
): Subscription {
  return {
    id: raw.id,
    userId: raw.user_id,
    planId: raw.plan_id,
    planName: raw.plan_name,
    status: raw.status,
    currentPeriodStart: raw.current_period_start,
    currentPeriodEnd: raw.current_period_end,
    canceledAt: raw.canceled_at,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
  }
}

function toPlanLimits(
  raw: RawPlanLimitsAttributes & { id: string },
): PlanLimits {
  return {
    planName: raw.plan_name,
    maxActiveAlerts: raw.max_active_alerts,
    minFrequencyMinutes: raw.min_frequency_minutes,
    priceHistoryDays: raw.price_history_days,
    maxSources: raw.max_sources,
  }
}

export async function getMySubscription(): Promise<Subscription> {
  logger.debug('Fetching current subscription')
  const response = await apiClient.get(ENDPOINTS.subscriptions.me)
  const raw = unwrapSingle<RawSubscriptionAttributes>(response.data)
  return toSubscription(raw)
}

export async function subscribeToPlan(planId: string): Promise<Subscription> {
  logger.debug('Subscribing to plan', { planId })
  const response = await apiClient.post(
    ENDPOINTS.subscriptions.subscribe(planId),
  )
  const raw = unwrapSingle<RawSubscriptionAttributes>(response.data)
  return toSubscription(raw)
}

export async function cancelSubscription(): Promise<Subscription> {
  logger.debug('Canceling subscription')
  const response = await apiClient.post(ENDPOINTS.subscriptions.cancel)
  const raw = unwrapSingle<RawSubscriptionAttributes>(response.data)
  return toSubscription(raw)
}

export async function getMyLimits(): Promise<PlanLimits> {
  logger.debug('Fetching plan limits')
  const response = await apiClient.get(ENDPOINTS.subscriptions.limits)
  const raw = unwrapSingle<RawPlanLimitsAttributes>(response.data)
  return toPlanLimits(raw)
}
