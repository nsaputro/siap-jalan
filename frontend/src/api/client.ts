const BASE_URL = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  // Trips
  getTrips: () => request<import('@/types').Trip[]>('/trips'),
  getTrip: (id: number) => request<import('@/types').Trip>(`/trips/${id}`),
  createTrip: (data: import('@/types').TripFormValues) =>
    request<import('@/types').Trip>('/trips', { method: 'POST', body: JSON.stringify(data) }),
  updateTrip: (id: number, data: Partial<import('@/types').TripFormValues>) =>
    request<import('@/types').Trip>(`/trips/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteTrip: (id: number) => request<void>(`/trips/${id}`, { method: 'DELETE' }),
  getTripWeather: (id: number) => request<unknown>(`/trips/${id}/weather`),

  // Packing items
  getItems: (listId: number) =>
    request<import('@/types').PackingItem[]>(`/lists/${listId}/items`),
  addItem: (listId: number, data: import('@/types').PackingItemFormValues) =>
    request<import('@/types').PackingItem>(`/lists/${listId}/items`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateItem: (id: number, data: Partial<import('@/types').PackingItem>) =>
    request<import('@/types').PackingItem>(`/items/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteItem: (id: number) => request<void>(`/items/${id}`, { method: 'DELETE' }),
  toggleItem: (id: number) =>
    request<import('@/types').PackingItem>(`/items/${id}/toggle`, { method: 'POST' }),
  promoteItem: (id: number) =>
    request<import('@/types').PackingItem>(`/items/${id}/promote`, { method: 'POST' }),

  // Activity templates
  getActivities: () => request<import('@/types').ActivityTemplate[]>('/activities'),
  getActivity: (slug: string) =>
    request<import('@/types').ActivityTemplate>(`/activities/${slug}`),
  mergeActivities: (slugs: string[]) =>
    request<import('@/types').MergedItem[]>('/activities/merge', {
      method: 'POST',
      body: JSON.stringify({ activity_slugs: slugs }),
    }),

  // AI suggestions
  getSuggestions: (tripId: number) =>
    request<import('@/types').PackingItem[]>(`/trips/${tripId}/suggest`, { method: 'POST' }),
}
