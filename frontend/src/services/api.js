// API service for connecting to the backend
const API_BASE_URL = 'http://localhost:8000'

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  // Newsletter endpoints
  async generateNewsletter(userId, config) {
    const { format, sections, template, customDates, maxArticles, maxTotalWords, maxSectionWords } = config
    // Backend expects user_id as query param; monthly uses /generate, others use /generate/{format}
    const base = format === 'monthly' ? `/api/v1/newsletter/generate` : `/api/v1/newsletter/generate/${format}`
    let endpoint = `${base}?user_id=${encodeURIComponent(userId)}`
    let body = {
      sections: Array.from(sections),
      template,
    }

    // Add date range for custom newsletters
    if (format === 'custom' && customDates?.from && customDates?.to) {
      body.date_from = customDates.from.toISOString().split('T')[0]
      body.date_to = customDates.to.toISOString().split('T')[0]
    }

    // Optional limits if provided
    if (typeof maxArticles === 'number') body.max_articles = maxArticles
    if (typeof maxTotalWords === 'number') body.max_total_words = maxTotalWords
    if (typeof maxSectionWords === 'number') body.max_section_words = maxSectionWords

    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  }

  async downloadNewsletter(userId, format = 'html') {
    return this.request(`/api/v1/newsletter/export/${userId}/latest?format=${format}`, {
      method: 'GET',
    })
  }

  async downloadNewsletterById(newsletterId, format = 'html') {
    return this.request(`/api/v1/newsletter/export/by-id/${newsletterId}?format=${format}`, {
      method: 'GET',
    })
  }

  async getNewsletterFormats() {
    return this.request('/api/v1/newsletter/formats')
  }

  async getNewsletters(userId, limit = 20) {
    return this.request(`/api/v1/newsletter/list/${userId}?limit=${limit}`)
  }

  async getNewsletterHistory(userId, limit = 10) {
    return this.request(`/api/v1/newsletter/history/${userId}?limit=${limit}`)
  }

  async getNewsletterById(newsletterId) {
    return this.request(`/api/v1/newsletter/get/${newsletterId}`, { method: 'GET' })
  }

  // Alerts & Dashboard
  async getUserAlerts(userId, limit = 50) {
    return this.request(`/api/v1/dashboard/alerts/${userId}?limit=${limit}`, {
      method: 'GET',
    })
  }

  // Auth endpoints
  async login(credentials) {
    return this.request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    })
  }

  async register(userData) {
    return this.request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    })
  }

  async logout() {
    const token = localStorage.getItem('auth_token')
    if (token) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_id')
      return this.request('/api/v1/auth/logout', {
        method: 'POST',
        body: JSON.stringify({ token }),
      })
    }
  }

  async getCurrentUser() {
    const token = localStorage.getItem('auth_token')
    if (!token) throw new Error('No auth token')
    
    return this.request(`/api/v1/auth/me?token=${token}`)
  }

  async validateToken() {
    const token = localStorage.getItem('auth_token')
    if (!token) return { valid: false }
    
    return this.request(`/api/v1/auth/validate?token=${token}`)
  }

  // User preferences endpoints
  async getUserPreferences(userId) {
    return this.request(`/api/v1/users/preferences/${userId}`)
  }

  async updateUserPreferences(userId, preferences) {
    return this.request(`/api/v1/users/preferences/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(preferences),
    })
  }

  async saveUserPreferences(preferences) {
    return this.request('/api/v1/users/preferences', {
      method: 'POST',
      body: JSON.stringify(preferences),
    })
  }

  // Health check
  async healthCheck() {
    return this.request('/api/v1/dashboard/health-check')
  }

  // Dashboard endpoints
  async getDashboardMetrics(userId) {
    return this.request(`/api/v1/dashboard/metrics/${userId}`)
  }

  async getDashboardAlerts(userId, limit = 5) {
    return this.request(`/api/v1/dashboard/alerts/${userId}?limit=${limit}`)
  }
}

export const apiService = new ApiService()
