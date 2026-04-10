/** PriceAlert domain types — mirrors backend PriceAlertAttributes */

export interface PriceAlert {
  id: string
  searchTerm: string
  maxPrice: number
  isActive: boolean
  frequencyMinutes: number
  lastTriggeredAt?: string | null
  userId?: number | null
  searchConfigId?: number | null
  sourceWebsiteIds: number[]
  createdAt?: string
  updatedAt?: string
}

export interface PriceAlertCreatePayload {
  searchTerm: string
  maxPrice: number
  userId: number
  isActive?: boolean
  frequencyMinutes?: number
  sourceWebsiteIds?: number[]
}

export interface PriceAlertUpdatePayload {
  searchTerm?: string
  maxPrice?: number
  isActive?: boolean
  frequencyMinutes?: number
  sourceWebsiteIds?: number[]
}
