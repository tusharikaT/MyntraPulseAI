import React, { useState } from 'react'
import axios from 'axios'
import { Bot, Send, User, ExternalLink, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'

const RESEARCH_QUESTIONS = [
  "Why do users struggle to discover new music?", // Adapting slightly to match the aesthetic or keeping original ones
  "What are the most common frustrations with recommendations?",
  "What listening behaviors are users trying to achieve?",
  "What causes users to repeatedly listen to the same content?",
  "Which user segments experience different discovery challenges?",
  "What unmet needs emerge consistently across reviews?",
  "Which Spotify discovery features frustrate users the most?",
  "What kind of new music do users want to find?",
  "Does Spotify understand users' mood and current listening context?",
  "Do users want more control over their recommendations?",
  "Where do users go when Spotify discovery fails?",
  "How do users feel when recommendations become repetitive or irrelevant?"
];

// Let's use the actual questions from the codebase to be accurate to the domain, but styled like the screenshot.
const ACTUAL_QUESTIONS = [
  "Why do users add fashion products to their wishlist?",
  "What prevents wishlisted products from eventually being purchased?",
  "What uncertainties remain after users have identified a product they like?",
  "What causes users to postpone a purchase?",
  "How do users compare multiple shortlisted products?",
  "What information do users seek outside Myntra/AJIO before purchasing?",
  "What role do fit, size, styling, price, reviews, occasion and social validation play?",
  "When do users use the wishlist as genuine purchase intent versus simply as a bookmarking mechanism?",
  "How do these behaviors differ across user segments?",
  "What unmet needs emerge consistently across user conversations?",
  "Which new wishlist features would most effectively resolve user friction?",
  "How can Myntra increase the conversion rate of saved items during major sale events?"
];

export default function DiscoveryCopilot() {
  const [messages, setMessages] = useState([
    { 
      role: 'ai', 
      content: "Hi! I'm your Discovery Copilot. Ask me anything about the user feedback dataset, like *'What are the biggest issues users face during checkout?'* or *'Are there any complaints about price drops?'*" 
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [expandedEvidenceIdx, setExpandedEvidenceIdx] = useState(null)

  const askCopilot = async (question) => {
    if (!question.trim()) return
    
    setIsChatOpen(true)
    const newMsg = { role: 'user', content: question }
    setMessages([...messages, newMsg])
    setInput('')
    setLoading(true)
    setExpandedEvidenceIdx(null)

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/copilot/ask', { 
        question: question 
      })
      
      setMessages(prev => [...prev, { 
        role: 'ai', 
        content: response.data.answer,
        suggestions: response.data.suggested_followups,
        sources: response.data.sources
      }])
    } catch (error) {
      console.error(error)
      setMessages(prev => [...prev, { role: 'ai', content: 'Sorry, I encountered an error communicating with the backend API.' }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      askCopilot(input)
    }
  }

  const parseMarkdown = (text) => {
    if (!text) return { __html: '' }
    let html = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\[Record (\d+)\]/g, '<span style="color: #F13AB1; font-weight: 600;">[Record $1]</span>')
      .replace(/\n/g, '<br />')
    return { __html: html }
  }

  const toggleEvidence = (idx) => {
    if (expandedEvidenceIdx === idx) {
      setExpandedEvidenceIdx(null)
    } else {
      setExpandedEvidenceIdx(idx)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)', position: 'relative', overflow: 'hidden' }}>
      
      {/* Background Dashboard: Grid of Questions */}
      <div style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
        
        {isChatOpen ? (
          // Chat View
          <div style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px', paddingBottom: '120px' }}>
            {messages.map((msg, idx) => (
              <div key={idx} style={{ display: 'flex', gap: '16px', flexDirection: msg.role === 'user' ? 'row-reverse' : 'row' }}>
                <div style={{ 
                  width: '32px', height: '32px', borderRadius: '50%', 
                  background: msg.role === 'user' ? '#333' : '#F13AB1',
                  color: msg.role === 'user' ? '#fff' : '#fff',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
                }}>
                  {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                </div>
                <div style={{ 
                  background: msg.role === 'user' ? '#29303e' : 'transparent',
                  border: msg.role === 'ai' ? '1px solid rgba(255,255,255,0.1)' : 'none',
                  color: '#e2e8f0',
                  padding: '16px', borderRadius: '12px', maxWidth: '100%', flex: 1,
                  lineHeight: 1.6, fontSize: '15px'
                }}>
                  <div dangerouslySetInnerHTML={parseMarkdown(msg.content)} />
                  
                  {/* Inline Evidence Panel Toggle */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div style={{ marginTop: '16px' }}>
                      <button 
                        onClick={() => toggleEvidence(idx)}
                        style={{ 
                          background: 'transparent', border: '1px solid #F13AB1', color: '#F13AB1', 
                          padding: '6px 12px', borderRadius: '6px', fontSize: '13px', cursor: 'pointer',
                          display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600
                        }}
                      >
                        {expandedEvidenceIdx === idx ? <ChevronUp size={14}/> : <ChevronDown size={14}/>}
                        {expandedEvidenceIdx === idx ? 'Hide Evidence' : `View Evidence (${msg.sources.length} sources)`}
                      </button>
                      
                      {expandedEvidenceIdx === idx && (
                        <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '12px', padding: '16px', background: '#121214', borderRadius: '8px', border: '1px solid #333' }}>
                          {msg.sources.map((src, i) => (
                            <div key={i} style={{ borderBottom: i === msg.sources.length - 1 ? 'none' : '1px solid #333', paddingBottom: i === msg.sources.length - 1 ? 0 : '12px' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                                <span style={{ fontSize: '12px', fontWeight: 600, color: '#F13AB1' }}>Record {i+1}</span>
                                <span style={{ fontSize: '11px', color: '#a0a0a5', background: '#29303e', padding: '2px 6px', borderRadius: '4px' }}>
                                  {src.platform}
                                </span>
                              </div>
                              <div style={{ fontSize: '13px', lineHeight: 1.5, color: '#a0a0a5', marginBottom: '8px', fontStyle: 'italic' }}>
                                "{src.quote}"
                              </div>
                              {src.original_url && (
                                <a href={src.original_url} target="_blank" rel="noreferrer" style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: '#60a5fa', textDecoration: 'none' }}>
                                  View original <ExternalLink size={12} />
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {msg.suggestions && msg.suggestions.length > 0 && (
                    <div style={{ marginTop: '20px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {msg.suggestions.map((s, i) => (
                        <button key={i} onClick={() => askCopilot(s)} style={{ 
                          background: 'rgba(241, 58, 177, 0.1)', color: '#F13AB1', border: '1px solid rgba(241, 58, 177, 0.3)', 
                          padding: '6px 12px', borderRadius: '16px', fontSize: '12px', cursor: 'pointer'
                        }}>
                          {s}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {loading && (
              <div style={{ display: 'flex', gap: '16px' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#F13AB1', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Bot size={18} />
                </div>
                <div style={{ padding: '16px', color: '#a0a0a5', fontStyle: 'italic' }}>
                  Analyzing feedback records and generating response...
                </div>
              </div>
            )}

            {!loading && (
              <div style={{ marginTop: '24px', paddingTop: '24px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ fontSize: '14px', color: '#a0a0a5', marginBottom: '16px' }}>More questions to explore:</div>
                <div className="grid-3" style={{ gap: '16px' }}>
                  {ACTUAL_QUESTIONS.map((q, idx) => {
                    const num = (idx + 1).toString().padStart(2, '0');
                    return (
                      <div 
                        key={idx} 
                        onClick={() => askCopilot(q)}
                        style={{
                          background: '#121214', border: '1px solid rgba(255,255,255,0.05)',
                          padding: '16px', borderRadius: '8px', cursor: 'pointer',
                          display: 'flex', alignItems: 'flex-start', gap: '12px',
                          transition: 'all 0.2s'
                        }}
                        onMouseOver={(e) => {
                          e.currentTarget.style.backgroundColor = '#1c1c1f'
                        }}
                        onMouseOut={(e) => {
                          e.currentTarget.style.backgroundColor = '#121214'
                        }}
                      >
                        <div style={{ fontSize: '14px', fontWeight: 800, color: '#F13AB1', marginTop: '2px' }}>{num}</div>
                        <div style={{ fontSize: '13px', color: '#e2e8f0', lineHeight: 1.5 }}>{q}</div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        ) : (
          // Grid View (First Load)
          <div className="grid-3" style={{ gap: '16px', paddingBottom: '100px', maxWidth: '1200px', margin: '0 auto' }}>
            {ACTUAL_QUESTIONS.map((q, idx) => {
              const num = (idx + 1).toString().padStart(2, '0');
              return (
                <div 
                  key={idx} 
                  onClick={() => askCopilot(q)}
                  style={{
                    background: '#121214', border: '1px solid rgba(255,255,255,0.05)',
                    padding: '20px', borderRadius: '8px', cursor: 'pointer',
                    display: 'flex', alignItems: 'flex-start', gap: '16px',
                    transition: 'all 0.2s'
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.backgroundColor = '#1c1c1f'
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.backgroundColor = '#121214'
                  }}
                >
                  <div style={{ fontSize: '16px', fontWeight: 800, color: '#F13AB1', marginTop: '2px' }}>{num}</div>
                  <div style={{ fontSize: '14px', color: '#e2e8f0', lineHeight: 1.5 }}>{q}</div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Pinned Input Bar at Bottom (Spotify Style) */}
      <div style={{ 
        position: 'absolute', bottom: '0', left: '0', right: '0', 
        padding: '24px', background: '#0a0a0c', display: 'flex', justifyContent: 'center',
        background: 'linear-gradient(to top, #0a0a0c 80%, transparent)'
      }}>
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center', width: '100%', maxWidth: '1200px', gap: '12px' }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <textarea 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Type a question, or tap one below to begin..."
              style={{ 
                width: '100%', background: '#121214', color: '#fff', border: '1px solid #333', 
                borderRadius: '8px', padding: '16px 20px', fontSize: '15px', 
                resize: 'none', height: '56px', outline: 'none'
              }}
              onFocus={(e) => e.target.style.borderColor = '#F13AB1'}
              onBlur={(e) => e.target.style.borderColor = '#333'}
            />
          </div>
          <button 
            onClick={() => askCopilot(input)}
            disabled={loading || !input.trim()}
            style={{ 
              background: (loading || !input.trim()) ? '#333' : '#F13AB1', 
              color: '#fff', border: 'none', borderRadius: '8px',
              padding: '0 24px', height: '56px', cursor: (loading || !input.trim()) ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '15px',
              transition: 'all 0.2s'
            }}
          >
            Send
          </button>
        </div>
      </div>
      
    </div>
  )
}
