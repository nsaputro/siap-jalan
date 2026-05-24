import { create } from 'zustand'
import type { Trip, ActivityTemplate } from '@/types'

interface AppState {
  trips: Trip[]
  activities: ActivityTemplate[]
  isLoading: boolean
  error: string | null

  setTrips: (trips: Trip[]) => void
  setActivities: (activities: ActivityTemplate[]) => void
  addTrip: (trip: Trip) => void
  updateTrip: (trip: Trip) => void
  removeTrip: (id: number) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useAppStore = create<AppState>((set) => ({
  trips: [],
  activities: [],
  isLoading: false,
  error: null,

  setTrips: (trips) => set({ trips }),
  setActivities: (activities) => set({ activities }),
  addTrip: (trip) => set((s) => ({ trips: [trip, ...s.trips] })),
  updateTrip: (trip) =>
    set((s) => ({ trips: s.trips.map((t) => (t.id === trip.id ? trip : t)) })),
  removeTrip: (id) => set((s) => ({ trips: s.trips.filter((t) => t.id !== id) })),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}))
