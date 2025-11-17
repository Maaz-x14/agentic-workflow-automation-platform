import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Editor from './pages/Editor'
import Workflows from './pages/Workflows'

export default function App() {
  return (
    <div className="app-root">
      <header className="app-header">
        <Link to="/">Workflows</Link> | <Link to="/editor">Editor</Link>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Workflows />} />
          <Route path="/editor" element={<Editor />} />
        </Routes>
      </main>
    </div>
  )
}
