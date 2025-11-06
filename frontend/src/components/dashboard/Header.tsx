'use client'

export default function Header() {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-orange-600 flex items-center justify-center text-white font-bold text-xs">
            S
          </div>
          <span className="text-sm uppercase tracking-widest text-gray-600 font-bold">
            Sudan Risk Dashboard
          </span>
        </div>

        <nav className="flex items-center gap-6 text-xs uppercase tracking-wide font-medium">
          <button className="text-gray-600 hover:text-gray-900">About</button>
          <button className="text-gray-600 hover:text-gray-900">Home</button>
          <button className="text-gray-600 hover:text-gray-900">Log In</button>
          <button className="bg-orange-600 text-white px-4 py-2 hover:bg-orange-700 transition-colors font-medium">
            Subscribe
          </button>
        </nav>
      </div>
    </header>
  )
}
