import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid } from 'recharts'
import { Folder, Smartphone, Globe, MessageSquare, Bot } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export default function Overview() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ platform: '', time_range: '' })
  const [insights, setInsights] = useState(null)
  const [loadingInsights, setLoadingInsights] = useState(false)

  const fetchInsights = () => {
    setLoadingInsights(true)
    axios.get(`${API_URL}/api/overview/insights`, { params: filters })
      .then(res => {
        setInsights(res.data)
        setLoadingInsights(false)
      })
      .catch(err => {
        console.error(err)
        setLoadingInsights(false)
      })
  }

  const fetchOverview = () => {
    setLoading(true)
    axios.get(`${API_URL}/api/overview`, { params: filters })
      .then(res => {
        setData(res.data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
  }

  useEffect(() => {
    fetchOverview()
    fetchInsights()
  }, [filters])

  if (loading && !data) return <div style={{ color: '#a0a0a5' }}>Loading Intelligence...</div>
  if (!data) return <div style={{ color: '#E72744' }}>Failed to load data. Ensure backend is running.</div>

  const COLORS = ['#F13AB1', '#E72744', '#FD913C', '#F05524', '#29303E', '#8b5cf6']
  
  // Custom colors for sentiment
  const SENTIMENT_COLORS = {
    'positive': '#F13AB1',
    'neutral': '#29303E',
    'negative': '#E72744'
  }

  const getSourceIcon = (source) => {
    if (source.toLowerCase().includes('store')) return <Smartphone size={16} />
    if (source.toLowerCase().includes('reddit')) return <MessageSquare size={16} />
    return <Globe size={16} />
  }

  return (
    <div>
      {/* Header & Filters */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div className="card-title" style={{ margin: 0 }}>
          <Folder size={20} color="#F13AB1" />
          <span style={{ fontSize: '20px', fontWeight: 700 }} className="text-gradient">Discovery Synthesis</span>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <select 
            value={filters.platform} 
            onChange={e => setFilters({...filters, platform: e.target.value})}
            style={{ background: '#121214', color: '#fff', border: '1px solid #333', padding: '6px 12px', borderRadius: '4px' }}
          >
            <option value="">All Platforms</option>
            <option value="Myntra">Myntra</option>
            <option value="AJIO">Ajio</option>
          </select>
          <select 
            value={filters.time_range} 
            onChange={e => setFilters({...filters, time_range: e.target.value})}
            style={{ background: '#121214', color: '#fff', border: '1px solid #333', padding: '6px 12px', borderRadius: '4px' }}
          >
            <option value="">All Time</option>
            <option value="1y">Last 1 Year</option>
          </select>
        </div>
      </div>

      {/* Top 3 KPIs */}
      <div className="grid-3" style={{ marginBottom: '24px' }}>
        <div className="card glow-pink" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
          <div className="stat-value" style={{ color: '#F13AB1' }}>{data.reviews_analyzed.toLocaleString()}</div>
          <div className="stat-label">Records Analyzed</div>
        </div>
        <div className="card glow-orange" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
          <div className="stat-value" style={{ color: '#FD913C' }}>{data.theme_count}</div>
          <div className="stat-label">Opportunity Themes</div>
        </div>
        <div className="card glow-red" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
          <div className="stat-value" style={{ color: '#E72744' }}>{data.average_severity.toFixed(2)}</div>
          <div className="stat-label">Average Severity (0-1)</div>
        </div>
      </div>

      {/* AI Insights Panel */}
      <div className="card" style={{ marginBottom: '24px', backgroundColor: 'rgba(241, 58, 177, 0.05)', border: '1px solid rgba(241, 58, 177, 0.2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#F13AB1', fontWeight: 600 }}>
            <Bot size={18} /> Executive AI Narrative
            {loadingInsights && <span style={{fontSize: '12px', fontStyle: 'italic', marginLeft: '8px', color: '#a0a0a5'}}>Analyzing...</span>}
          </div>
        </div>
        
        {insights && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px' }}>
              <div style={{ color: '#fff', fontWeight: 700, marginBottom: '8px' }}>🚨 Hero Problem: {insights.hero_problem?.title}</div>
              <div style={{ color: '#e2e8f0', fontSize: '14px', lineHeight: 1.5 }}>{insights.hero_problem?.description}</div>
              <div style={{ fontSize: '12px', color: '#E72744', marginTop: '8px', fontWeight: 600 }}>Impact: {insights.hero_problem?.impact_score?.toUpperCase()}</div>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <div style={{ fontSize: '12px', color: '#a0a0a5', textTransform: 'uppercase', marginBottom: '8px', fontWeight: 600 }}>Key Pain Points</div>
                {insights.painpoints?.map((p, i) => (
                  <div key={i} style={{ marginBottom: '12px' }}>
                    <div style={{ color: '#fff', fontSize: '13px', fontWeight: 600 }}>&bull; {p.title}</div>
                    <div style={{ color: '#a0a0a5', fontSize: '13px', marginLeft: '12px', marginTop: '4px' }}>{p.context}</div>
                  </div>
                ))}
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#a0a0a5', textTransform: 'uppercase', marginBottom: '8px', fontWeight: 600 }}>Needs Validation</div>
                {insights.needs_validation?.map((nv, i) => (
                  <div key={i} style={{ marginBottom: '12px' }}>
                    <div style={{ color: '#fff', fontSize: '13px', fontWeight: 600 }}>? {nv.area}</div>
                    <div style={{ color: '#a0a0a5', fontSize: '13px', marginLeft: '16px', marginTop: '4px' }}>{nv.reason}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        {!insights && !loadingInsights && (
          <div style={{ color: '#a0a0a5', fontSize: '13px', fontStyle: 'italic' }}>
            No insights available for this slice of data.
          </div>
        )}
      </div>

      {/* Sources Carousel */}
      <div className="grid-4" style={{ marginBottom: '24px' }}>
        {data.sources.map((src, i) => (
          <div key={i} className="card glow-orange" style={{ padding: '16px', display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(253, 145, 60, 0.1)', color: '#FD913C', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {getSourceIcon(src.source_type)}
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: '14px', textTransform: 'capitalize' }}>{src.source_type.replace(/_/g, ' ')}</div>
              <div style={{ fontSize: '12px', color: '#a0a0a5' }}>{src.total_records} records &middot; {src.year_coverage}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid-2" style={{ marginBottom: '24px' }}>
        {/* Timeline AreaChart */}
        <div className="card glow-pink">
          <div className="card-title">Reviews by Year</div>
          <div style={{ height: '250px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.reviews_by_year} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F13AB1" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#F13AB1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                <XAxis dataKey="year" stroke="#a0a0a5" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#1c1c1f', border: '1px solid #F13AB1', borderRadius: '8px' }} />
                <Area type="monotone" dataKey="count" stroke="#F13AB1" fillOpacity={1} fill="url(#colorCount)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sentiment & Segments */}
        <div className="card glow-red">
          <div className="card-title">Sentiment & Segments</div>
          <div style={{ display: 'flex', alignItems: 'flex-start', marginTop: '16px', height: '280px', gap: '24px', justifyContent: 'center' }}>
            
            {/* Donut Chart for Sentiment */}
            <div style={{ position: 'relative', width: '200px', height: '280px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie 
                    data={data.sentiment_breakdown} 
                    dataKey="count" 
                    nameKey="sentiment" 
                    cx="50%" cy={90}
                    innerRadius={60} 
                    outerRadius={80} 
                    paddingAngle={2}
                    stroke="none"
                  >
                    {data.sentiment_breakdown?.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={SENTIMENT_COLORS[entry.sentiment] || COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1c1c1f', border: '1px solid #333', borderRadius: '8px' }} />
                  <Legend layout="horizontal" verticalAlign="bottom" align="center" iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ 
                position: 'absolute', top: 0, left: 0, width: '100%', height: '180px', 
                display: 'flex', alignItems: 'center', justifyContent: 'center', 
                fontSize: '12px', fontWeight: 600, color: '#a0a0a5', flexDirection: 'column', pointerEvents: 'none'
              }}>
                <div>Sentiment</div>
              </div>
            </div>

            {/* Segments Mentions Donut */}
            <div style={{ position: 'relative', width: '200px', height: '280px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie 
                    data={data.segment_mentions?.slice(0, 5)} 
                    dataKey="count" 
                    nameKey="segment" 
                    cx="50%" cy={90}
                    innerRadius={60} 
                    outerRadius={80} 
                    paddingAngle={2}
                    stroke="none"
                  >
                    {data.segment_mentions?.slice(0, 5).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1c1c1f', border: '1px solid #333', borderRadius: '8px' }} />
                  <Legend layout="horizontal" verticalAlign="bottom" align="center" iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ 
                position: 'absolute', top: 0, left: 0, width: '100%', height: '180px', 
                display: 'flex', alignItems: 'center', justifyContent: 'center', 
                fontSize: '12px', fontWeight: 600, color: '#a0a0a5', flexDirection: 'column', pointerEvents: 'none'
              }}>
                <div>Segments</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Grid: Recent Reviews Verbatims */}
      <div className="card glow-orange" style={{ marginBottom: '40px' }}>
        <div className="card-title">Recent Reviews</div>
        <div className="grid-3" style={{ marginTop: '16px' }}>
          {data.recent_verbatims?.map((rev, i) => (
            <div key={i} style={{ background: '#121214', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ background: '#29303E', color: '#fff', padding: '2px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 'bold' }}>{rev.platform || "Unknown"}</span>
                <span style={{ color: '#a0a0a5', fontSize: '11px', textTransform: 'capitalize' }}>{rev.source.replace(/_/g, ' ')}</span>
              </div>
              <div style={{ fontSize: '13px', color: '#e2e8f0', lineHeight: 1.5, fontStyle: 'italic' }}>
                "{rev.text.length > 200 ? rev.text.substring(0, 200) + '...' : rev.text}"
              </div>
            </div>
          ))}
          {(!data.recent_verbatims || data.recent_verbatims.length === 0) && (
            <div style={{ color: '#a0a0a5', fontSize: '13px' }}>No recent verbatims available.</div>
          )}
        </div>
      </div>
    </div>
  )
}
