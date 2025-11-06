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
          <button className="text-gray-600 hover:text-orange-600 transition">About</button>
          <button className="text-gray-600 hover:text-orange-600 transition">Home</button>
          <button className="text-gray-600 hover:text-orange-600 transition">Log In</button>
          <button className="border-2 border-orange-600 text-orange-600 px-4 py-2 hover:bg-orange-50 transition font-medium">
            Subscribe
          </button>
        </nav>
      </div>
    </header>
  )
}
