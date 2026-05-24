import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, beforeEach } from 'vitest'
import { ActivityPicker } from '@/components/ActivityPicker'

// Mock the API client
vi.mock('@/api/client', () => ({
  api: {
    getActivities: vi.fn(),
    mergeActivities: vi.fn(),
  },
}))

import { api } from '@/api/client'

const MOCK_ACTIVITIES = [
  { id: 1, slug: 'hiking',  name: 'Hiking',  description: null, icon_emoji: '🥾', is_builtin: true, climate_types: [], items: [] },
  { id: 2, slug: 'beach',   name: 'Beach',   description: null, icon_emoji: '🏖️', is_builtin: true, climate_types: [], items: [] },
  { id: 3, slug: 'camping', name: 'Camping', description: null, icon_emoji: '🏕️', is_builtin: true, climate_types: [], items: [] },
]

beforeEach(() => {
  vi.mocked(api.getActivities).mockResolvedValue(MOCK_ACTIVITIES)
  vi.mocked(api.mergeActivities).mockResolvedValue([])
})

describe('ActivityPicker', () => {
  it('renders activity buttons after loading', async () => {
    render(<ActivityPicker selected={[]} onChange={() => {}} />)
    await waitFor(() => {
      expect(screen.getByText('Hiking')).toBeInTheDocument()
      expect(screen.getByText('Beach')).toBeInTheDocument()
      expect(screen.getByText('Camping')).toBeInTheDocument()
    })
  })

  it('shows emoji icons for each activity', async () => {
    render(<ActivityPicker selected={[]} onChange={() => {}} />)
    await waitFor(() => {
      expect(screen.getByText('🥾')).toBeInTheDocument()
      expect(screen.getByText('🏖️')).toBeInTheDocument()
    })
  })

  it('calls onChange with slug when activity is clicked', async () => {
    const onChange = vi.fn()
    render(<ActivityPicker selected={[]} onChange={onChange} />)
    await waitFor(() => screen.getByText('Hiking'))
    fireEvent.click(screen.getByText('Hiking').closest('button')!)
    expect(onChange).toHaveBeenCalledWith(['hiking'])
  })

  it('calls onChange removing slug when already-selected activity is clicked', async () => {
    const onChange = vi.fn()
    render(<ActivityPicker selected={['hiking']} onChange={onChange} />)
    await waitFor(() => screen.getByText('Hiking'))
    fireEvent.click(screen.getByText('Hiking').closest('button')!)
    expect(onChange).toHaveBeenCalledWith([])
  })

  it('shows selected activities in footer text', async () => {
    vi.mocked(api.mergeActivities).mockResolvedValue([{} as never, {} as never])
    render(<ActivityPicker selected={['hiking', 'beach']} onChange={() => {}} />)
    await waitFor(() => {
      expect(screen.getByText(/Selected:/)).toBeInTheDocument()
    })
  })

  it('shows preview item count from merge API', async () => {
    vi.mocked(api.mergeActivities).mockResolvedValue(Array(12).fill({} as never))
    render(<ActivityPicker selected={['hiking']} onChange={() => {}} />)
    await waitFor(() => {
      expect(screen.getByText(/12 items/)).toBeInTheDocument()
    })
  })

  it('shows instruction text when nothing selected', async () => {
    render(<ActivityPicker selected={[]} onChange={() => {}} />)
    await waitFor(() => screen.getByText('Hiking'))
    expect(screen.getByText(/select all activities/i)).toBeInTheDocument()
  })
})
