import { beforeEach, describe, expect, it } from 'vitest'
import { useAppStore } from '@/store'
import type { Trip } from '@/types'

const makeTripStub = (overrides: Partial<Trip> = {}): Trip => ({
  id: 1,
  destination: 'Bali',
  start_date: '2025-06-01',
  end_date: '2025-06-07',
  duration_days: 6,
  activities: [],
  traveller_count: 1,
  packing_lists: [],
  created_at: '',
  updated_at: '',
  ha_user_id: null,
  country: null,
  trip_type: null,
  climate_type: null,
  notes: null,
  ...overrides,
})

beforeEach(() => {
  // Reset store between tests
  useAppStore.setState({ trips: [], activities: [], isLoading: false, error: null })
})

describe('AppStore', () => {
  it('setTrips replaces the entire list', () => {
    const trips = [makeTripStub({ id: 1 }), makeTripStub({ id: 2, destination: 'Lombok' })]
    useAppStore.getState().setTrips(trips)
    expect(useAppStore.getState().trips).toHaveLength(2)
    expect(useAppStore.getState().trips[1].destination).toBe('Lombok')
  })

  it('addTrip prepends to the list', () => {
    useAppStore.getState().setTrips([makeTripStub({ id: 1, destination: 'Bali' })])
    useAppStore.getState().addTrip(makeTripStub({ id: 2, destination: 'Lombok' }))
    expect(useAppStore.getState().trips[0].destination).toBe('Lombok')
    expect(useAppStore.getState().trips).toHaveLength(2)
  })

  it('removeTrip removes by id', () => {
    useAppStore.getState().setTrips([makeTripStub({ id: 1 }), makeTripStub({ id: 2 })])
    useAppStore.getState().removeTrip(1)
    expect(useAppStore.getState().trips).toHaveLength(1)
    expect(useAppStore.getState().trips[0].id).toBe(2)
  })

  it('updateTrip replaces the matching trip', () => {
    useAppStore.getState().setTrips([makeTripStub({ id: 1, destination: 'Old' })])
    useAppStore.getState().updateTrip(makeTripStub({ id: 1, destination: 'New' }))
    expect(useAppStore.getState().trips[0].destination).toBe('New')
  })

  it('updateTrip does not affect other trips', () => {
    useAppStore.getState().setTrips([makeTripStub({ id: 1 }), makeTripStub({ id: 2, destination: 'Unchanged' })])
    useAppStore.getState().updateTrip(makeTripStub({ id: 1, destination: 'Changed' }))
    expect(useAppStore.getState().trips[1].destination).toBe('Unchanged')
  })

  it('setLoading sets isLoading flag', () => {
    useAppStore.getState().setLoading(true)
    expect(useAppStore.getState().isLoading).toBe(true)
    useAppStore.getState().setLoading(false)
    expect(useAppStore.getState().isLoading).toBe(false)
  })

  it('setError sets error message', () => {
    useAppStore.getState().setError('Something went wrong')
    expect(useAppStore.getState().error).toBe('Something went wrong')
  })

  it('setError clears error when null', () => {
    useAppStore.getState().setError('err')
    useAppStore.getState().setError(null)
    expect(useAppStore.getState().error).toBeNull()
  })
})
