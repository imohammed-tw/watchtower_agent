import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { apiService } from '@/services/api'

const CONTENT_TYPES = [
  { value: 'regulatory', label: 'Regulatory' },
  { value: 'technical', label: 'Technical' },
  { value: 'market', label: 'Market' },
  { value: 'security', label: 'Security' },
  { value: 'compliance', label: 'Compliance' }
]

const INDUSTRY_OPTIONS = [
  'Healthcare', 'Finance', 'Manufacturing', 'Technology', 
  'Automotive', 'Retail', 'Education', 'Government'
]

function Profile() {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [preferences, setPreferences] = useState({
    keywords: [],
    preferred_sources: [],
    excluded_sources: [],
    industry_focus: [],
    content_types: ['regulatory', 'technical', 'market'],
    urgency_threshold: 5,
    relevance_threshold: 0.7
  })
  const [newKeyword, setNewKeyword] = useState('')
  const [newSource, setNewSource] = useState('')
  const [newExcludedSource, setNewExcludedSource] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    loadUserPreferences()
  }, [])

  const loadUserPreferences = async () => {
    try {
      const userId = localStorage.getItem('user_id')
      if (!userId) {
        navigate('/login')
        return
      }

      const response = await apiService.getUserPreferences(userId)
      if (response.preferences) {
        setPreferences(response.preferences)
      }
    } catch (error) {
      console.error('Failed to load preferences:', error)
      setMessage('Failed to load preferences')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    setMessage('')

    try {
      const userId = localStorage.getItem('user_id')
      const response = await apiService.updateUserPreferences(userId, preferences)
      
      if (response.status === 'success') {
        setMessage('Preferences saved successfully!')
      }
    } catch (error) {
      console.error('Failed to save preferences:', error)
      setMessage('Failed to save preferences')
    } finally {
      setIsSaving(false)
    }
  }

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

  const addKeyword = () => {
    if (newKeyword.trim() && !preferences.keywords.includes(newKeyword.trim())) {
      setPreferences(prev => ({
        ...prev,
        keywords: [...prev.keywords, newKeyword.trim()]
      }))
      setNewKeyword('')
    }
  }

  const removeKeyword = (keyword) => {
    setPreferences(prev => ({
      ...prev,
      keywords: prev.keywords.filter(k => k !== keyword)
    }))
  }

  const addSource = () => {
    if (newSource.trim() && !preferences.preferred_sources.includes(newSource.trim())) {
      setPreferences(prev => ({
        ...prev,
        preferred_sources: [...prev.preferred_sources, newSource.trim()]
      }))
      setNewSource('')
    }
  }

  const removeSource = (source) => {
    setPreferences(prev => ({
      ...prev,
      preferred_sources: prev.preferred_sources.filter(s => s !== source)
    }))
  }

  const addExcludedSource = () => {
    if (newExcludedSource.trim() && !preferences.excluded_sources.includes(newExcludedSource.trim())) {
      setPreferences(prev => ({
        ...prev,
        excluded_sources: [...prev.excluded_sources, newExcludedSource.trim()]
      }))
      setNewExcludedSource('')
    }
  }

  const removeExcludedSource = (source) => {
    setPreferences(prev => ({
      ...prev,
      excluded_sources: prev.excluded_sources.filter(s => s !== source)
    }))
  }

  const toggleIndustryFocus = (industry) => {
    setPreferences(prev => ({
      ...prev,
      industry_focus: prev.industry_focus.includes(industry)
        ? prev.industry_focus.filter(i => i !== industry)
        : [...prev.industry_focus, industry]
    }))
  }

  const toggleContentType = (type) => {
    setPreferences(prev => ({
      ...prev,
      content_types: prev.content_types.includes(type)
        ? prev.content_types.filter(t => t !== type)
        : [...prev.content_types, type]
    }))
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400 mx-auto mb-4"></div>
            <p className="text-white/70">Loading preferences...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-6">
      <div className="mb-6">
        {/* <h1 className="text-2xl font-bold text-white">Profile Settings</h1> */}
        <p className="text-white/70">Manage your AI Watchtower preferences and account</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main Settings */}
        <div className="lg:col-span-2 space-y-6">
          {/* Keywords */}
          <Card className="border-white/10 bg-white/5 text-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Keywords
                <div className="group relative">
                  <svg className="h-4 w-4 text-white/60 hover:text-white cursor-help" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-900 text-white text-xs rounded-lg px-3 py-2 w-64 z-10">
                    <div className="text-center">Keywords help filter content by specific terms like "AI governance", "compliance", or "security" that are relevant to your interests.</div>
                    <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                  </div>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                  placeholder="Add keyword..."
                  className="border-white/15 bg-white/5 text-white placeholder:text-white/50"
                  onKeyPress={(e) => e.key === 'Enter' && addKeyword()}
                />
                <Button onClick={addKeyword} variant="outline" className="border-white/15 text-black hover:bg-cyan-600 hover:text-white">
                  Add
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {preferences.keywords.map((keyword) => (
                  <Badge key={keyword} variant="secondary" className="bg-cyan-500/20 text-cyan-300">
                    {keyword}
                    <button
                      onClick={() => removeKeyword(keyword)}
                      className="ml-2 hover:text-red-300"
                    >
                      ×
                    </button>
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Preferred Sources */}
          <Card className="border-white/10 bg-white/5 text-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Preferred Sources
                <div className="group relative">
                  <svg className="h-4 w-4 text-white/60 hover:text-white cursor-help" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-900 text-white text-xs rounded-lg px-3 py-2 w-64 z-10">
                    <div className="text-center">Trusted news sources and publications that you want to prioritize in your newsletters and alerts.</div>
                    <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                  </div>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  value={newSource}
                  onChange={(e) => setNewSource(e.target.value)}
                  placeholder="Add preferred source..."
                  className="border-white/15 bg-white/5 text-white placeholder:text-white/50"
                  onKeyPress={(e) => e.key === 'Enter' && addSource()}
                />
                <Button onClick={addSource} variant="outline" className="border-white/15 text-black hover:bg-cyan-600 hover:text-white">
                  Add
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {preferences.preferred_sources.map((source) => (
                  <Badge key={source} variant="secondary" className="bg-green-500/20 text-green-300">
                    {source}
                    <button
                      onClick={() => removeSource(source)}
                      className="ml-2 hover:text-red-300"
                    >
                      ×
                    </button>
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Excluded Sources */}
          <Card className="border-white/10 bg-white/5 text-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Excluded Sources
                <div className="group relative">
                  <svg className="h-4 w-4 text-white/60 hover:text-white cursor-help" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-900 text-white text-xs rounded-lg px-3 py-2 w-64 z-10">
                    <div className="text-center">Sources you want to exclude from your newsletters and alerts to avoid irrelevant or unreliable content.</div>
                    <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                  </div>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  value={newExcludedSource}
                  onChange={(e) => setNewExcludedSource(e.target.value)}
                  placeholder="Add excluded source..."
                  className="border-white/15 bg-white/5 text-white placeholder:text-white/50"
                  onKeyPress={(e) => e.key === 'Enter' && addExcludedSource()}
                />
                <Button onClick={addExcludedSource} variant="outline" className="border-white/15 text-black hover:bg-cyan-600 hover:text-white">
                  Add
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">  
                {preferences.excluded_sources.map((source) => (
                  <Badge key={source} variant="secondary" className="bg-red-500/20 text-red-300">
                    {source}
                    <button
                      onClick={() => removeExcludedSource(source)}
                      className="ml-2 hover:text-red-300"
                    >
                      ×
                    </button>
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Industry Focus */}
          <Card className="border-white/10 bg-white/5 text-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Industry Focus
                <div className="group relative">
                  <svg className="h-4 w-4 text-white/60 hover:text-white cursor-help" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-900 text-white text-xs rounded-lg px-3 py-2 w-64 z-10">
                    <div className="text-center">Select industries that are relevant to your work or interests to receive targeted AI and technology news.</div>
                    <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                  </div>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2">
                {INDUSTRY_OPTIONS.map((industry) => (
                  <label key={industry} className="flex items-center gap-2 p-2 rounded hover:bg-white/5">
                    <input
                      type="checkbox"
                      checked={preferences.industry_focus.includes(industry)}
                      onChange={() => toggleIndustryFocus(industry)}
                      className="rounded border-white/30"
                    />
                    <span className="text-sm">{industry}</span>
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Content Types */}
          <Card className="border-white/10 bg-white/5 text-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Content Types
                <div className="group relative">
                  <svg className="h-4 w-4 text-white/60 hover:text-white cursor-help" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-900 text-white text-xs rounded-lg px-3 py-2 w-64 z-10">
                    <div className="text-center">Choose the types of content you want to receive: regulatory updates, technical developments, market analysis, security alerts, and compliance news.</div>
                    <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                  </div>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2">
                {CONTENT_TYPES.map((type) => (
                  <label key={type.value} className="flex items-center gap-2 p-2 rounded hover:bg-white/5">
                    <input
                      type="checkbox"
                      checked={preferences.content_types.includes(type.value)}
                      onChange={() => toggleContentType(type.value)}
                      className="rounded border-white/30"
                    />
                    <span className="text-sm">{type.label}</span>
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Thresholds */}
          <Card className="border-white/10 bg-white/5 text-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Alert Thresholds
                <div className="group relative">
                  <svg className="h-4 w-4 text-white/60 hover:text-white cursor-help" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block bg-gray-900 text-white text-xs rounded-lg px-3 py-2 w-64 z-10">
                    <div className="text-center">Set minimum urgency (1-10) and relevance (0-1) scores for alerts. Higher thresholds mean fewer, more important notifications.</div>
                    <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                  </div>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="pb-4">Urgency Threshold (1-10)</Label>
                  <Input
                    type="number"
                    min="1"
                    max="10"
                    value={preferences.urgency_threshold}
                    onChange={(e) => setPreferences(prev => ({ ...prev, urgency_threshold: parseInt(e.target.value) }))}
                    className="border-white/15 bg-white/5 text-white"
                  />
                </div>
                <div>
                  <Label className="pb-4">Relevance Threshold (0-1)</Label>
                  <Input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={preferences.relevance_threshold}
                    onChange={(e) => setPreferences(prev => ({ ...prev, relevance_threshold: parseFloat(e.target.value) }))}
                    className="border-white/15 bg-white/5 text-white"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">

          {/* Stats */}
          <Card className="border-white/10 bg-white/5 text-white">
            <CardHeader>
              <CardTitle>Preferences Summary</CardTitle>
            </CardHeader>
             <CardContent className="space-y-2 text-sm">
               <div className="flex justify-between">
                 <span>Keywords:</span>
                 <span>{preferences.keywords.length}</span>
               </div>
               <div className="flex justify-between">
                 <span>Preferred Sources:</span>
                 <span>{preferences.preferred_sources.length}</span>
               </div>
               <div className="flex justify-between">
                 <span>Excluded Sources:</span>
                 <span>{preferences.excluded_sources.length}</span>
               </div>
               <div className="flex justify-between">
                 <span>Industries:</span>
                 <span>{preferences.industry_focus.length}</span>
               </div>
               <div className="flex justify-between">
                 <span>Content Types:</span>
                 <span>{preferences.content_types.length}</span>
               </div>
               <div className="flex justify-between">
                 <span>Urgency Threshold:</span>
                 <span>{preferences.urgency_threshold}/10</span>
               </div>
               <div className="flex justify-between">
                 <span>Relevance Threshold:</span>
                 <span>{preferences.relevance_threshold}</span>
               </div>
             </CardContent>
          </Card>

          
          {/* Save Button */}
          <div className="space-y-3">
            <Button
              onClick={handleSave}
              disabled={isSaving}
              className="w-full bg-cyan-600 text-white hover:bg-cyan-500"
            >
              {isSaving ? 'Saving...' : 'Save Preferences'}
            </Button>
            
            {message && (
              <div className={`text-sm ${message.includes('success') ? 'text-green-300' : 'text-red-300'}`}>
                {message}
              </div>
            )}
          </div>

          {/* Account Actions */}
          <Card className="border-white/10 bg-white/5 text-white">
            <CardHeader>
              <CardTitle>Account</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                onClick={handleLogout}
                variant="outline"
                className="w-full border-white/15 text-black hover:bg-cyan-600 hover:text-white"
              >
                Logout
              </Button>
            </CardContent>
          </Card>

          
        </div>
      </div>
    </div>
  )
}

export default Profile
