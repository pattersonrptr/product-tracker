/** Search configuration domain types */

export interface SearchConfig {
  id: string
  searchTerm: string
  frequencyDays: number
  preferredTime: string
  isActive: boolean
  userId: number
  sourceWebsiteIds: number[]
  createdAt?: string
  updatedAt?: string
}

export interface SearchConfigCreatePayload {
  searchTerm: string
  frequencyDays: number
  preferredTime: string
  isActive?: boolean
  userId: number
  sourceWebsiteIds: number[]
}

export interface SearchConfigUpdatePayload extends Partial<SearchConfigCreatePayload> {}
