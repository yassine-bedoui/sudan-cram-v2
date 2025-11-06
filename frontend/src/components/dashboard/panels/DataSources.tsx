export default function DataSources() {
  return (
    <div className="border border-gray-300 p-4 bg-white rounded">
      <h3 className="text-xs uppercase tracking-widest text-gray-600 mb-3 font-bold">
        Data Sources
      </h3>
      <p className="text-xs text-gray-600 mb-2">
        Climate: <a href="#" className="text-orange-600 hover:text-orange-700 font-medium transition">NOAA VIIRS</a> | Conflict: <a href="#" className="text-orange-600 hover:text-orange-700 font-medium transition">ACLED</a>
      </p>
      <p className="text-xs text-gray-600">
        © Mapbox | © OpenStreetMap | Improve this map
      </p>
    </div>
  )
}
