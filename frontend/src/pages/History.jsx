import { useEffect, useState } from 'react'
import { apiService } from '@/services/api'

function History() {
  const [newsletters, setNewsletters] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [typeFilter, setTypeFilter] = useState('all') // all|daily|weekly|monthly|custom
  const [statusFilter, setStatusFilter] = useState('all') // all|Published|Draft|Processing
  const [query, setQuery] = useState('')

  useEffect(() => {
    const userId = localStorage.getItem('user_id')
    if (!userId) return
    ;(async () => {
      try {
        const res = await apiService.getNewsletterHistory(userId, 20)
        setNewsletters(res.newsletters || [])
      } catch (e) {
        setError('Failed to load history')
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  const handleDownloadLatest = async () => {
    try {
      const userId = localStorage.getItem('user_id')
      await apiService.downloadNewsletter(userId, 'html')
    } catch (e) {
      // no-op UI; could toast
    }
  }

  const formatType = (n) => (n.format || n.type || n.config?.format || 'unknown')
  const formatStatusClass = (s) =>
    (s || 'Published') === 'Published'
      ? 'bg-green-400/15 text-green-300 ring-1 ring-inset ring-green-400/20'
      : 'bg-yellow-400/15 text-yellow-300 ring-1 ring-inset ring-yellow-400/20'
  const formatTypeClass = (t) => 'bg-blue-400/15 text-blue-300 ring-1 ring-inset ring-blue-400/20'

  const filtered = newsletters.filter((n) => {
    const t = (formatType(n) || '').toLowerCase()
    const s = (n.status || 'Published').toLowerCase()
    const q = query.trim().toLowerCase()
    const matchesType = typeFilter === 'all' || t === typeFilter
    const matchesStatus = statusFilter === 'all' || s === statusFilter.toLowerCase()
    const matchesQuery = !q || (n.title || '').toLowerCase().includes(q)
    return matchesType && matchesStatus && matchesQuery
  })

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 text-white">
      <div className="mb-6">
        {/* <h1 className="text-2xl font-bold">Newsletter History</h1> */}
        <p className="text-white/70">Browse and manage your previously generated newsletters</p>
      </div>

      {/* Filter Bar */}
      <div className="mb-6 rounded-lg border border-white/10 bg-white/5 p-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex gap-4">
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="rounded-md border border-white/15 bg-[#0d1620] px-3 py-2 text-sm text-white shadow-[inset_0_0_0_1px_rgba(255,255,255,0.05)] focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
            >
              <option value="all">All Types</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="custom">Custom</option>
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-md border border-white/15 bg-[#0d1620] px-3 py-2 text-sm text-white shadow-[inset_0_0_0_1px_rgba(255,255,255,0.05)] focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
            >
              <option value="all">All Status</option>
              <option value="Published">Published</option>
              <option value="Draft">Draft</option>
              <option value="Processing">Processing</option>
            </select>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Search newsletters..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="rounded-md border border-white/15 bg-[#0d1620] px-3 py-2 text-sm text-white placeholder:text-white/50 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.05)] focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
            />
            <button className="rounded-md bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500">
              Search
            </button>
          </div>
        </div>
      </div>

      {/* Newsletter List */}
      <div className="space-y-4">
        {loading && (
          <div className="rounded-lg border border-white/10 bg-white/5 p-6 text-white/70">Loading history…</div>
        )}
        {error && (
          <div className="rounded-lg border border-white/10 bg-white/5 p-6 text-red-300">{error}</div>
        )}
        {!loading && !error && filtered.map((n) => (
          <div key={n.id || n.title} className="rounded-lg border border-white/10 bg-white/5 p-6">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-semibold">{n.title}</h3>
                <div className="mt-1 flex items-center gap-4 text-sm text-white/70">
                  <span>{new Date(n.generated_at || n.date || '').toLocaleDateString() || '-'}</span>
                  <span>•</span>
                  <span>{n.total_articles || n.articles || 0} articles</span>
                  <span>•</span>
                  <span className={`rounded-full px-2 py-1 text-xs font-medium ${formatTypeClass(formatType(n))}`}>
                    {formatType(n)}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`rounded-full px-2 py-1 text-xs font-medium ${formatStatusClass(n.status)}`}>
                  {n.status || 'Published'}
                </span>
                <button
                  onClick={async () => {
                    try {
                      const data = await apiService.getNewsletterById(n.id)
                      // Store for Newsletter page to preview without regenerating
                      localStorage.setItem('preview_newsletter', JSON.stringify(data))
                      window.location.href = '/newsletter'
                    } catch {}
                  }}
                  className="rounded-md border border-white/15 px-3 py-2 text-sm hover:bg-white/10 cursor-pointer"
                >
                  View
                </button>
                <button
                  onClick={() => apiService.downloadNewsletterById(n.id, 'html')}
                  className="rounded-md bg-cyan-600 px-3 py-2 text-sm font-medium text-white hover:bg-cyan-500 cursor-pointer"
                >
                  Download
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default History
