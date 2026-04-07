/**
 * Centralized API endpoint definitions.
 * Keeps all backend URLs in one place — change here, propagates everywhere.
 */

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const API_BASE_URL = BASE

export const ENDPOINTS = {
  auth: {
    login: `${BASE}/auth/login`,
    register: `${BASE}/auth/register`,
    refresh: `${BASE}/auth/refresh-token`,
    validate: `${BASE}/auth/verify-token`,
  },
  users: {
    me: `${BASE}/users/me`,
    byUsername: (username: string) => `${BASE}/users/username/${username}`,
    list: `${BASE}/users/`,
    byId: (id: string) => `${BASE}/users/${id}`,
  },
  products: {
    list: `${BASE}/products/`,
    byId: (id: string) => `${BASE}/products/${id}`,
    byUrl: (url: string) => `${BASE}/products/url?url=${encodeURIComponent(url)}`,
  },
  priceHistory: {
    list: `${BASE}/price-histories/`,
    byId: (id: string) => `${BASE}/price-histories/${id}`,
    byProduct: (productId: string) => `${BASE}/price-histories/product/${productId}`,
    latestByProduct: (productId: string) =>
      `${BASE}/price-histories/product/${productId}/latest`,
  },
  searchConfigs: {
    list: `${BASE}/search-configs/`,
    byId: (id: string) => `${BASE}/search-configs/${id}`,
  },
  sourceWebsites: {
    list: `${BASE}/source-websites/`,
    byId: (id: string) => `${BASE}/source-websites/${id}`,
  },
} as const
