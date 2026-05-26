import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ChevronLeft, Trash2, Plus } from 'lucide-react'
import { api } from '@/api/client'
import type { ActivityTemplate, ActivityTemplateItem, PropagationSummary } from '@/types'

export function TemplateDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [tmpl, setTmpl] = useState<ActivityTemplate | null>(null)
  const [loading, setLoading] = useState(true)
  const [cloning, setCloning] = useState(false)
  const [saveStatus, setSaveStatus] = useState<string>('')
  const [newItemName, setNewItemName] = useState('')
  const [addingItem, setAddingItem] = useState(false)

  const [editName, setEditName] = useState('')
  const [editEmoji, setEditEmoji] = useState('')

  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!id) return
    api
      .getActivities()
      .then(async (list) => {
        const found = list.find((a) => a.id === Number(id))
        if (!found) { navigate('/templates'); return }

        if (found.is_builtin) {
          // If the user already has a personal copy with the same name, redirect there.
          const existing = list.find((a) => !a.is_builtin && a.name === found.name)
          if (existing) {
            navigate(`/templates/${existing.id}`, { replace: true })
            return
          }
          // Auto-clone the built-in as a personal copy (same name + emoji).
          setCloning(true)
          try {
            const clone = await api.cloneActivity(found.slug, { name: found.name })
            navigate(`/templates/${clone.id}`, { replace: true })
          } catch {
            navigate('/templates')
          }
          return
        }

        setTmpl(found)
        setEditName(found.name)
        setEditEmoji(found.icon_emoji)
      })
      .catch(() => navigate('/templates'))
      .finally(() => { setLoading(false); setCloning(false) })
  }, [id, navigate])

  const showSaveStatus = (summary: PropagationSummary) => {
    const updated = summary.trips_updated ?? 0
    setSaveStatus(
      updated > 0
        ? `Saved — propagated to ${updated} trip${updated !== 1 ? 's' : ''}`
        : 'Saved',
    )
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
    saveTimerRef.current = setTimeout(() => setSaveStatus(''), 3000)
  }

  const saveInfo = async () => {
    if (!tmpl) return
    const name = editName.trim()
    const emoji = editEmoji.trim() || tmpl.icon_emoji
    if (name === tmpl.name && emoji === tmpl.icon_emoji) return
    if (!name) return
    try {
      const result = await api.updateActivity(tmpl.id, { name, icon_emoji: emoji })
      setTmpl(result.template)
      showSaveStatus(result.propagation_summary)
    } catch (e: unknown) {
      setSaveStatus('Save failed: ' + (e instanceof Error ? e.message : String(e)))
    }
  }

  const toggleEssential = async (item: ActivityTemplateItem) => {
    if (!tmpl) return
    try {
      const updated = await api.updateActivityItem(tmpl.id, item.id, {
        is_essential: !item.is_essential,
      })
      setTmpl((t) =>
        t ? { ...t, items: t.items.map((i) => (i.id === updated.id ? updated : i)) } : t,
      )
    } catch { /* silent */ }
  }

  const deleteItem = async (itemId: number) => {
    if (!tmpl) return
    try {
      await api.deleteActivityItem(tmpl.id, itemId)
      setTmpl((t) => (t ? { ...t, items: t.items.filter((i) => i.id !== itemId) } : t))
    } catch { /* silent */ }
  }

  const addItem = async () => {
    const name = newItemName.trim()
    if (!name || !tmpl) return
    setAddingItem(true)
    try {
      const item = await api.addActivityItem(tmpl.id, {
        name,
        quantity: 1,
        is_essential: false,
        priority: 0,
        gender_filter: 'all',
      })
      setTmpl((t) => (t ? { ...t, items: [...t.items, item] } : t))
      setNewItemName('')
    } catch { /* silent */ }
    finally { setAddingItem(false) }
  }

  if (loading || cloning || !tmpl) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-2 text-gray-400">
        <div>{cloning ? 'Creating your personal copy…' : 'Loading…'}</div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      {/* ── Header ── */}
      <div className="mb-6 flex items-center gap-3">
        <Link
          to="/templates"
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
        >
          <ChevronLeft className="h-4 w-4" />
          Activities
        </Link>
        <span className="text-gray-300">/</span>
        <span className="text-sm font-medium text-gray-700">
          {tmpl.icon_emoji} {tmpl.name}
        </span>
      </div>

      {/* ── Template info card ── */}
      <div className="mb-5 rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
        <div className="flex items-center gap-2 border-b border-gray-100 bg-gray-50 px-4 py-3">
          <span className="text-xs font-semibold uppercase tracking-widest text-gray-400">
            Template Info
          </span>
          <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">
            personal copy
          </span>
          <span className="ml-auto text-xs text-gray-400">changes only affect your trips</span>
        </div>

        <div className="divide-y divide-gray-100">
          <div className="flex items-center gap-3 px-4 py-3">
            <label className="w-16 flex-shrink-0 text-xs text-gray-400">Name</label>
            <input
              className="flex-1 bg-transparent text-sm text-gray-900 outline-none focus:border-b focus:border-blue-400"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              onBlur={saveInfo}
              onKeyDown={(e) => e.key === 'Enter' && (e.currentTarget as HTMLInputElement).blur()}
            />
          </div>
          <div className="flex items-center gap-3 px-4 py-3">
            <label className="w-16 flex-shrink-0 text-xs text-gray-400">Emoji</label>
            <input
              className="w-16 bg-transparent text-sm text-gray-900 outline-none focus:border-b focus:border-blue-400"
              value={editEmoji}
              onChange={(e) => setEditEmoji(e.target.value)}
              onBlur={saveInfo}
              onKeyDown={(e) => e.key === 'Enter' && (e.currentTarget as HTMLInputElement).blur()}
            />
          </div>
        </div>
      </div>

      {saveStatus && (
        <p className="mb-3 text-center text-xs text-gray-400">{saveStatus}</p>
      )}

      {/* ── Items card ── */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
        <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50 px-4 py-3">
          <span className="text-xs font-semibold uppercase tracking-widest text-gray-400">
            Items
          </span>
          <span className="text-xs text-gray-400">{tmpl.items.length}</span>
        </div>

        {tmpl.items.length === 0 && (
          <p className="px-4 py-6 text-center text-sm text-gray-400">
            No items yet — add one below.
          </p>
        )}

        <div className="divide-y divide-gray-100">
          {tmpl.items.map((item) => (
            <div key={item.id} className="flex items-center gap-3 px-4 py-3">
              <button
                onClick={() => toggleEssential(item)}
                title={item.is_essential ? 'Essential' : 'Mark essential'}
                className={`flex-shrink-0 text-lg transition-opacity hover:opacity-70 ${
                  item.is_essential ? 'opacity-100' : 'opacity-25'
                }`}
              >
                ★
              </button>

              <span className="flex-1 text-sm text-gray-900">{item.name}</span>

              {item.quantity > 1 && (
                <span className="text-xs text-gray-400">×{item.quantity}</span>
              )}

              <button
                onClick={() => deleteItem(item.id)}
                className="flex-shrink-0 rounded p-1 text-gray-300 hover:text-red-400"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-2 border-t border-gray-100 px-4 py-3">
          <Plus className="h-4 w-4 flex-shrink-0 text-gray-400" />
          <input
            className="flex-1 bg-transparent text-sm text-gray-700 outline-none placeholder-gray-300"
            placeholder="Add item (Enter to save)…"
            value={newItemName}
            onChange={(e) => setNewItemName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !addingItem) addItem()
            }}
            disabled={addingItem}
          />
        </div>
      </div>
    </div>
  )
}
