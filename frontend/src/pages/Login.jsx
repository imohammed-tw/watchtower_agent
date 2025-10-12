import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { apiService } from '@/services/api'

function Login() {
  const [isLogin, setIsLogin] = useState(true)
  const [formData, setFormData] = useState({
    user_id: '',
    password: '',
    email: '',
    name: ''
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  
  const navigate = useNavigate()

  const handleInputChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')
    setSuccess('')

    try {
      if (isLogin) {
        // Login
        const response = await apiService.login({
          user_id: formData.user_id,
          password: formData.password
        })
        
        if (response.success) {
          // Store token in localStorage
          localStorage.setItem('auth_token', response.token)
          localStorage.setItem('user_id', response.user_id)
          setSuccess('Login successful! Redirecting...')
          // Immediate redirect to onboarding route
          window.location.replace('/dashboard')
        }
      } else {
        // Register
        const response = await apiService.register({
          user_id: formData.user_id,
          password: formData.password,
          email: formData.email,
          name: formData.name
        })
        
        if (response.success) {
          setSuccess('Registration successful! You can now login.')
          setIsLogin(true) // Switch to login mode
          setFormData({ user_id: '', password: '', email: '', name: '' })
        }
      }
    } catch (err) {
      setError(err.message || 'Authentication failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 text-white">
      <div className="flex min-h-screen items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <Card className="border-white/10 bg-white/5 text-white">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl font-bold">
                {isLogin ? 'Welcome Back' : 'Create Account'}
              </CardTitle>
              <p className="text-white/70">
                {isLogin 
                  ? 'Sign in to your AI Watchtower account' 
                  : 'Join AI Watchtower to get started'
                }
              </p>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* User ID */}
                <div className="space-y-2">
                  <Label className="pb-2" htmlFor="user_id">User ID</Label>
                  <Input
                    id="user_id"
                    name="user_id"
                    type="text"
                    value={formData.user_id}
                    onChange={handleInputChange}
                    placeholder="Enter your user ID"
                    className="border-white/15 bg-white/5 text-white placeholder:text-white/50"
                    required
                  />
                </div>

                {/* Password */}
                <div className="space-y-2">
                  <Label className="pb-2" htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    placeholder="Enter your password"
                    className="border-white/15 bg-white/5 text-white placeholder:text-white/50"
                    required
                  />
                </div>

                {/* Registration fields */}
                {!isLogin && (
                  <>
                    <div className="space-y-2">
                      <Label className="pb-2" htmlFor="email">Email (Optional)</Label>
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        value={formData.email}
                        onChange={handleInputChange}
                        placeholder="Enter your email"
                        className="border-white/15 bg-white/5 text-white placeholder:text-white/50"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="pb-2" htmlFor="name">Name (Optional)</Label>
                      <Input
                        id="name"
                        name="name"
                        type="text"
                        value={formData.name}
                        onChange={handleInputChange}
                        placeholder="Enter your name"
                        className="border-white/15 bg-white/5 text-white placeholder:text-white/50"
                      />
                    </div>
                  </>
                )}

                {/* Error/Success Messages */}
                {error && (
                  <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300">
                    {error}
                  </div>
                )}

                {success && (
                  <div className="rounded-lg border border-green-500/20 bg-green-500/10 p-3 text-sm text-green-300">
                    {success}
                  </div>
                )}

                {/* Submit Button */}
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-cyan-600 text-white hover:bg-cyan-500 active:translate-y-px transition disabled:opacity-60 cursor-pointer"
                >
                  {isLoading 
                    ? (isLogin ? 'Signing in...' : 'Creating account...') 
                    : (isLogin ? 'Sign In' : 'Create Account')
                  }
                </Button>
              </form>

              <div className="mt-6">
                <Separator className="bg-white/10" />
                <div className="mt-4 text-center">
                  <button
                    type="button"
                    onClick={() => {
                      setIsLogin(!isLogin)
                      setError('')
                      setSuccess('')
                      setFormData({ user_id: '', password: '', email: '', name: '' })
                    }}
                    className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors cursor-pointer"
                  >
                    {isLogin 
                      ? "Don't have an account? Create one" 
                      : "Already have an account? Sign in"
                    }
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default Login
