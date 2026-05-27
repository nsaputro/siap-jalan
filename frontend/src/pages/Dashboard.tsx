import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Luggage, Upload, Download } from 'lucide-react'
import { api } from '@/api/client'
import { useAppStore } from '@/store'
import { PackingProgress } from '@/components/PackingProgress'

export function Dashboard() {
  const { trips, setTrips, isLoading, setLoading, setError } = useAppStore()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [transferMsg, setTransferMsg] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    api
      .getTrips()
      .then(setTrips)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [setTrips, setLoading, setError])

  const handleExport = async () => {
    try {
      await api.exportData()
    } catch {
      setTransferMsg('Export failed')
      setTimeout(() => setTransferMsg(null), 3000)
    }
  }

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const text = await file.text()
      const payload = JSON.parse(text)
      const result = await api.importData(payload)
      const msg = `Imported ${result.trips_imported} trip(s) and ${result.activities_imported} activity template(s)`
      setTransferMsg(result.warnings.length > 0 ? `${msg}. Warnings: ${result.warnings.join('; ')}` : msg)
      const trips = await api.getTrips()
      setTrips(trips)
    } catch (err) {
      setTransferMsg((err as Error).message)
    } finally {
      e.target.value = ''
      setTimeout(() => setTransferMsg(null), 5000)
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center text-gray-400">Loading…</div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Luggage className="h-7 w-7 text-blue-500" />
          <h1 className="text-2xl font-bold text-gray-900">My Trips</h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExport}
            className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
            title="Export active & future trips + custom activities as JSON"
          >
            <Download className="h-4 w-4" />
            Export
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
            title="Import trips and activities from a SiapJalan JSON export"
          >
            <Upload className="h-4 w-4" />
            Import
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json,application/json"
            className="hidden"
            onChange={handleImport}
          />
          <Link
            to="/templates"
            className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
          >
            🎒 Activities
          </Link>
          <Link
            to="/trips/new"
            className="flex items-center gap-2 rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600"
          >
            <Plus className="h-4 w-4" />
            New Trip
          </Link>
        </div>
      </div>
      {transferMsg && (
        <p className="mb-4 rounded-lg bg-blue-50 px-4 py-2 text-sm text-blue-700">{transferMsg}</p>
      )}

      {trips.length === 0 ? (
        <div className="rounded-xl border-2 border-dashed border-gray-200 px-8 py-16 text-center">
          <Luggage className="mx-auto mb-4 h-12 w-12 text-gray-300" />
          <p className="mb-1 text-gray-500">No trips yet</p>
          <Link to="/trips/new" className="text-sm text-blue-500 hover:underline">
            Create your first trip →
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {trips.map((trip) => {
            const allItems = trip.packing_lists.flatMap((l) => l.items)
            const packed = allItems.filter((i) => i.is_packed).length

            return (
              <Link
                key={trip.id}
                to={`/trips/${trip.id}`}
                className="block rounded-xl border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="mb-3 flex items-start justify-between">
                  <div>
                    <h2 className="font-semibold text-gray-900">{trip.destination}</h2>
                    <p className="text-sm text-gray-400">
                      {trip.start_date} → {trip.end_date}
                      {trip.duration_days ? ` · ${trip.duration_days}d` : ''}
                    </p>
                  </div>
                  <div className="flex gap-1">
                    {trip.activities.slice(0, 4).map((slug) => (
                      <span key={slug} className="text-lg" title={slug}>
                        {/* icon rendered by ActivityPicker data */}
                      </span>
                    ))}
                  </div>
                </div>
                <PackingProgress packed={packed} total={allItems.length} />
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
