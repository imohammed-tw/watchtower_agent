import { Link } from 'react-router-dom'

function LoginNavbar() {
  return (
    <nav className="border-b border-black/10 bg-gradient-to-r from-gray-950 via-gray-900 to-gray-950 text-white">
      <div className="flex w-full items-center px-6 py-4">
        {/* Logo Section - Only logo and text, no navigation */}
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
      </div>
    </nav>
  )
}

export default LoginNavbar
