import { useState, useEffect } from 'react'
import { api } from '@/api/client'
import type { ActivityTemplate } from '@/types'

interface Props {
  selected: string[]
  onChange: (slugs: string[]) => void
}

export function ActivityPicker({ selected, onChange }: Props) {
  const [activities, setActivities] = useState<ActivityTemplate[]>([])
  const [previewCount, setPreviewCount] = useState<number | null>(null)

  useEffect(() => {
    api.getActivities().then(setActivities).catch(console.error)
  }, [])

  useEffect(() => {
    if (selected.length === 0) {
      // Use a microtask to avoid setting state synchronously in effect
      Promise.resolve().then(() => setPreviewCount(null))
      return
    }
    api
      .mergeActivities(selected)
      .then((items) => setPreviewCount(items.length))
      .catch(() => setPreviewCount(null))
  }, [selected])

  const toggle = (slug: string) => {
    onChange(
      selected.includes(slug) ? selected.filter((s) => s !== slug) : [...selected, slug],
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500">Select all activities for this trip</p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {activities.map((a) => {
          const active = selected.includes(a.slug)
          return (
            <button
              key={a.slug}
              type="button"
              onClick={() => toggle(a.slug)}
              className={[
                'flex flex-col items-center gap-2 rounded-xl border-2 p-4 text-sm font-medium transition-all',
                active
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300',
              ].join(' ')}
            >
              <span className="text-3xl">{a.icon_emoji}</span>
              <span>{a.name}</span>
              {active && (
                <span className="text-xs text-blue-500">✓</span>
              )}
            </button>
          )
        })}
      </div>
      {selected.length > 0 && (
        <p className="text-sm text-gray-600">
          Selected:{' '}
          <span className="font-medium">
            {activities
              .filter((a) => selected.includes(a.slug))
              .map((a) => `${a.icon_emoji} ${a.name}`)
              .join('  ·  ')}
          </span>
          {previewCount !== null && (
            <span className="ml-2 text-gray-400">→ {previewCount} items</span>
          )}
        </p>
      )}
    </div>
  )
}
