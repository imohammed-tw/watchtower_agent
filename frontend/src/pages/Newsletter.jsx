import { useMemo, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Separator } from '@/components/ui/separator'
import { Calendar } from '@/components/ui/calendar'
import { Badge } from '@/components/ui/badge'
import { Separator as UISeparator } from '@/components/ui/separator'
import { Download, FileText, Loader2, CheckCircle, AlertCircle, ExternalLink } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { apiService } from '@/services/api'

const ALL_SECTIONS = [
  'Executive Summary',
  'Regulatory & Compliance Watch',
  'Security & Risk Alerts',
  'Technical Breakthroughs',
  'Market Intelligence',
  'Industry Applications',
  'Forward Intelligence',
]

// Adjusted timings so progress feels even; last step no longer dominates
const LOADING_STEPS = [
  { id: 'preferences', label: 'Loading user preferences...', duration: 1600 },
  { id: 'content', label: 'Gathering content from sources...', duration: 2000 },
  { id: 'analysis', label: 'Analyzing and categorizing content...', duration: 2400 },
  { id: 'sections', label: 'Generating newsletter sections...', duration: 2000 },
  { id: 'formatting', label: 'Formatting and finalizing...', duration: 1100 }
]

function Newsletter() {
  const [format, setFormat] = useState('weekly')
  const [template, setTemplate] = useState('professional')
  const [selected, setSelected] = useState(new Set(['Executive Summary', 'Technical Breakthroughs']))
  const [customDates, setCustomDates] = useState({ from: undefined, to: undefined })
  const [limits, setLimits] = useState({ maxArticles: 20, maxTotalWords: undefined, maxSectionWords: undefined })
  const [isLoading, setIsLoading] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [result, setResult] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [error, setError] = useState(null)
  const [showResults, setShowResults] = useState(false)
  const [activeTab, setActiveTab] = useState('newsletter') // 'newsletter' | 'alerts'
  // If navigated from History “View”, load preview payload
  useState(() => {
    try {
      const preview = localStorage.getItem('preview_newsletter')
      if (preview) {
        const parsed = JSON.parse(preview)
        setResult({ newsletter: parsed })
        setShowResults(true)
      }
    } catch {}
  })

  const isCustom = format === 'custom'
  const selectedCount = selected.size

  const toggleSection = (name) => {
    const next = new Set(selected)
    if (next.has(name)) next.delete(name)
    else next.add(name)
    setSelected(next)
  }

  const generate = async () => {
    setIsLoading(true)
    setError(null)
    setResult(null)
    setCurrentStep(0)
    setShowResults(false)
    
    try {
      // Get userId from localStorage (set during login)
      const userId = localStorage.getItem('user_id')
      if (!userId) {
        throw new Error('User not authenticated')
      }

      // Simulate loading steps
      for (let i = 0; i < LOADING_STEPS.length; i++) {
        setCurrentStep(i)
        await new Promise(resolve => setTimeout(resolve, LOADING_STEPS[i].duration))
      }
      
      const config = {
        format,
        sections: Array.from(selected),
        template,
        customDates: isCustom ? customDates : undefined,
        maxArticles: limits.maxArticles,
        maxTotalWords: limits.maxTotalWords,
        maxSectionWords: limits.maxSectionWords,
      }
      
      const response = await apiService.generateNewsletter(userId, config)
      setResult(response)
      setShowResults(true)

      // Fetch alerts for this user to populate Alerts & Actions tab
      try {
        const alertsResp = await apiService.getUserAlerts(userId, 50)
        setAlerts(alertsResp?.alerts || [])
      } catch (e) {
        console.warn('Failed to fetch alerts:', e)
      }
    } catch (err) {
      setError(err.message || 'Failed to generate newsletter')
    } finally {
      setIsLoading(false)
    }
  }

  const downloadNewsletter = async (format = 'html') => {
    try {
      const userId = localStorage.getItem('user_id')
      const response = await apiService.downloadNewsletter(userId, format)
      
      // Create download link
      const blob = new Blob([response], { type: 'text/html' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `newsletter-${Date.now()}.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Download failed:', err)
    }
  }

  const formatLabel = useMemo(() => ({
    daily: 'Daily',
    weekly: 'Weekly',
    monthly: 'Monthly',
    custom: 'Custom',
  })[format], [format])

  // Sanitize/prepare newsletter markdown so UI looks clean
  const preprocessMarkdown = (raw) => {
    if (!raw || typeof raw !== 'string') return raw
    let md = raw
    // Remove Newsletter Configuration block
    md = md.replace(/##?\s*Newsletter Configuration:[\s\S]*?(?=\n## |\n### |$)/gi, '')
    // Remove leading cover/title meta lines (AI Watchtower header, generated timestamp, target length)
    md = md.replace(/AI Watchtower[\s\S]*?Target Length:[^\n]*\n/gi, '')
    // Remove blank list items like "-" or "*"
    md = md.replace(/^\s*[-*]\s*$/gm, '')
    // Collapse duplicate consecutive headers (e.g., same header text repeated with any level)
    const lines = md.split(/\n/)
    let out = []
    let prevHeader = ''
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      const m = line.match(/^#{2,4}\s*(.+)\s*$/)
      if (m) {
        const text = m[1].trim().toLowerCase()
        if (text === prevHeader) {
          continue
        }
        prevHeader = text
      } else if (line.trim().length > 0) {
        prevHeader = ''
      }
      out.push(line)
    }
    md = out.join('\n')
    return md.trim()
  }

  // Full-page slider: two panels side-by-side; translate container to show active
  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6 text-white overflow-hidden">
      <div className="mb-6">
        {/* <h1 className="text-2xl font-bold">Newsletter Generator</h1> */}
        {/* <p className="text-white/70">Configure type, sections, and generate using the backend agents</p> */}
      </div>

      {/* Slider viewport */}
      <div className={`relative w-full overflow-hidden ${isLoading ? 'blur-[2px] pointer-events-none select-none' : ''}`}>
        <div className="flex w-[200%] transition-transform duration-500 ease-in-out animate__animated" style={{ transform: showResults ? 'translateX(-50%)' : 'translateX(0%)' }}>
          {/* Panel 1: Configuration (takes 50% width) */}
          <div className="w-1/2 pr-6">
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              {/* Left: Configuration */}
              <Card className="border-white/10 bg-white/5 text-white lg:col-span-2">
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Type & Template */}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="block text-sm font-medium pb-2">Newsletter Type</label>
                <Select value={format} onValueChange={setFormat}>
                  <SelectTrigger className="w-full border-white/15 bg-white/5 text-white">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-900 text-white">
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                    <SelectItem value="monthly">Monthly</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="block text-sm font-medium pb-2">Template</label>
                <Select value={template} onValueChange={setTemplate}>
                  <SelectTrigger className="w-full border-white/15 bg-white/5 text-white">
                    <SelectValue placeholder="Select template" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-900 text-white">
                    <SelectItem value="professional">Professional</SelectItem>
                    <SelectItem value="executive">Executive</SelectItem>
                    <SelectItem value="technical">Technical</SelectItem>
                    <SelectItem value="newsletter">Newsletter</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            

            <Separator className="bg-white/10" />

            {/* Sections */}
            <div className="space-y-3">
              <div>
                <div className="text-sm font-medium">Sections ({selectedCount})</div>
                <div className="text-xs text-white/60">Choose what all sections you want in your rewind</div>
              </div>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                {ALL_SECTIONS.map((name) => (
                  <label key={name} className="flex items-center gap-3 rounded-md px-2 py-2 transition hover:bg-white/5">
                    <Checkbox
                      checked={selected.has(name)}
                      onCheckedChange={() => toggleSection(name)}
                      className="border-white/30 data-[state=checked]:bg-cyan-500 data-[state=checked]:border-cyan-500"
                    />
                    <span className="text-sm text-white/90">{name}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Custom date range */}
            {isCustom && (
              <div className="space-y-3">
                <div className="text-sm">Date Range</div>
                <div className="rounded-lg border border-white/10 bg-white/5 p-3">
                  <Calendar
                    mode="range"
                    selected={customDates}
                    onSelect={setCustomDates}
                    className="rounded-md border-0 bg-transparent text-white [&_.rdp-day]:text-white [&_.rdp-button]:hover:bg-white/10"
                  />
                </div>
              </div>
            )}

            <Separator className="bg-white/10" />

            {/* Optional Configuration */}
            <div className="space-y-3">
              <div className="text-sm text-white/70 font-medium">Advanced Configuration (Optional)</div>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <label className="block text-sm font-medium pb-2">Max Articles</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={limits.maxArticles ?? ''}
                    onChange={(e)=> setLimits(prev=>({ ...prev, maxArticles: e.target.value ? Number(e.target.value) : undefined }))}
                    className="w-full rounded-md border border-white/15 bg-white/5 px-3 py-2 text-white placeholder:text-white/50"
                    placeholder="20"
                  />
                </div>
                <div className="space-y-2">
                  <label className="block text-sm font-medium pb-2">Max Total Words</label>
                  <input
                    type="number"
                    min="100"
                    max="10000"
                    value={limits.maxTotalWords ?? ''}
                    onChange={(e)=> setLimits(prev=>({ ...prev, maxTotalWords: e.target.value ? Number(e.target.value) : undefined }))}
                    className="w-full rounded-md border border-white/15 bg-white/5 px-3 py-2 text-white placeholder:text-white/50"
                    placeholder="Auto"
                  />
                </div>
                <div className="space-y-2">
                  <label className="block text-sm font-medium pb-2">Max Section Words</label>
                  <input
                    type="number"
                    min="50"
                    max="2000"
                    value={limits.maxSectionWords ?? ''}
                    onChange={(e)=> setLimits(prev=>({ ...prev, maxSectionWords: e.target.value ? Number(e.target.value) : undefined }))}
                    className="w-full rounded-md border border-white/15 bg-white/5 px-3 py-2 text-white placeholder:text-white/50"
                    placeholder="Auto"
                  />
                </div>
              </div>
            </div>

          </CardContent>
              </Card>

              {/* Right: Actions / Preview */}
              <div className="space-y-6">
          <Card className="border-white/10 bg-white/5 text-white">
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-white/80">
              <div className="flex justify-between"><span>Type</span><span>{formatLabel}</span></div>
              <div className="flex justify-between"><span>Template</span><span className="capitalize">{template}</span></div>
              <div className="flex justify-between"><span>Sections</span><span>{selectedCount}</span></div>
              {isCustom && (
                <div className="flex justify-between"><span>Date Range</span><span>{customDates?.from ? 'Selected' : 'Not set'}</span></div>
              )}
            </CardContent>
          </Card>

                <Button
            onClick={generate}
            disabled={isLoading || selectedCount === 0}
            className="w-full bg-cyan-600 text-white hover:bg-cyan-500 active:translate-y-px transition disabled:opacity-60"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating…
              </>
            ) : (
              'Generate Newsletter'
            )}
          </Button>

                {error && (
            <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            </div>
          )}
              </div>
            </div>
          </div>

          {/* Panel 2: Full-width Results */}
          <div className="w-1/2 pl-6 animate__animated">
            {result && showResults && (
            <Card className="border-white/10 bg-white/5 text-white">
              <CardHeader>
                <div className="flex items-center gap-4">
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-400" />
                    Generated Newsletter
                  </CardTitle>
                  <div className="ml-auto rounded-md border border-white/10 p-1 text-sm">
                    <button
                      onClick={() => setActiveTab('newsletter')}
                      className={`px-3 py-1 rounded ${activeTab==='newsletter' ? 'bg-white/15' : 'hover:bg-white/10'}`}
                    >
                      Newsletter
                    </button>
                    <button
                      onClick={() => setActiveTab('alerts')}
                      className={`px-3 py-1 rounded ${activeTab==='alerts' ? 'bg-white/15' : 'hover:bg-white/10'}`}
                    >
                      Alerts & Actions
                    </button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h3 className="font-semibold text-lg">{result.newsletter?.title}</h3>
                  <p className="text-sm text-white/70">
                    Generated: {new Date(result.newsletter?.generated_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  <Button onClick={()=> setShowResults(false)} variant="ghost" className="px-0 text-cyan-400 hover:text-cyan-300">
                    ← Back to Configuration
                  </Button>
                </div>
                
                {/* Removed duplicated totals header; metrics are inside content below */}
                
                <UISeparator className="bg-white/10" />

                {activeTab === 'newsletter' ? (
                  result.newsletter?.content ? (
                    /^\s*</.test(result.newsletter.content)
                      ? (
                        <div className="prose prose-invert max-w-none [&_h1]:text-2xl [&_h2]:text-xl [&_h3]:text-lg [&_a]:text-cyan-300 hover:[&_a]:text-cyan-200 [&_a]:inline-flex [&_a]:items-center [&_a]:gap-1 [&_ul]:list-disc [&_ul]:pl-6 [&_blockquote]:border-l-4 [&_blockquote]:border-white/20 [&_blockquote]:pl-4" dangerouslySetInnerHTML={{ __html: result.newsletter.content }} />
                      ) : (
                        <div className="prose prose-invert max-w-none text-left">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}
                            components={{
                              a: ({node, ...props}) => (
                                <a {...props} target="_blank" rel="noopener noreferrer" className="text-cyan-300 inline-flex items-center gap-1 hover:underline">
                                  {props.children}
                                  <ExternalLink className="h-4 w-4" />
                                </a>
                              ),
                              h2: ({node, ...props}) => (
                                <>
                                  <h2 {...props} className="mt-8 text-2xl font-bold tracking-wide text-white text-left" />
                                  <hr className="my-4 border-white/10" />
                                </>
                              ),
                              h4: ({node, ...props}) => (
                                <h4 {...props} className="text-lg font-semibold mt-6 text-cyan-300 text-left" />
                              ),
                              h3: ({node, ...props}) => (
                                <h3 {...props} className="text-xl font-semibold mt-6 text-white text-left" />
                              ),
                              p: ({node, ...props}) => (
                                <p {...props} className="text-white/85 leading-7 text-left" />
                              ),
                              ul: ({node, ...props}) => (
                                <ul {...props} className="list-disc pl-6 space-y-1 text-left" />
                              ),
                              li: ({node, ...props}) => (
                                <li {...props} className="text-white/85" />
                              ),
                            }}
                          >
                            {preprocessMarkdown(result.newsletter.content)}
                          </ReactMarkdown>
                        </div>
                      )
                  ) : (
                    <div className="text-sm text-white/70">No content returned by backend.</div>
                  )
                ) : (
                  <div className="space-y-3">
                    <div className="text-sm text-white/80">Things That Need Your Attention Right Now</div>
                    {(alerts || []).map((a) => (
                      <div key={a.id} className="rounded-lg border border-white/10 p-3 bg-white/5">
                        <div className="flex items-center justify-between">
                          <div className="font-medium">{a.title}</div>
                          {a.risk_level && (
                            <span className="text-xs rounded-full bg-white/10 px-2 py-0.5 capitalize">{a.risk_level}</span>
                          )}
                        </div>
                        {a.description && (
                          <p className="mt-1 text-sm text-white/70">{a.description}</p>
                        )}
                        <div className="mt-2 text-xs text-white/60 flex gap-3">
                          {a.alert_type && <span className="capitalize">Type: {a.alert_type}</span>}
                          {a.created_at && <span>Raised: {new Date(a.created_at).toLocaleString()}</span>}
                          {a.deadline && <span>Deadline: {new Date(a.deadline).toLocaleDateString()}</span>}
                        </div>
                      </div>
                    ))}
                    {!(alerts || []).length && (
                      <div className="text-sm text-white/60">No alerts available yet for this user.</div>
                    )}
                  </div>
                )}
                
                <div className="space-y-2">
                  <Button 
                    onClick={() => downloadNewsletter('html')}
                    className="w-full bg-cyan-600 text-white hover:bg-cyan-500"
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download HTML
                  </Button>
                  <Button 
                    onClick={() => downloadNewsletter('markdown')}
                    className="w-full bg-cyan-600 text-white hover:bg-cyan-500"
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    Download Markdown
                  </Button>
                </div>
              </CardContent>
            </Card>
            )}
          </div>
        </div>
      </div>

      {/* Loading Overlay */}
      {isLoading && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <Card className="border-white/10 bg-white/5 text-white max-w-md w-full mx-4">
            <CardHeader>
              <CardTitle className="text-center">Generating Newsletter</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                {LOADING_STEPS.map((step, index) => (
                  <div key={step.id} className="flex items-center gap-3">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      index < currentStep ? 'bg-green-500' : 
                      index === currentStep ? 'bg-cyan-500' : 'bg-white/20'
                    }`}>
                      {index < currentStep ? (
                        <CheckCircle className="h-4 w-4 text-white" />
                      ) : index === currentStep ? (
                        <Loader2 className="h-4 w-4 text-white animate-spin" />
                      ) : (
                        <div className="w-2 h-2 bg-white/50 rounded-full" />
                      )}
                    </div>
                    <span className={`text-sm ${
                      index <= currentStep ? 'text-white' : 'text-white/50'
                    }`}>
                      {step.label}
                    </span>
                  </div>
                ))}
              </div>
              
              <div className="w-full bg-white/10 rounded-full h-2">
                <div 
                  className="bg-cyan-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${((currentStep + 1) / LOADING_STEPS.length) * 100}%` }}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default Newsletter