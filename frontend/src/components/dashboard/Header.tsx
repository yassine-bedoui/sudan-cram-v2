'use client'

export default function Header({ darkMode, onToggleDarkMode }) {
  return (
    <header className="bg-gray-950 border-b border-gray-800 px-6 py-4 flex justify-between items-center">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-teal-500 rounded flex items-center justify-center">
          <span className="text-white font-bold">S</span>
        </div>
        <h1 className="text-xl font-bold text-white">Sudan Risk Dashboard</h1>
      </div>

      <div className="flex items-center gap-4">
        <a href="/about" className="text-gray-400 hover:text-white">About</a>
        <a href="/home" className="text-gray-400 hover:text-white">Home</a>
        <button className="text-gray-400 hover:text-white">Log In</button>
        
        {/* Dark Mode Toggle */}
        <button 
          onClick={onToggleDarkMode}
          className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700"
        >
          {darkMode ? '☀️' : '🌙'}
        </button>

        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded font-semibold">
          Subscribe
        </button>
      </div>
    </header>
  )
}
