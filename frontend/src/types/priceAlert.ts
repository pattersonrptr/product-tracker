/** PriceAlert domain types — mirrors backend PriceAlert entity */

export interface PriceAlert {
  id: string
  searchTerm: string
  maxPrice: number
  isActive: boolean
  frequencyMinutes: number
  lastTriggeredAt?: string
  userId: number
  searchConfigId?: number
  sourceWebsiteIds: number[]
  createdAt?: string
  updatedAt?: string
}

export interface PriceAlertCreatePayload {
  searchTerm: string
  maxPrice: number
  isActive?: boolean
  frequencyMinutes?: number
  userId: number
  sourceWebsiteIds: number[]
}

export type PriceAlertUpdatePayload = Partial<PriceAlertCreatePayload>
