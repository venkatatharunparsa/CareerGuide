import { useEffect, useState } from 'react'

import { Routes, Route, Navigate } from 'react-router-dom'

import Layout from './components/Layout'

import Dashboard from './pages/Dashboard'

import Profile from './pages/Profile'

import Jobs from './pages/Jobs'

import Login from './pages/Login'



export default function App() {

  const [token, setToken] = useState(() => localStorage.getItem('token'))



  useEffect(() => {

    const onStorage = () => setToken(localStorage.getItem('token'))

    window.addEventListener('storage', onStorage)

    return () => window.removeEventListener('storage', onStorage)

  }, [])



  return (

    <Routes>

      <Route path="/login" element={<Login onAuth={() => setToken(localStorage.getItem('token'))} />} />

      <Route path="/" element={token ? <Layout onLogout={() => setToken(null)} /> : <Navigate to="/login" replace />}>

        <Route index element={<Dashboard />} />

        <Route path="profile" element={<Profile />} />

        <Route path="jobs" element={<Jobs />} />

      </Route>

    </Routes>

  )

}


