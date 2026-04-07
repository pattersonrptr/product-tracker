/** Source website domain types */

export interface SourceWebsite {
  id: string
  name: string
  baseUrl: string
  isActive: boolean
  createdAt?: string
  updatedAt?: string
}

export interface SourceWebsiteCreatePayload {
  name: string
  baseUrl: string
  isActive?: boolean
}

export interface SourceWebsiteUpdatePayload extends Partial<SourceWebsiteCreatePayload> {}
