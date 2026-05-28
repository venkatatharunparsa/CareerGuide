import axios from 'axios'

// In Vite dev, use '' so /api is proxied to the backend (see vite.config.js).
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 120000,
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
