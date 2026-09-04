import React, { useState, useEffect } from 'react'
import { Search, ChevronLeft, ChevronRight, Filter, X, Bot, Activity } from 'lucide-react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export default function DiscoveryLens() {
  const [data, setData] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ page: 1, limit: 12, total: 0, total_pages: 0 })
  const [selectedRecord, setSelectedRecord] = useState(null)
  const [insight, setInsight] = useState(null)
  const [loadingInsight, setLoadingInsight] = useState(false)
  
  const [filters, setFilters] = useState({
    platform: '',
    source_type: '',
    journey_stage: '',
    barrier_label: '',
    wishlist_relevance: '',
    theme_id: ''
  })
  
  const [themes, setThemes] = useState([])

  const fetchRecords = async (page = 1) => {
    setLoading(true)
    try {
      const params = { page, limit: pagination.limit }
      if (filters.platform) params.platform = filters.platform
      if (filters.source_type) params.source_type = filters.source_type
      if (filters.journey_stage) params.journey_stage = filters.journey_stage
      if (filters.barrier_label) params.barrier_label = filters.barrier_label
      if (filters.wishlist_relevance) params.wishlist_relevance = filters.wishlist_relevance
      if (filters.theme_id) params.theme_id = filters.theme_id
      
      const response = await axios.get(`${API_URL}/api/lens/records`, { params })
      setData(response.data.data)
      setPagination(response.data.pagination)
    } catch (error) {
      console.error("Failed to fetch records:", error)
    } finally {
      setLoading(false)
    }
  }

  const fetchAnalytics = async () => {
    try {
      const params = {}
      if (filters.platform) params.platform = filters.platform
      if (filters.source_type) params.source_type = filters.source_type
      if (filters.journey_stage) params.journey_stage = filters.journey_stage
      if (filters.barrier_label) params.barrier_label = filters.barrier_label
      if (filters.wishlist_relevance) params.wishlist_relevance = filters.wishlist_relevance
      if (filters.theme_id) params.theme_id = filters.theme_id
      
      const response = await axios.get(`${API_URL}/api/lens/analytics`, { params })
      setAnalytics(response.data)
    } catch (error) {
      console.error("Failed to fetch analytics:", error)
    }
  }

  const fetchInsight = async () => {
    setLoadingInsight(true)
    try {
      const params = {}
      if (filters.platform) params.platform = filters.platform
      if (filters.source_type) params.source_type = filters.source_type
      if (filters.journey_stage) params.journey_stage = filters.journey_stage
      if (filters.barrier_label) params.barrier_label = filters.barrier_label
      if (filters.wishlist_relevance) params.wishlist_relevance = filters.wishlist_relevance
      if (filters.theme_id) params.theme_id = filters.theme_id

      const res = await axios.get(`${API_URL}/api/lens/insights`, { params })
      setInsight(res.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingInsight(false)
    }
  }

  const fetchThemes = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/themes`)
      setThemes(response.data.themes)
    } catch (error) {
      console.error("Failed to fetch themes:", error)
    }
  }

  useEffect(() => {
    fetchThemes()
  }, [])

  useEffect(() => {
    fetchRecords(1)
    fetchAnalytics()
    fetchInsight()
  }, [filters])

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value })
  }

  const getRelevanceColor = (relevance) => {
    if (relevance === 'wishlist_related') return '#F13AB1'
    if (relevance === 'shopping_generic') return '#a0a0a5'
    return '#555'
  }

  return (
    <div style={{ position: 'relative' }}>
      <div className="card-title" style={{ marginBottom: '24px' }}>
        <Search size={20} color="#F13AB1" />
        <span style={{ fontSize: '20px', fontWeight: 700 }} className="text-gradient">Discovery Lens (Deep Dive)</span>
      </div>
      
      {/* Filters */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
          <Filter size={18} color="#a0a0a5" />
          <select name="platform" value={filters.platform} onChange={handleFilterChange} style={{ background: '#121214', color: '#fff', border: '1px solid #333', padding: '8px', borderRadius: '4px' }}>
            <option value="">All Platforms</option>
            <option value="Myntra">Myntra</option>
            <option value="AJIO">AJIO</option>
            <option value="Amazon Fashion">Amazon</option>
            <option value="Flipkart Fashion">Flipkart</option>
            <option value="Nykaa Fashion">Nykaa</option>
          </select>
          <select name="source_type" value={filters.source_type} onChange={handleFilterChange} style={{ background: '#121214', color: '#fff', border: '1px solid #333', padding: '8px', borderRadius: '4px' }}>
            <option value="">All Sources</option>
            <option value="reddit">Reddit</option>
            <option value="play_store">Play Store</option>
            <option value="app_store">App Store</option>
            <option value="web_article">Web</option>
            <option value="youtube">YouTube</option>
            <option value="product_reviews">Reviews</option>
          </select>
          <select name="journey_stage" value={filters.journey_stage} onChange={handleFilterChange} style={{ background: '#121214', color: '#fff', border: '1px solid #333', padding: '8px', borderRadius: '4px' }}>
            <option value="">All Journey Stages</option>
            <option value="Shortlist / intent">Shortlist / Intent</option>
            <option value="Product evaluation">Product Evaluation</option>
            <option value="Purchase">Purchase</option>
            <option value="Post-purchase">Post-Purchase</option>
            <option value="Pre-product">Pre-Product</option>
          </select>
          <input 
            type="text" 
            name="barrier_label" 
            placeholder="Search Barriers (e.g. price_drop)" 
            value={filters.barrier_label} 
            onChange={handleFilterChange}
            style={{ background: '#121214', color: '#fff', border: '1px solid #333', padding: '8px', borderRadius: '4px' }}
          />
          <select name="wishlist_relevance" value={filters.wishlist_relevance} onChange={handleFilterChange} style={{ background: '#121214', color: '#fff', border: '1px solid #333', padding: '8px', borderRadius: '4px' }}>
            <option value="">All Relevance</option>
            <option value="wishlist_related">Wishlist Related</option>
            <option value="shopping_generic">Shopping Generic</option>
            <option value="unknown">Unknown</option>
          </select>
          <select name="theme_id" value={filters.theme_id} onChange={handleFilterChange} style={{ background: '#121214', color: '#fff', border: '1px solid #333', padding: '8px', borderRadius: '4px', maxWidth: '150px', textOverflow: 'ellipsis' }}>
            <option value="">All Themes</option>
            {themes.map(t => <option key={t.theme_id} value={t.theme_id}>{t.theme_name}</option>)}
          </select>
        </div>
      </div>

      {/* KPI Header & AI Insight Panel */}
      <div className="grid-2" style={{ marginBottom: '24px' }}>
        
        {/* KPI Panel */}
        {analytics && (
          <div className="card glow-orange" style={{ display: 'flex', flexDirection: 'column', gap: '16px', justifyContent: 'center' }}>
            <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', textAlign: 'center' }}>
              <div>
                <div style={{ fontSize: '32px', fontWeight: 800, color: '#FD913C' }}>{analytics.slice_friction_score}</div>
                <div style={{ fontSize: '12px', color: '#a0a0a5', textTransform: 'uppercase', fontWeight: 600 }}>Slice Friction Score</div>
              </div>
              <div style={{ width: '1px', height: '40px', background: 'rgba(255,255,255,0.1)' }}></div>
              <div>
                <div style={{ fontSize: '24px', fontWeight: 800, color: '#E72744' }}>{analytics.emotion_detection?.negative || 0}</div>
                <div style={{ fontSize: '12px', color: '#a0a0a5', textTransform: 'uppercase', fontWeight: 600 }}>Negative Emotion</div>
              </div>
              <div style={{ width: '1px', height: '40px', background: 'rgba(255,255,255,0.1)' }}></div>
              <div>
                <div style={{ fontSize: '24px', fontWeight: 800, color: '#fff' }}>{analytics.total_records}</div>
                <div style={{ fontSize: '12px', color: '#a0a0a5', textTransform: 'uppercase', fontWeight: 600 }}>Total Records</div>
              </div>
            </div>
            
            {/* Feature Frustration Map */}
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px' }}>
              <div style={{ fontSize: '12px', color: '#a0a0a5', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Activity size={14} /> Feature Frustration Map
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {analytics.top_barriers?.slice(0, 5).map((b, i) => (
                  <span key={i} style={{ 
                    background: `rgba(231, 39, 68, ${Math.max(0.2, (5-i)/5)})`, 
                    color: i < 3 ? '#fff' : '#fca5a5', 
                    padding: '4px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 600 
                  }}>
                    {b.barrier.replace(/_/g, ' ')} ({b.count})
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Insight Panel */}
        <div className="card glow-pink" style={{ backgroundColor: 'rgba(241, 58, 177, 0.05)', border: '1px solid rgba(241, 58, 177, 0.2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#F13AB1', fontWeight: 600 }}>
              <Bot size={18} /> Deep Dive Narrative
              {loadingInsight && <span style={{fontSize: '12px', fontStyle: 'italic', marginLeft: '8px', color: '#a0a0a5'}}>Analyzing...</span>}
            </div>
          </div>
          
          {insight && (
            <div style={{ marginTop: '16px', background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px', color: '#e2e8f0', fontSize: '15px', lineHeight: 1.6 }}>
              {insight.slice_summary}
            </div>
          )}
          {!insight && !loadingInsight && (
            <div style={{ marginTop: '12px', color: '#a0a0a5', fontSize: '13px', fontStyle: 'italic' }}>
              No insight generated for this specific filtered slice.
            </div>
          )}
        </div>

      </div>

      {/* Verbatims Dashboard Grid */}
      <div style={{ display: 'flex', gap: '24px' }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>Representative Verbatims</div>
          
          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#a0a0a5' }}>Loading records...</div>
          ) : (
            <>
              <div className="grid-3" style={{ marginBottom: '24px' }}>
                {data.map((record) => (
                  <div 
                    key={record.record_id} 
                    className="card"
                    style={{ 
                      cursor: 'pointer', padding: '16px', border: selectedRecord?.record_id === record.record_id ? '1px solid #F13AB1' : '1px solid rgba(255,255,255,0.05)',
                      transition: 'all 0.2s', boxShadow: selectedRecord?.record_id === record.record_id ? '0 0 10px rgba(241, 58, 177, 0.2)' : 'none'
                    }}
                    onClick={() => setSelectedRecord(record)}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <span style={{ fontSize: '11px', fontWeight: 700, color: '#fff', background: '#29303E', padding: '2px 8px', borderRadius: '12px' }}>
                        {record.source_type}
                      </span>
                      <span style={{ fontSize: '11px', color: getRelevanceColor(record.wishlist_relevance) }}>
                        {record.wishlist_relevance.replace('_', ' ')}
                      </span>
                    </div>
                    
                    <div style={{ fontSize: '13px', color: '#e2e8f0', lineHeight: 1.5, marginBottom: '12px', fontStyle: 'italic', display: '-webkit-box', WebkitLineClamp: 4, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                      "{record.raw_text_snippet}"
                    </div>
                    
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {record.barrier_labels.slice(0, 2).map((b, i) => (
                        <span key={i} style={{ background: 'rgba(241, 58, 177, 0.1)', color: '#F13AB1', padding: '2px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 600 }}>{b}</span>
                      ))}
                      {record.barrier_labels.length > 2 && <span style={{ color: '#a0a0a5', fontSize: '10px' }}>+{record.barrier_labels.length - 2}</span>}
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px', color: '#a0a0a5', fontSize: '14px', borderTop: '1px solid #333' }}>
                <div>Showing {data.length.toLocaleString()} of {pagination.total.toLocaleString()}</div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <button 
                    onClick={() => fetchRecords(pagination.page - 1)}
                    disabled={pagination.page <= 1}
                    style={{ background: 'transparent', border: '1px solid #333', color: pagination.page <= 1 ? '#555' : '#fff', padding: '6px', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <span>Page {pagination.page} of {pagination.total_pages}</span>
                  <button 
                    onClick={() => fetchRecords(pagination.page + 1)}
                    disabled={pagination.page >= pagination.total_pages}
                    style={{ background: 'transparent', border: '1px solid #333', color: pagination.page >= pagination.total_pages ? '#555' : '#fff', padding: '6px', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Side Panel for Detail View */}
        {selectedRecord && (
          <div className="card glow-pink" style={{ width: '380px', flexShrink: 0, overflowY: 'auto', maxHeight: 'calc(100vh - 200px)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '16px' }}>
              <div style={{ fontWeight: 600, color: '#fff' }}>Record Inspection</div>
              <X size={18} style={{ cursor: 'pointer', color: '#a0a0a5' }} onClick={() => setSelectedRecord(null)} />
            </div>
            
            <div style={{ marginBottom: '24px' }}>
              <div style={{ color: '#F13AB1', fontSize: '12px', marginBottom: '8px', textTransform: 'uppercase', fontWeight: 600 }}>Raw Feedback</div>
              <div style={{ background: '#121214', padding: '16px', borderRadius: '8px', fontSize: '14px', lineHeight: 1.6, border: '1px solid rgba(255,255,255,0.05)', fontStyle: 'italic' }}>
                "{selectedRecord.raw_text_snippet}"
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
              <div>
                <div style={{ color: '#a0a0a5', fontSize: '11px', marginBottom: '4px', textTransform: 'uppercase' }}>Source Type</div>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{selectedRecord.source_type}</div>
              </div>
              <div>
                <div style={{ color: '#a0a0a5', fontSize: '11px', marginBottom: '4px', textTransform: 'uppercase' }}>Platform</div>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{selectedRecord.platform}</div>
              </div>
              <div>
                <div style={{ color: '#a0a0a5', fontSize: '11px', marginBottom: '4px', textTransform: 'uppercase' }}>Wishlist Relevance</div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: getRelevanceColor(selectedRecord.wishlist_relevance) }}>{selectedRecord.wishlist_relevance.replace('_', ' ')}</div>
              </div>
              <div>
                <div style={{ color: '#a0a0a5', fontSize: '11px', marginBottom: '4px', textTransform: 'uppercase' }}>Wishlist Intent</div>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{selectedRecord.wishlist_intent.replace('_', ' ')}</div>
              </div>
              <div>
                <div style={{ color: '#a0a0a5', fontSize: '11px', marginBottom: '4px', textTransform: 'uppercase' }}>Journey Stage</div>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{selectedRecord.journey_stage.replace('_', ' ')}</div>
              </div>
              <div>
                <div style={{ color: '#a0a0a5', fontSize: '11px', marginBottom: '4px', textTransform: 'uppercase' }}>Theme</div>
                <div style={{ fontSize: '13px', color: '#FD913C', fontWeight: 600 }}>{selectedRecord.theme_name || 'Unassigned'}</div>
              </div>
            </div>

            <div>
              <div style={{ color: '#a0a0a5', fontSize: '12px', marginBottom: '8px', textTransform: 'uppercase', fontWeight: 600 }}>Barriers Detected</div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {selectedRecord.barrier_labels.map((b, i) => (
                  <span key={i} style={{ background: 'rgba(231, 39, 68, 0.1)', color: '#E72744', border: '1px solid rgba(231, 39, 68, 0.3)', padding: '4px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 600 }}>
                    {b}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
