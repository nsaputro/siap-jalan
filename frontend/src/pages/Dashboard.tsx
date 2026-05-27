import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, Luggage, Upload, Download } from 'lucide-react'
import { api } from '@/api/client'
import { useAppStore } from '@/store'
import { PackingProgress } from '@/components/PackingProgress'

type ExportOpts = { trips: boolean; activities: boolean }
type ImportState = { payload: Record<string, unknown>; tripCount: number; actCount: number }

export function Dashboard() {
  const { trips, setTrips, isLoading, setLoading, setError } = useAppStore()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [transferMsg, setTransferMsg] = useState<string | null>(null)
  const [exportDialog, setExportDialog] = useState(false)
  const [exportOpts, setExportOpts] = useState<ExportOpts>({ trips: true, activities: true })
  const [importState, setImportState] = useState<ImportState | null>(null)
  const [importOpts, setImportOpts] = useState<ExportOpts>({ trips: true, activities: true })
  const [importing, setImporting] = useState(false)

  useEffect(() => {
    setLoading(true)
    api
      .getTrips()
      .then(setTrips)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [setTrips, setLoading, setError])

  const handleExport = async () => {
    setExportDialog(false)
    try {
      await api.exportData(exportOpts)
    } catch {
      setTransferMsg('Export failed')
      setTimeout(() => setTransferMsg(null), 3000)
    }
  }

  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      const payload = JSON.parse(await file.text()) as Record<string, unknown>
      const tripCount = (payload.trips as unknown[])?.length ?? 0
      const actCount = (payload.activities as unknown[])?.length ?? 0
      setImportState({ payload, tripCount, actCount })
      setImportOpts({ trips: tripCount > 0, activities: actCount > 0 })
    } catch {
      setTransferMsg('Invalid JSON file')
      setTimeout(() => setTransferMsg(null), 3000)
    } finally {
      e.target.value = ''
    }
  }

  const handleImport = async () => {
    if (!importState) return
    setImporting(true)
    try {
      const payload = {
        ...importState.payload,
        trips: importOpts.trips ? importState.payload.trips : [],
        activities: importOpts.activities ? importState.payload.activities : [],
      }
      const result = await api.importData(payload)
      const msg = `Imported ${result.trips_imported} trip(s) and ${result.activities_imported} activity template(s)`
      setTransferMsg(result.warnings.length > 0 ? `${msg}. Warnings: ${result.warnings.join('; ')}` : msg)
      const updated = await api.getTrips()
      setTrips(updated)
      setImportState(null)
    } catch (err) {
      setTransferMsg((err as Error).message)
    } finally {
      setImporting(false)
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
            onClick={() => setExportDialog(true)}
            className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
          >
            <Download className="h-4 w-4" />
            Export
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
          >
            <Upload className="h-4 w-4" />
            Import
          </button>
          <input ref={fileInputRef} type="file" accept=".json,application/json" className="hidden" onChange={handleFileSelected} />
          <Link to="/templates" className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50">
            🎒 Activities
          </Link>
          <Link to="/trips/new" className="flex items-center gap-2 rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600">
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
              <Link key={trip.id} to={`/trips/${trip.id}`} className="block rounded-xl border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
                <div className="mb-3 flex items-start justify-between">
                  <div>
                    <h2 className="font-semibold text-gray-900">{trip.destination}</h2>
                    <p className="text-sm text-gray-400">
                      {trip.start_date} → {trip.end_date}
                      {trip.duration_days ? ` · ${trip.duration_days}d` : ''}
                    </p>
                  </div>
                </div>
                <PackingProgress packed={packed} total={allItems.length} />
              </Link>
            )
          })}
        </div>
      )}

      {/* Export dialog */}
      {exportDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setExportDialog(false)}>
          <div className="w-72 rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h2 className="mb-1 text-base font-semibold text-gray-900">Export</h2>
            <p className="mb-4 text-xs text-gray-500">Choose what to include in the export file:</p>
            <div className="mb-5 space-y-3">
              <label className="flex cursor-pointer items-center gap-2.5 text-sm text-gray-700">
                <input type="checkbox" checked={exportOpts.trips} onChange={(e) => setExportOpts((o) => ({ ...o, trips: e.target.checked }))} className="h-4 w-4" />
                Trips <span className="text-xs text-gray-400">(active &amp; future)</span>
              </label>
              <label className="flex cursor-pointer items-center gap-2.5 text-sm text-gray-700">
                <input type="checkbox" checked={exportOpts.activities} onChange={(e) => setExportOpts((o) => ({ ...o, activities: e.target.checked }))} className="h-4 w-4" />
                Custom activity templates
              </label>
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setExportDialog(false)} className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
              <button onClick={handleExport} disabled={!exportOpts.trips && !exportOpts.activities} className="rounded-lg bg-blue-500 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-600 disabled:opacity-40">
                <Download className="mr-1.5 inline h-3.5 w-3.5" />Download
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Import dialog */}
      {importState && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setImportState(null)}>
          <div className="w-72 rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h2 className="mb-1 text-base font-semibold text-gray-900">Import</h2>
            <p className="mb-4 text-xs text-gray-500">
              Found {importState.tripCount} trip(s) and {importState.actCount} activity template(s). Choose what to import:
            </p>
            <div className="mb-5 space-y-3">
              <label className={`flex items-center gap-2.5 text-sm ${importState.tripCount === 0 ? 'cursor-not-allowed opacity-40' : 'cursor-pointer text-gray-700'}`}>
                <input type="checkbox" checked={importOpts.trips} disabled={importState.tripCount === 0} onChange={(e) => setImportOpts((o) => ({ ...o, trips: e.target.checked }))} className="h-4 w-4" />
                Trips ({importState.tripCount})
              </label>
              <label className={`flex items-center gap-2.5 text-sm ${importState.actCount === 0 ? 'cursor-not-allowed opacity-40' : 'cursor-pointer text-gray-700'}`}>
                <input type="checkbox" checked={importOpts.activities} disabled={importState.actCount === 0} onChange={(e) => setImportOpts((o) => ({ ...o, activities: e.target.checked }))} className="h-4 w-4" />
                Custom activity templates ({importState.actCount})
              </label>
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setImportState(null)} className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
              <button onClick={handleImport} disabled={importing || (!importOpts.trips && !importOpts.activities)} className="rounded-lg bg-blue-500 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-600 disabled:opacity-40">
                {importing ? 'Importing…' : 'Import'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
