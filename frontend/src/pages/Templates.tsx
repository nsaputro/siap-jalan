import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Copy, Pencil, Trash2, Luggage } from 'lucide-react'
import { api } from '@/api/client'
import type { ActivityTemplate } from '@/types'

export function Templates() {
  const navigate = useNavigate()
  const [activities, setActivities] = useState<ActivityTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Clone dialog state
  const [cloneSource, setCloneSource] = useState<ActivityTemplate | null>(null)
  const [cloneName, setCloneName] = useState('')
  const [cloneEmoji, setCloneEmoji] = useState('')
  const [cloning, setCloning] = useState(false)
  const [cloneError, setCloneError] = useState<string | null>(null)

  // New activity dialog state
  const [showNewDialog, setShowNewDialog] = useState(false)
  const [newName, setNewName] = useState('')
  const [newEmoji, setNewEmoji] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  useEffect(() => {
    api
      .getActivities()
      .then(setActivities)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const builtins = activities.filter((a) => a.is_builtin)
  const mine = activities.filter((a) => !a.is_builtin)

  const openClone = (tmpl: ActivityTemplate) => {
    setCloneSource(tmpl)
    setCloneName(`My ${tmpl.name}`)
    setCloneEmoji('')
    setCloneError(null)
  }

  const handleClone = async () => {
    if (!cloneSource || !cloneName.trim()) return
    setCloning(true)
    setCloneError(null)
    try {
      const created = await api.cloneActivity(cloneSource.slug, {
        name: cloneName.trim(),
        icon_emoji: cloneEmoji.trim() || undefined,
      })
      setActivities((prev) => [...prev, created])
      setCloneSource(null)
    } catch (e: unknown) {
      setCloneError(e instanceof Error ? e.message : 'Clone failed')
    } finally {
      setCloning(false)
    }
  }

  const handleCreate = async () => {
    if (!newName.trim()) return
    setCreating(true)
    setCreateError(null)
    try {
      const created = await api.createActivity({
        name: newName.trim(),
        icon_emoji: newEmoji.trim() || '🎒',
        items: [],
      })
      setActivities((prev) => [...prev, created])
      setShowNewDialog(false)
      navigate(`/templates/${created.id}`)
    } catch (e: unknown) {
      setCreateError(e instanceof Error ? e.message : 'Create failed')
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (tmpl: ActivityTemplate) => {
    if (!confirm(`Delete "${tmpl.name}"? This cannot be undone.`)) return
    try {
      await api.deleteActivity(tmpl.id)
      setActivities((prev) => prev.filter((a) => a.id !== tmpl.id))
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : 'Delete failed')
    }
  }

  if (loading) {
    return <div className="flex h-64 items-center justify-center text-gray-400">Loading…</div>
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      {/* ── Header ── */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🎒</span>
          <h1 className="text-2xl font-bold text-gray-900">Activity Templates</h1>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/"
            className="flex items-center gap-1 rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            <Luggage className="h-4 w-4" />
            Trips
          </Link>
          <button
            onClick={() => { setShowNewDialog(true); setNewName(''); setNewEmoji(''); setCreateError(null) }}
            className="flex items-center gap-2 rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600"
          >
            <Plus className="h-4 w-4" />
            New Activity
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div>
      )}

      {/* ── Built-in templates ── */}
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-widest text-gray-400">
        Built-in ({builtins.length})
      </h2>
      <div className="mb-6 space-y-2">
        {builtins.map((tmpl) => (
          <div
            key={tmpl.id}
            className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm"
          >
            <span className="text-2xl">{tmpl.icon_emoji}</span>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-gray-900">{tmpl.name}</p>
              <p className="text-xs text-gray-400">{tmpl.items.length} items · built-in</p>
            </div>
            <div className="flex items-center gap-2">
              <Link
                to={`/templates/${tmpl.id}`}
                className="flex items-center gap-1 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50"
              >
                <Pencil className="h-3.5 w-3.5" />
                Edit
              </Link>
              <button
                onClick={() => openClone(tmpl)}
                className="flex items-center gap-1 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50"
              >
                <Copy className="h-3.5 w-3.5" />
                Clone
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* ── My activities ── */}
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-widest text-gray-400">
        My Activities ({mine.length})
      </h2>
      {mine.length === 0 ? (
        <div className="rounded-xl border-2 border-dashed border-gray-200 px-8 py-10 text-center">
          <p className="mb-1 text-sm text-gray-400">No custom activities yet</p>
          <p className="text-xs text-gray-400">Edit a built-in to personalise it, or create a new one from scratch.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {mine.map((tmpl) => (
            <div
              key={tmpl.id}
              className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm"
            >
              <span className="text-2xl">{tmpl.icon_emoji}</span>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-900">{tmpl.name}</p>
                <p className="text-xs text-gray-400">{tmpl.items.length} items · custom</p>
              </div>
              <div className="flex items-center gap-2">
                <Link
                  to={`/templates/${tmpl.id}`}
                  className="flex items-center gap-1 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-50"
                >
                  <Pencil className="h-3.5 w-3.5" />
                  Edit
                </Link>
                <button
                  onClick={() => handleDelete(tmpl)}
                  className="flex items-center gap-1 rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-500 hover:bg-red-50"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Clone dialog ── */}
      {cloneSource && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl">
            <h2 className="mb-4 text-base font-bold text-gray-900">
              Clone "{cloneSource.name}"
            </h2>
            {cloneError && (
              <p className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">{cloneError}</p>
            )}
            <div className="mb-3">
              <label className="mb-1 block text-xs font-medium text-gray-500">New Name *</label>
              <input
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
                value={cloneName}
                onChange={(e) => setCloneName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleClone()}
                autoFocus
              />
            </div>
            <div className="mb-5">
              <label className="mb-1 block text-xs font-medium text-gray-500">
                Emoji (optional — leave blank to inherit)
              </label>
              <input
                className="w-20 rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
                value={cloneEmoji}
                onChange={(e) => setCloneEmoji(e.target.value)}
                placeholder={cloneSource.icon_emoji}
              />
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setCloneSource(null)}
                className="rounded-lg border border-gray-200 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleClone}
                disabled={cloning || !cloneName.trim()}
                className="rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600 disabled:opacity-50"
              >
                {cloning ? 'Cloning…' : 'Clone'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── New activity dialog ── */}
      {showNewDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl">
            <h2 className="mb-4 text-base font-bold text-gray-900">New Activity Template</h2>
            {createError && (
              <p className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">{createError}</p>
            )}
            <div className="mb-3 flex gap-3">
              <div className="flex-1">
                <label className="mb-1 block text-xs font-medium text-gray-500">Name *</label>
                <input
                  className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                  placeholder="e.g. Yoga Retreat"
                  autoFocus
                />
              </div>
              <div className="w-20">
                <label className="mb-1 block text-xs font-medium text-gray-500">Emoji</label>
                <input
                  className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
                  value={newEmoji}
                  onChange={(e) => setNewEmoji(e.target.value)}
                  placeholder="🎒"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowNewDialog(false)}
                className="rounded-lg border border-gray-200 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={creating || !newName.trim()}
                className="rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600 disabled:opacity-50"
              >
                {creating ? 'Creating…' : 'Create & Edit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
