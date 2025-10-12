import { useEffect, useState } from 'react'
import { apiService } from '@/services/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

function Metric({ label, value, accent }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-4">
      <div className="text-xs uppercase tracking-wide text-white/60">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${accent || 'text-white'}`}>{value}</div>
    </div>
  )
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const userId = localStorage.getItem('user_id')
    if (!userId) return
    ;(async () => {
      try {
        const [m, a] = await Promise.all([
          apiService.getDashboardMetrics(userId),
          apiService.getDashboardAlerts(userId, 6)
        ])
        setMetrics(m)
        setAlerts(a.alerts || [])
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6 text-white">
      <div className="mb-6">
        {/* <h1 className="text-2xl font-bold">Dashboard</h1> */}
        <p className="text-white/70">A personalised overview of your AI Watchtower activity</p>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Metric label="Total Articles" value={metrics?.total_articles ?? '—'} />
        <Metric label="Sections" value={metrics?.sections ?? '—'} />
        <Metric label="High Risk Items" value={metrics?.high_risk_items ?? 0} accent="text-red-300" />
        <Metric label="Actions Required" value={metrics?.actions_required ?? 0} accent="text-yellow-300" />
      </div>

      {/* Risk Card */}
      <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-3">
        <Card className="border-white/10 bg-white/5 text-white md:col-span-2">
          <CardHeader>
            <CardTitle>Recent Alerts & Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {loading && <div className="text-white/60">Loading…</div>}
            {!loading && alerts.length === 0 && (
              <div className="text-white/60">No active alerts right now.</div>
            )}
            {alerts.map((a) => (
              <div key={a.id} className="rounded-lg border border-white/10 p-3 bg-white/5">
                <div className="flex items-center justify-between">
                  <div className="font-medium">{a.title}</div>
                  <span className={`text-xs rounded-full px-2 py-0.5 capitalize ${a.risk_level==='critical'?'bg-red-500/20 text-red-300':a.risk_level==='high'?'bg-orange-500/20 text-orange-300':a.risk_level==='medium'?'bg-yellow-500/20 text-yellow-300':'bg-green-500/20 text-green-300'}`}>{a.risk_level}</span>
                </div>
                <p className="mt-1 text-sm text-white/70">{a.description}</p>
                <div className="mt-2 text-xs text-white/60 flex gap-3">
                  {a.deadline && <span>Deadline: {new Date(a.deadline).toLocaleDateString()}</span>}
                  {typeof a.days_remaining === 'number' && <span>Days remaining: {a.days_remaining}</span>}
                </div>
              </div>
            ))}
            <div className="pt-2">
              <Button className="bg-cyan-600 text-white hover:bg-cyan-500">View all alerts</Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/10 bg-white/5 text-white">
          <CardHeader>
            <CardTitle>Your Snapshot</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center justify-between"><span>Overall Risk</span><span className="capitalize">{metrics?.risk_level ?? 'low'}</span></div>
            <div className="flex items-center justify-between"><span>Impact Score</span><span>{metrics?.impact_score ?? 0}/10</span></div>
            <div className="flex items-center justify-between"><span>Last Newsletter</span><span>{metrics?.last_newsletter_date ? new Date(metrics.last_newsletter_date).toLocaleString() : '—'}</span></div>
            <div className="pt-2">
              <Button className="w-full bg-cyan-600 text-white hover:bg-cyan-500" onClick={()=> (window.location.href='/newsletter')}>Generate New Brief</Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Personalised tips */}
      <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-3">
        <Card className="border-white/10 bg-white/5 text-white">
          <CardHeader>
            <CardTitle>Recommendations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-white/80">
            <div>• Add more sources in Profile to diversify content.</div>
            <div>• Set lower section word limits for denser briefs.</div>
            <div>• Use Custom range for end-of-month recaps.</div>
          </CardContent>
        </Card>
        <Card className="border-white/10 bg-white/5 text-white">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button className="w-full bg-cyan-600 text-white hover:bg-cyan-500" onClick={()=> (window.location.href='/history')}>View History</Button>
            <Button className="w-full bg-cyan-600 text-white hover:bg-cyan-500" onClick={()=> (window.location.href='/profile')}>Edit Preferences</Button>
          </CardContent>
        </Card>
        <Card className="border-white/10 bg-white/5 text-white">
          <CardHeader>
            <CardTitle>System</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm text-white/70">
            <div className="flex items-center justify-between"><span>Status</span><span>Online</span></div>
            <div className="flex items-center justify-between"><span>Region</span><span>Local</span></div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

