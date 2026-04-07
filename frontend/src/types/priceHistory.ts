/** Price history domain types */

export interface PriceHistory {
  id: string
  productId: number
  price: number
  createdAt: string
}

export interface PriceHistoryCreatePayload {
  productId: number
  price: number
}

/** Formatted entry used by charts */
export interface PriceHistoryChartPoint {
  price: number
  /** Short label shown on X axis: e.g. "01/03" */
  dateLabel: string
  /** Full datetime string shown in tooltip */
  dateTime: string
}
