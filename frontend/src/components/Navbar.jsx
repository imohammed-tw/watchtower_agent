import { Link, useLocation, useNavigate } from 'react-router-dom'
import { apiService } from '@/services/api'

function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try {
      await apiService.logout()
      navigate('/login')
    } catch (error) {
      console.error('Logout failed:', error)
      // Force logout even if API fails
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_id')
      navigate('/login')
    }
  }

  const navItems = [
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/newsletter', label: 'Newsletter' },
    { path: '/history', label: 'History' },
    { path: '/profile', label: 'Profile' }
  ]

  const isActive = (path) => location.pathname === path

  return (
    <nav className="border-b border-black/10 bg-gradient-to-r from-gray-950 via-gray-900 to-gray-950 text-white">
      <div className="flex w-full items-center px-6 py-4">
        {/* Left: Logo */}
        <Link to="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center">
            <div className="flex flex-col items-center">
              <div className="text-2xl font-extrabold tracking-tight">AI</div>
              <div className="mt-1 flex flex-col gap-0.5">
                <div className="h-0.5 w-6 bg-white/90"></div>
                <div className="h-0.5 w-6 bg-white/90"></div>
              </div>
            </div>
          </div>
          <div>
            <div className="text-lg font-semibold leading-5">Watchtower</div>
            <div className="text-xs text-white/70">Responsible AI Intelligence</div>
          </div>
        </Link>

        {/* Middle: Nav links (centered, spacious) */}
        <div className="hidden md:flex flex-1 items-center justify-center">
          <div className="flex items-center gap-14">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`text-sm font-medium tracking-wide transition-all duration-200 ${
                  isActive(item.path)
                    ? 'text-cyan-300 underline underline-offset-[12px] decoration-2 decoration-cyan-400'
                    : 'text-white/80 hover:text-white hover:underline hover:underline-offset-[12px] hover:decoration-cyan-300'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>

        {/* Right: Logout icon */}
        <div className="ml-4 flex items-center">
          <button
            onClick={handleLogout}
            title="Logout"
            className="inline-flex items-center justify-center rounded-full p-2 text-white/80 ring-1 ring-white/10 transition-all hover:bg-white/10 hover:text-white"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H7a4 4 0 0 1-4-4V7a4 4 0 0 1 4-4h2" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>

          {/* Mobile menu button (optional) */}
          <button className="ml-2 rounded-md p-2 text-white/80 hover:bg-white/10 hover:text-white md:hidden" aria-label="Menu">
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Navigation */}
      <div className="md:hidden border-t border-white/10 bg-transparent">
        <div className="px-6 py-2 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive(item.path)
                  ? 'bg-white/10 text-cyan-300'
                  : 'text-white/80 hover:bg-white/10 hover:text-white'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  )
}

export default Navbar
