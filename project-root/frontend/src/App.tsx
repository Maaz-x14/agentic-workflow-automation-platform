import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Editor from './pages/Editor'

export default function App() {
  return (
    <div className="app-root">
      <header style={{ padding: 12, borderBottom: '1px solid #eee' }}>
        <Link to="/">Dashboard</Link> | <Link to="/editor">Editor</Link>
      </header>
      <main style={{ padding: 12 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/editor" element={<Editor />} />
        </Routes>
      </main>
    </div>
  )
}
