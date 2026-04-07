/**
 * JSON:API response parsers and serializers.
 *
 * The backend returns all responses in JSON:API format:
 *   { data: { id, type, attributes: {...} } }          ← single resource
 *   { data: [...], meta: { total: N } }                ← collection
 *
 * These helpers extract the domain data, hiding the envelope from the rest
 * of the application.
 */

import type {
  CollectionResponse,
  PaginatedResult,
  ResourceObject,
  SingleResourceResponse,
} from '@/types/api'

/**
 * Extracts attributes from a single resource object, merging in the `id`.
 * Returns a plain object with camelCase keys as-is from the API.
 */
export function unwrapSingle<TAttributes extends object>(
  response: SingleResourceResponse<TAttributes>,
): TAttributes & { id: string } {
  const { id, attributes } = response.data
  return { ...attributes, id: id ?? '' }
}

/**
 * Extracts attributes from a collection response.
 * Returns `{ items, total }` where items are plain domain objects.
 */
export function unwrapCollection<TAttributes extends object>(
  response: CollectionResponse<TAttributes>,
): PaginatedResult<TAttributes & { id: string }> {
  const items = response.data.map((resource: ResourceObject<TAttributes>) => ({
    ...resource.attributes,
    id: resource.id ?? '',
  }))
  const total = response.meta?.total ?? items.length
  return { items, total }
}

/**
 * Serializes a payload into a JSON:API request body for POST/PATCH.
 *
 * @param type   - JSON:API resource type (e.g. "products")
 * @param attrs  - Attributes to send
 * @param id     - Include only for PATCH (update) requests
 */
export function wrapPayload<T extends object>(
  type: string,
  attrs: T,
  id?: string,
): { data: { type: string; id?: string; attributes: T } } {
  return {
    data: {
      type,
      ...(id !== undefined ? { id } : {}),
      attributes: attrs,
    },
  }
}
