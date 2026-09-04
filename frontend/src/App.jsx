import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Folder, Search, Target, Bot } from 'lucide-react'

// Placeholder components for the 4 pages
import Overview from './pages/Overview'
import DiscoveryLens from './pages/DiscoveryLens'
import PMPriorityRadar from './pages/PMPriorityRadar'
import DiscoveryCopilot from './pages/DiscoveryCopilot'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export default function App() {
  const [activeTab, setActiveTab] = useState('Overview')
  const [totalRecords, setTotalRecords] = useState(null)

  useEffect(() => {
    axios.get(`${API_URL}/api/overview`)
      .then(res => setTotalRecords(res.data.reviews_analyzed))
      .catch(err => console.error(err))
  }, [])

  const tabs = [
    { id: 'Overview', label: 'Overview', icon: Folder, color: '#facc15' }, // yellow folder
    { id: 'Discovery Lens', label: 'Discovery Lens', icon: Search, color: '#60a5fa' }, // blue search
    { id: 'PM Priority Radar', label: 'PM Priority Radar', icon: Target, color: '#f43f5e' }, // pink/red target
    { id: 'Discovery Copilot', label: 'Discovery Copilot', icon: Bot, color: '#a78bfa' }, // purple bot
  ]

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">M</div>
          <div className="sidebar-logo-text">
            <h1>Myntra Pulse</h1>
            <p>Review Intelligence</p>
          </div>
        </div>
        
        <div className="sidebar-label">WORKSPACE</div>
        
        <div className="nav-links">
          {tabs.map(tab => (
            <div 
              key={tab.id}
              className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <tab.icon className="nav-icon" style={{ color: tab.color }} />
              {tab.label}
            </div>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="main-content">
        {/* Header */}
        <div className="header">
          <div>
            <div className="header-subtitle">
              AI-POWERED REVIEW ANALYSIS
            </div>
            <div className="header-title">
              <h2>Myntra Discovery <span>Intelligence Engine</span></h2>
            </div>
            <div className="header-desc">
              {totalRecords ? totalRecords.toLocaleString() : "Loading"} feedback records from App Store, Play Store, Reddit & Web — analyzed for wishlist intent, purchase barriers, and journey friction.
            </div>
          </div>
        </div>

        {/* Top Tabs (replicated from sidebar for breadcrumb feel as per screenshot) */}
        <div className="tabs">
          {tabs.map(tab => (
            <div 
              key={`top-${tab.id}`}
              className={`tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <tab.icon size={16} style={{ color: tab.color }} />
              {tab.label}
            </div>
          ))}
        </div>

        {/* Page Content - Conditional Rendering acts like pre-loaded views */}
        <div className="page-container">
          {activeTab === 'Overview' && <Overview />}
          {activeTab === 'Discovery Lens' && <DiscoveryLens />}
          {activeTab === 'PM Priority Radar' && <PMPriorityRadar />}
          {activeTab === 'Discovery Copilot' && <DiscoveryCopilot />}
        </div>
      </div>
    </div>
  )
}
