export default function DownloadOptions() {
  return (
    <div className="border border-gray-300 p-4 bg-white">
      <h3 className="text-xs uppercase tracking-widest text-gray-600 mb-3 font-bold">
        Download & Export
      </h3>
      <div className="space-y-2">
        <button className="w-full text-left text-xs text-orange-600 hover:text-orange-700 py-2 flex items-center gap-2 font-medium transition">
          <i>📥</i>Download Data (CSV)
        </button>
        <button className="w-full text-left text-xs text-orange-600 hover:text-orange-700 py-2 flex items-center gap-2 font-medium transition">
          <i>📄</i>Generate Narrative Report
        </button>
        <button className="w-full text-left text-xs text-orange-600 hover:text-orange-700 py-2 flex items-center gap-2 font-medium transition">
          <i>🖼️</i>Export Map Image
        </button>
      </div>
    </div>
  )
}
