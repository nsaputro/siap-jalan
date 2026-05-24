interface Props {
  packed: number
  total: number
}

export function PackingProgress({ packed, total }: Props) {
  const pct = total === 0 ? 0 : Math.round((packed / total) * 100)

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-500">
          {packed} / {total} items packed
        </span>
        <span className="font-semibold text-gray-700">{pct}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-gray-100">
        <div
          className="h-2 rounded-full bg-blue-500 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
