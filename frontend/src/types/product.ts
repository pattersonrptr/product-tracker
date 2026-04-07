/** Product domain types — mirrors backend ProductAttributes */

export type ProductCondition = 'new' | 'used' | 'refurbished' | 'undetermined'

export interface Product {
  id: string
  url: string
  title: string
  sourceProductCode?: string
  description?: string
  imageUrls?: string
  city?: string
  state?: string
  condition: ProductCondition
  sellerName?: string
  isAvailable: boolean
  sourceWebsiteId: number
  sourceMetadata?: Record<string, unknown>
  currentPrice?: number
  createdAt?: string
  updatedAt?: string
}

export interface ProductCreatePayload {
  url: string
  title: string
  sourceProductCode?: string
  description?: string
  imageUrls?: string
  city?: string
  state?: string
  condition?: ProductCondition
  sellerName?: string
  isAvailable?: boolean
  sourceWebsiteId: number
  sourceMetadata?: Record<string, unknown>
}

export interface ProductUpdatePayload extends Partial<ProductCreatePayload> {}
