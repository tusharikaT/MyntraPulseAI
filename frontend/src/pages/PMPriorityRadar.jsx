import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { Target, Info, ChevronDown, ChevronUp, Bot, MessageSquare } from 'lucide-react'
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts'

export default function PMPriorityRadar() {
  const [themes, setThemes] = useState([])
  const [loading, setLoading] = useState(true)
  const [showInfo, setShowInfo] = useState(false)
  const [insights, setInsights] = useState(null)
  const [loadingInsights, setLoadingInsights] = useState(false)
  const [insightError, setInsightError] = useState(null)
  
  const [expandedTheme, setExpandedTheme] = useState(null)
  const [examples, setExamples] = useState([])
  const [loadingExamples, setLoadingExamples] = useState(false)

  const fetchInsights = async () => {
    setLoadingInsights(true)
    setInsightError(null)
    try {
      const res = await axios.get('http://127.0.0.1:8000/api/themes/insights')
      if (res.data.themes && res.data.themes.length > 0) {
        setInsights(res.data.themes)
      } else {
        setInsightError("LLM failed to generate insights (possibly due to rate limits or API key issues).")
      }
    } catch (err) {
      console.error(err)
      setInsightError("Failed to fetch insights from the server.")
    } finally {
      setLoadingInsights(false)
    }
  }

  useEffect(() => {
    axios.get('http://127.0.0.1:8000/api/themes')
      .then(res => {
        setThemes(res.data.themes)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
    
    // Auto-fetch insights
    fetchInsights()
  }, [])

  const toggleExamples = async (themeId) => {
    if (expandedTheme === themeId) {
      setExpandedTheme(null)
      return
    }
    setExpandedTheme(themeId)
    setLoadingExamples(true)
    setExamples([])
    try {
      const res = await axios.get(`http://127.0.0.1:8000/api/themes/${themeId}/examples`)
      setExamples(res.data.examples)
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingExamples(false)
    }
  }

  const plottedThemes = React.useMemo(() => {
    const coordGroups = {};
    themes.forEach(theme => {
      // Group points that share the exact same coordinates (like 1.0, 1.0)
      const key = `${Number(theme.metric_proximity).toFixed(2)}_${Number(theme.severity).toFixed(2)}`;
      if (!coordGroups[key]) coordGroups[key] = [];
      coordGroups[key].push(theme.theme_id);
    });

    return themes.map((theme, index) => {
      const key = `${Number(theme.metric_proximity).toFixed(2)}_${Number(theme.severity).toFixed(2)}`;
      const group = coordGroups[key];
      const count = group.length;
      const groupIndex = group.indexOf(theme.theme_id);
      
      let dx = 0;
      let dy = 0;
      if (count > 1) {
        // Deterministic spiral placement for overlapping points
        const radius = 0.04 + (groupIndex * 0.012);
        const angle = groupIndex * 2.39996; // Golden angle (~137.5 degrees)
        dx = Math.cos(angle) * radius;
        dy = Math.sin(angle) * radius;
      }
      
      return {
        ...theme,
        rankLabel: (index + 1).toString(),
        plot_proximity: theme.metric_proximity + dx,
        plot_severity: theme.severity + dy
      };
    });
  }, [themes]);

  if (loading) return <div style={{ padding: '24px', color: '#a0a0a5' }}>Loading Themes...</div>

  const getConsistencyColor = (consistency) => {
    if (consistency >= 0.8) return '#F13AB1' // High consistency (Pink)
    if (consistency >= 0.5) return '#E72744' // Medium-High (Red)
    if (consistency >= 0.3) return '#FD913C' // Medium (Orange)
    return '#F05524' // Low consistency (Dark Orange)
  }

  return (
    <div style={{ paddingBottom: '40px' }}>
      <div className="card-title" style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Target size={24} color="#F13AB1" />
          <span style={{ fontSize: '24px', fontWeight: 700 }} className="text-gradient">PM Priority Radar & Theme Rankings</span>
        </div>
        <button 
          onClick={() => setShowInfo(!showInfo)}
          style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
            color: '#e2e8f0', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', fontSize: '14px'
          }}
        >
          <Info size={16} color="#F13AB1" />
          How is this calculated?
          {showInfo ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {showInfo && (
        <div className="card glow-pink" style={{ marginBottom: '24px', backgroundColor: 'rgba(241, 58, 177, 0.05)', border: '1px solid rgba(241, 58, 177, 0.2)' }}>
          <h3 style={{ marginTop: 0, color: '#F13AB1', marginBottom: '8px' }}>PM Priority Score — Explanation</h3>
          <p style={{ color: '#e2e8f0', fontSize: '14px', lineHeight: 1.6 }}>
            The PM Priority Score ranks opportunity themes (user problems) by how attractive they are to work on, given our business goal.
            <br/><br/>
            <strong>Formula:</strong> <code>0.30*Prevalence + 0.25*Severity + 0.25*Proximity + 0.10*Consistency + 0.10*Addressability</code>
          </p>
        </div>
      )}

      {/* Bubble Chart */}
      <div className="card glow-orange" style={{ marginBottom: '24px' }}>
        <div className="card-title">Theme Quadrants (Proximity vs Severity)</div>
        <div style={{ color: '#a0a0a5', fontSize: '12px', marginBottom: '16px' }}>Bubble size represents Prevalence (number of affected users). Overlapping points are clustered in a spiral for visibility.</div>
        <div style={{ height: '400px', width: '100%' }}>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              {/* Dynamic zooming with dataMin and dataMax */}
              <XAxis type="number" dataKey="plot_proximity" name="Proximity" stroke="#a0a0a5" domain={['dataMin - 0.05', 'dataMax + 0.05']} tick={false} label={{ value: 'Proximity', position: 'bottom', fill: '#a0a0a5' }} />
              <YAxis type="number" dataKey="plot_severity" name="Severity" stroke="#a0a0a5" domain={['dataMin - 0.05', 'dataMax + 0.05']} tick={false} label={{ value: 'Severity', angle: -90, position: 'left', fill: '#a0a0a5' }} />
              <ZAxis type="number" dataKey="prevalence" range={[100, 800]} name="Prevalence" />
              <Scatter name="Themes" data={plottedThemes}>
                {themes.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getConsistencyColor(entry.cross_source_consistency)} opacity={0.8} />
                ))}
                <LabelList dataKey="rankLabel" position="center" fill="#fff" fontSize={14} fontWeight="bold" />
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        <div style={{ marginTop: '16px', display: 'flex', flexWrap: 'wrap', gap: '16px', borderTop: '1px solid #333', paddingTop: '16px' }}>
          {themes.map((theme, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ background: getConsistencyColor(theme.cross_source_consistency), color: '#fff', borderRadius: '50%', width: '24px', height: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 'bold' }}>{idx + 1}</div>
              <div style={{ fontSize: '13px', color: '#e2e8f0' }}>{theme.theme_name}</div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Insights Panel */}
      <div className="card glow-red" style={{ marginBottom: '24px', backgroundColor: 'rgba(231, 39, 68, 0.05)', border: '1px solid rgba(231, 39, 68, 0.2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#E72744', fontWeight: 600 }}>
            <Bot size={18} /> Top Themes Narrative
            {loadingInsights && <span style={{fontSize: '12px', fontStyle: 'italic', marginLeft: '8px', color: '#a0a0a5'}}>Analyzing...</span>}
          </div>
        </div>
        
        {insightError && (
          <div style={{ background: 'rgba(231, 39, 68, 0.1)', borderLeft: '3px solid #E72744', padding: '12px', borderRadius: '4px', color: '#e2e8f0', fontSize: '13px', marginBottom: '16px' }}>
            <strong>Error:</strong> {insightError}
          </div>
        )}

        {insights && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {insights.map((ins, i) => {
              const matchedTheme = themes.find(t => t.theme_id === ins.theme_id)
              return (
                <div key={i} style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px', borderLeft: '3px solid #E72744' }}>
                  <div style={{ color: '#fff', fontWeight: 600, fontSize: '15px', marginBottom: '4px' }}>
                    #{i+1} {matchedTheme ? matchedTheme.theme_name : 'Unknown Theme'}
                  </div>
                  <div style={{ color: '#e2e8f0', fontSize: '14px', marginBottom: '12px', fontStyle: 'italic' }}>"{ins.summary}"</div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <div>
                      <div style={{ fontSize: '11px', color: '#a0a0a5', textTransform: 'uppercase', marginBottom: '4px', fontWeight: 600 }}>Root Cause Hypothesis</div>
                      <div style={{ fontSize: '13px', color: '#e2e8f0', lineHeight: 1.5 }}>{ins.root_cause}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', color: '#a0a0a5', textTransform: 'uppercase', marginBottom: '4px', fontWeight: 600 }}>Product Opportunity</div>
                      <div style={{ fontSize: '13px', color: '#e2e8f0', lineHeight: 1.5 }}>{ins.opportunity}</div>
                    </div>
                  </div>
                  
                  {/* Actionable Sections Below Chart Insights */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '16px', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '12px' }}>
                    <div>
                      <div style={{ fontSize: '11px', color: '#FD913C', textTransform: 'uppercase', marginBottom: '4px', fontWeight: 600 }}>Affected User Segments</div>
                      <div style={{ fontSize: '12px', color: '#a0a0a5' }}>
                        {matchedTheme?.dominant_stages.map(s => <span key={s} style={{background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px', marginRight: '4px'}}>{s}</span>) || 'Various'}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', color: '#F13AB1', textTransform: 'uppercase', marginBottom: '4px', fontWeight: 600 }}>Key Proposed Features</div>
                      <div style={{ fontSize: '12px', color: '#a0a0a5' }}>
                        {ins.opportunity}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
        {!insights && !loadingInsights && !insightError && (
          <div style={{ color: '#a0a0a5', fontSize: '13px', fontStyle: 'italic', padding: '0 16px 16px 16px' }}>
            Click "Generate Insights" to ask the LLM to analyze the top themes.
          </div>
        )}
      </div>

      {/* Ranked Table */}
      <div className="card" style={{ overflowX: 'auto' }}>
        <div className="card-title">Ranked Opportunities</div>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #333', color: '#a0a0a5', backgroundColor: '#121214' }}>
              <th style={{ padding: '12px 16px', width: '5%' }}>Rank</th>
              <th style={{ padding: '12px 16px', width: '30%' }}>Theme</th>
              <th style={{ padding: '12px 16px' }}>PM Score</th>
              <th style={{ padding: '12px 16px' }}>Prevalence</th>
              <th style={{ padding: '12px 16px' }}>Severity</th>
              <th style={{ padding: '12px 16px' }}>Proximity</th>
              <th style={{ padding: '12px 16px' }}>Evidence</th>
            </tr>
          </thead>
          <tbody>
            {themes.map((theme, idx) => (
              <React.Fragment key={theme.theme_id}>
                <tr style={{ borderBottom: expandedTheme === theme.theme_id ? 'none' : '1px solid #2a2a2e' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600 }}>#{idx + 1}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ fontWeight: 600 }}>{theme.theme_name}</div>
                    <div style={{ color: '#a0a0a5', fontSize: '11px', marginTop: '4px' }}>
                      Stages: {theme.dominant_stages.join(', ') || 'N/A'}
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ 
                      background: idx < 3 ? 'rgba(241, 58, 177, 0.1)' : 'rgba(255,255,255,0.05)', 
                      color: idx < 3 ? '#F13AB1' : '#fff', 
                      padding: '4px 8px', borderRadius: '4px', fontWeight: 600 
                    }}>
                      {theme.pm_priority_score.toFixed(3)}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>{theme.prevalence}</td>
                  <td style={{ padding: '12px 16px' }}>{theme.severity}</td>
                  <td style={{ padding: '12px 16px' }}>{theme.metric_proximity}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <button 
                      onClick={() => toggleExamples(theme.theme_id)}
                      style={{ background: 'transparent', border: '1px solid #F13AB1', color: '#F13AB1', padding: '4px 8px', borderRadius: '4px', fontSize: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
                    >
                      <MessageSquare size={14} />
                      {expandedTheme === theme.theme_id ? 'Hide' : 'Examples'}
                    </button>
                  </td>
                </tr>
                {expandedTheme === theme.theme_id && (
                  <tr style={{ borderBottom: '1px solid #2a2a2e' }}>
                    <td colSpan="7" style={{ padding: '0 16px 16px 16px' }}>
                      <div style={{ background: '#121214', borderRadius: '8px', padding: '16px', border: '1px solid #333' }}>
                        <div style={{ fontSize: '12px', color: '#F13AB1', textTransform: 'uppercase', marginBottom: '12px', fontWeight: 600 }}>Representative Verbatims</div>
                        {loadingExamples ? (
                          <div style={{ color: '#a0a0a5', fontSize: '13px' }}>Loading examples...</div>
                        ) : (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {examples.map((ex, i) => (
                              <div key={i} style={{ display: 'flex', gap: '12px' }}>
                                <div style={{ color: '#FD913C', flexShrink: 0, width: '80px', fontSize: '12px', fontWeight: 600 }}>{ex.source_type}</div>
                                <div style={{ color: '#e2e8f0', fontSize: '13px', lineHeight: 1.4, fontStyle: 'italic' }}>"{ex.raw_text}"</div>
                              </div>
                            ))}
                            {examples.length === 0 && <div style={{ color: '#a0a0a5', fontSize: '13px' }}>No examples available.</div>}
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
