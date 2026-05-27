import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { api } from '@/api/client'
import { useAppStore } from '@/store'
import { ActivityPicker } from '@/components/ActivityPicker'
import type { TripType } from '@/types'

interface FormValues {
  destination: string
  country?: string
  start_date: string
  end_date: string
  trip_type?: TripType
  notes?: string
  traveller_count: number
}

export function NewTrip() {
  const navigate = useNavigate()
  const addTrip = useAppStore((s) => s.addTrip)
  const [activities, setActivities] = useState<string[]>(['essentials', 'toiletries'])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ defaultValues: { traveller_count: 1 } })

  const onSubmit = async (values: FormValues) => {
    setSaving(true)
    setError(null)
    try {
      const trip = await api.createTrip({ ...values, activities })
      addTrip(trip)
      navigate(`/trips/${trip.id}`)
    } catch (e) {
      setError((e as Error).message)
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">New Trip</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic info */}
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-4">
          <h2 className="font-semibold text-gray-800">Trip Details</h2>

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Destination *
              </label>
              <input
                {...register('destination')}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none"
                placeholder="e.g. Bali, Indonesia"
              />
              {errors.destination && (
                <p className="mt-1 text-xs text-red-500">{errors.destination.message}</p>
              )}
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Start Date *</label>
              <input
                type="date"
                {...register('start_date')}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none"
              />
              {errors.start_date && (
                <p className="mt-1 text-xs text-red-500">{errors.start_date.message}</p>
              )}
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">End Date *</label>
              <input
                type="date"
                {...register('end_date')}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none"
              />
              {errors.end_date && (
                <p className="mt-1 text-xs text-red-500">{errors.end_date.message}</p>
              )}
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Trip Type</label>
              <select
                {...register('trip_type')}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none"
              >
                <option value="">Select…</option>
                {(['leisure', 'business', 'adventure', 'family'] as TripType[]).map((t) => (
                  <option key={t} value={t}>
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Travellers</label>
              <input
                type="number"
                min={1}
                {...register('traveller_count')}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none"
              />
            </div>

            <div className="col-span-2">
              <label className="mb-1 block text-sm font-medium text-gray-700">Notes</label>
              <textarea
                {...register('notes')}
                rows={2}
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none"
                placeholder="Any special requirements…"
              />
            </div>
          </div>
        </div>

        {/* Activity picker */}
        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="mb-4 font-semibold text-gray-800">Activities</h2>
          <ActivityPicker selected={activities} onChange={setActivities} />
        </div>

        {error && (
          <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p>
        )}

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-blue-500 px-6 py-2 text-sm font-medium text-white hover:bg-blue-600 disabled:opacity-50"
          >
            {saving ? 'Creating…' : 'Create Trip'}
          </button>
        </div>
      </form>
    </div>
  )
}
