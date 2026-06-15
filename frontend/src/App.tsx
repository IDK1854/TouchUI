import { useState, useEffect, useCallback } from 'react'
import './App.css'
import { TradingViewIcon, DiscordIcon, YouTubeIcon, VolumeUpIcon, VolumeDownIcon, SpotifyIcon, PlayIcon, PauseIcon, SkipBackIcon, SkipForwardIcon, SwitchIcon, MixerIcon, BackIcon, VolumeMuteIcon } from './icons'

const API = "http://127.0.0.1:8000/api"

function App() {
  const [volume, setVolume] = useState(50)
  const [stats, setStats] = useState({ cpu: 0, ram: 0 })
  const [now, setNow] = useState(new Date())
  const [media, setMedia] = useState({ playing: false, title: '', artist: '' })
  const [view, setView] = useState<'main' | 'mixer'>('main')
  const [mixerSessions, setMixerSessions] = useState<{pid: number, name: string, volume: number, muted: boolean}[]>([])

  useEffect(() => {
    const clockId = setInterval(() => setNow(new Date()), 1000)

    fetch(`${API}/volume`).then(r => r.json()).then(d => setVolume(d.volume ?? 50)).catch(() => {})

    const statsId = setInterval(() => {
      fetch(`${API}/system`).then(r => r.json()).then(setStats).catch(() => {})
      fetch(`${API}/media`).then(r => r.json()).then(setMedia).catch(() => {})
      fetch(`${API}/mixer`).then(r => r.json()).then(d => setMixerSessions(d.sessions || [])).catch(() => {})
    }, 1500)
    
    fetch(`${API}/system`).then(r => r.json()).then(setStats).catch(() => {})
    fetch(`${API}/media`).then(r => r.json()).then(setMedia).catch(() => {})
    fetch(`${API}/mixer`).then(r => r.json()).then(d => setMixerSessions(d.sessions || [])).catch(() => {})

    return () => { clearInterval(clockId); clearInterval(statsId) }
  }, [])

  const launch = useCallback((id: string) => {
    fetch(`${API}/launch/${id}`, { method: 'POST' }).catch(() => {})
  }, [])

  const changeVol = useCallback(async (v: number) => {
    const clamped = Math.max(0, Math.min(100, v))
    setVolume(clamped)
    try { await fetch(`${API}/volume/${clamped}`, { method: 'POST' }) } catch {}
  }, [])

  const mediaAction = useCallback(async (action: string) => {
    // Optimistic UI update
    if (action === 'playpause') {
       setMedia(prev => ({ ...prev, playing: !prev.playing }))
    }
    try { await fetch(`${API}/media/${action}`, { method: 'POST' }) } catch {}
  }, [])

  const changeMixerVol = useCallback(async (pid: number, v: number) => {
    const clamped = Math.max(0, Math.min(100, v))
    setMixerSessions(prev => prev.map(s => s.pid === pid ? { ...s, volume: clamped } : s))
    try { await fetch(`${API}/mixer/${pid}/${clamped}`, { method: 'POST' }) } catch {}
  }, [])

  const toggleMute = useCallback(async (pid: number, currentState: boolean) => {
    const newState = !currentState
    setMixerSessions(prev => prev.map(s => s.pid === pid ? { ...s, muted: newState } : s))
    try { await fetch(`${API}/mixer/${pid}/mute/${newState ? 1 : 0}`, { method: 'POST' }) } catch {}
  }, [])

  const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  const dateStr = now.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' })

  if (view === 'mixer') {
    return (
      <div className="dashboard">
        <div className="top-bar">
          <div className="clock">
            <span className="clock-time">{timeStr}</span>
            <span className="clock-date">{dateStr}</span>
          </div>
        </div>
        <div className="mixer-view">
          <div className="mixer-header">
            <button className="back-btn" onClick={() => setView('main')}>
              <BackIcon /> Back
            </button>
            <span className="mixer-title">Volume Mixer</span>
          </div>
          <div className="mixer-list">
            {mixerSessions.map(s => (
              <div key={s.pid} className="mixer-item">
                <div className="mixer-item-header">
                  <div className="mixer-app-name">{s.name}</div>
                  <div className="mixer-app-vol">{s.muted ? 'Muted' : `${s.volume}%`}</div>
                </div>
                <div className="mixer-slider-row">
                  <button className={`mute-btn ${s.muted ? 'muted' : ''}`} onClick={() => toggleMute(s.pid, s.muted)}>
                    {s.muted ? <VolumeMuteIcon /> : <VolumeUpIcon />}
                  </button>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={s.volume}
                    onChange={e => changeMixerVol(s.pid, parseInt(e.target.value))}
                    className={`volume-slider ${s.muted ? 'muted-slider' : ''}`}
                  />
                </div>
              </div>
            ))}
            {mixerSessions.length === 0 && (
              <div className="mixer-empty">No active audio applications found.</div>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      {/* ── Top Bar ── */}
      <div className="top-bar">
        <div className="clock">
          <span className="clock-time">{timeStr}</span>
          <span className="clock-date">{dateStr}</span>
        </div>

        <div className="system-stats">
          <div className="stat">
            <span className="stat-label">CPU</span>
            <div className="stat-track">
              <div className="stat-fill cpu" style={{ width: `${stats.cpu}%` }} />
            </div>
            <span className="stat-value">{Math.round(stats.cpu)}%</span>
          </div>
          <div className="stat">
            <span className="stat-label">RAM</span>
            <div className="stat-track">
              <div className="stat-fill ram" style={{ width: `${stats.ram}%` }} />
            </div>
            <span className="stat-value">{Math.round(stats.ram)}%</span>
          </div>
        </div>
      </div>

      {/* ── Main Content ── */}
      <div className="main-content">
        {/* Left: App Launcher */}
        <div className="apps-panel">
          <span className="section-label">Quick Launch</span>
          <div className="apps-grid">
            <button className="app-btn tradingview" onClick={() => launch('tradingview')}>
              <TradingViewIcon />
              <span>TradingView</span>
            </button>
            <button className="app-btn discord" onClick={() => launch('discord')}>
              <DiscordIcon />
              <span>Discord</span>
            </button>
            <button className="app-btn youtube" onClick={() => launch('youtube')}>
              <YouTubeIcon />
              <span>YouTube</span>
            </button>
            <button className="app-btn spotify" onClick={() => launch('spotify')}>
              <SpotifyIcon />
              <span>Spotify</span>
            </button>
          </div>
        </div>

        {/* Right: Controls */}
        <div className="controls-panel">
          {/* Media Card */}
          <div className="control-card media-card">
            {media.title ? (
              <>
                <div className="media-info">
                  <div className="media-title">{media.title}</div>
                  <div className="media-artist">{media.artist}</div>
                </div>
                <div className="media-controls">
                  <button className="media-btn" onClick={() => mediaAction('prev')}><SkipBackIcon /></button>
                  <button className="media-btn play-btn" onClick={() => mediaAction('playpause')}>
                    {media.playing ? <PauseIcon /> : <PlayIcon />}
                  </button>
                  <button className="media-btn" onClick={() => mediaAction('next')}><SkipForwardIcon /></button>
                  <button className="media-btn" onClick={() => mediaAction('switch')}><SwitchIcon /></button>
                </div>
              </>
            ) : (
              <div className="media-empty">No Media Playing</div>
            )}
          </div>

          {/* Volume Card */}
          <div className="control-card volume-card">
            <div className="volume-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <VolumeUpIcon />
                <div className="volume-pct">{volume}<span>%</span></div>
              </div>
              <button className="mixer-btn" onClick={() => setView('mixer')}>
                <MixerIcon />
              </button>
            </div>
            <div className="slider-row">
              <button className="vol-btn" onClick={() => changeVol(volume - 5)}>
                <VolumeDownIcon />
              </button>
              <input
                type="range"
                min="0"
                max="100"
                value={volume}
                onChange={e => changeVol(parseInt(e.target.value))}
                className="volume-slider"
              />
              <button className="vol-btn" onClick={() => changeVol(volume + 5)}>
                <VolumeUpIcon />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
