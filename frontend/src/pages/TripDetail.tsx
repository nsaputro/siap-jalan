import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Trash2, Sparkles, ChevronLeft, Plus } from 'lucide-react'
import { api } from '@/api/client'
import { useAppStore } from '@/store'
import { PackingProgress } from '@/components/PackingProgress'
import type { Trip, PackingItem } from '@/types'

export function TripDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { updateTrip, removeTrip } = useAppStore()

  const [trip, setTrip] = useState<Trip | null>(null)
  const [loading, setLoading] = useState(true)
  const [suggesting, setSuggesting] = useState(false)
  const [addingTo, setAddingTo] = useState<number | null>(null) // list id
  const [newItemName, setNewItemName] = useState('')

  useEffect(() => {
    if (!id) return
    api
      .getTrip(Number(id))
      .then(setTrip)
      .catch(() => navigate('/'))
      .finally(() => setLoading(false))
  }, [id, navigate])

  if (loading || !trip) {
    return <div className="flex h-64 items-center justify-center text-gray-400">Loading…</div>
  }

  const defaultList = trip.packing_lists.find((l) => l.is_default) ?? trip.packing_lists[0]
  const allItems = defaultList?.items ?? []
  const packed = allItems.filter((i) => i.is_packed).length

  // Group items by source_activities[0] (or "General" if none)
  const grouped: Record<string, PackingItem[]> = {}
  for (const item of allItems) {
    const key = item.source_activities[0] ?? '__general__'
    if (!grouped[key]) grouped[key] = []
    grouped[key].push(item)
  }

  const toggle = async (item: PackingItem) => {
    const updated = await api.toggleItem(item.id)
    setTrip((t) =>
      t
        ? {
            ...t,
            packing_lists: t.packing_lists.map((l) => ({
              ...l,
              items: l.items.map((i) => (i.id === updated.id ? updated : i)),
            })),
          }
        : t,
    )
  }

  const deleteItem = async (itemId: number) => {
    await api.deleteItem(itemId)
    setTrip((t) =>
      t
        ? {
            ...t,
            packing_lists: t.packing_lists.map((l) => ({
              ...l,
              items: l.items.filter((i) => i.id !== itemId),
            })),
          }
        : t,
    )
  }

  const addAdHocItem = async (listId: number, activitySlug?: string) => {
    if (!newItemName.trim()) return
    const item = await api.addItem(listId, {
      name: newItemName.trim(),
      quantity: 1,
      is_essential: false,
      source_activity: activitySlug,
    })
    setNewItemName('')
    setAddingTo(null)
    setTrip((t) =>
      t
        ? {
            ...t,
            packing_lists: t.packing_lists.map((l) =>
              l.id === listId ? { ...l, items: [...l.items, item] } : l,
            ),
          }
        : t,
    )
  }

  const suggest = async () => {
    setSuggesting(true)
    try {
      const items = await api.getSuggestions(trip.id)
      setTrip((t) =>
        t
          ? {
              ...t,
              packing_lists: t.packing_lists.map((l) =>
                l.is_default ? { ...l, items: [...l.items, ...items] } : l,
              ),
            }
          : t,
      )
    } finally {
      setSuggesting(false)
    }
  }

  const deleteTrip = async () => {
    if (!confirm('Delete this trip?')) return
    await api.deleteTrip(trip.id)
    removeTrip(trip.id)
    updateTrip(trip) // refresh store
    navigate('/')
  }

  const activitySlugs = trip.activities
  const sections = [
    ...activitySlugs.filter((s) => grouped[s]),
    ...(grouped['__general__'] ? ['__general__'] : []),
  ]

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/')}
          className="mb-4 flex items-center gap-1 text-sm text-gray-400 hover:text-gray-600"
        >
          <ChevronLeft className="h-4 w-4" /> Back
        </button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{trip.destination}</h1>
            <p className="text-sm text-gray-400">
              {trip.start_date} → {trip.end_date}
              {trip.duration_days ? ` · ${trip.duration_days} days` : ''}
            </p>
            {trip.activities.length > 0 && (
              <p className="mt-1 text-sm text-gray-500">
                Activities: {trip.activities.join(', ')}
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={suggest}
              disabled={suggesting}
              className="flex items-center gap-2 rounded-lg bg-purple-500 px-3 py-2 text-sm font-medium text-white hover:bg-purple-600 disabled:opacity-50"
            >
              <Sparkles className="h-4 w-4" />
              {suggesting ? 'Thinking…' : 'AI Suggest'}
            </button>
            <button
              onClick={deleteTrip}
              className="rounded-lg border border-red-200 p-2 text-red-400 hover:bg-red-50"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Progress */}
      {defaultList && (
        <div className="mb-6">
          <PackingProgress packed={packed} total={allItems.length} />
        </div>
      )}

      {/* Per-activity sections */}
      {defaultList && (
        <div className="space-y-6">
          {sections.map((slug) => {
            const items = grouped[slug] ?? []
            const label = slug === '__general__' ? '＋ General' : slug
            return (
              <div key={slug} className="rounded-xl border border-gray-200 bg-white">
                <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
                  <h2 className="font-medium text-gray-700 capitalize">{label}</h2>
                  <button
                    onClick={() => setAddingTo(defaultList.id)}
                    className="flex items-center gap-1 text-sm text-blue-500 hover:text-blue-600"
                  >
                    <Plus className="h-3 w-3" /> Add item
                  </button>
                </div>

                <ul className="divide-y divide-gray-50">
                  {items.map((item) => (
                    <li key={item.id} className="flex items-center gap-3 px-4 py-3">
                      <input
                        type="checkbox"
                        checked={item.is_packed}
                        onChange={() => toggle(item)}
                        className="h-4 w-4 rounded border-gray-300 text-blue-500"
                      />
                      <span
                        className={[
                          'flex-1 text-sm',
                          item.is_packed ? 'text-gray-400 line-through' : 'text-gray-800',
                        ].join(' ')}
                      >
                        {item.name}
                        {item.quantity > 1 && (
                          <span className="ml-1 text-gray-400">×{item.quantity}</span>
                        )}
                        {item.is_essential && (
                          <span className="ml-2 rounded bg-amber-100 px-1 text-xs text-amber-600">
                            essential
                          </span>
                        )}
                      </span>
                      {item.added_by === 'adhoc' && (
                        <span className="text-xs text-gray-300">adhoc</span>
                      )}
                      <button
                        onClick={() => deleteItem(item.id)}
                        className="text-gray-300 hover:text-red-400"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </li>
                  ))}
                </ul>

                {/* Inline add */}
                {addingTo === defaultList.id && (
                  <div className="border-t border-gray-100 px-4 py-3 flex gap-2">
                    <input
                      autoFocus
                      value={newItemName}
                      onChange={(e) => setNewItemName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') addAdHocItem(defaultList.id, slug === '__general__' ? undefined : slug)
                        if (e.key === 'Escape') setAddingTo(null)
                      }}
                      placeholder="Item name… (Enter to add)"
                      className="flex-1 rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:border-blue-400 focus:outline-none"
                    />
                    <button
                      onClick={() => addAdHocItem(defaultList.id, slug === '__general__' ? undefined : slug)}
                      className="rounded-lg bg-blue-500 px-3 py-1.5 text-sm text-white hover:bg-blue-600"
                    >
                      Add
                    </button>
                    <button
                      onClick={() => setAddingTo(null)}
                      className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            )
          })}

          {/* Empty state */}
          {sections.length === 0 && (
            <div className="rounded-xl border-2 border-dashed border-gray-200 px-8 py-12 text-center">
              <p className="text-gray-400 mb-2">No items yet</p>
              <button
                onClick={suggest}
                className="text-sm text-purple-500 hover:underline"
              >
                Get AI suggestions →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
