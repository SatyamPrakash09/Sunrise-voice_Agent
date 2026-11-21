import { Room, RoomEvent, Track } from 'livekit-client'
import { useRef, useState } from 'react'
import mascotImg from './assets/mascot.jpg'
import './App.css'

/* ── SVG Icons (inline to avoid extra deps) ────────────────── */
const PhoneIcon = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.79 19.79 0 0 1 2.12 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
  </svg>
)
const PhoneOffIcon = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="m10.68 13.31 1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 18.92 14v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07"/>
    <path d="M4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91"/>
    <line x1="1" y1="1" x2="23" y2="23"/>
  </svg>
)
const MicIcon = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="1" width="6" height="12" rx="3"/>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/>
    <line x1="8" y1="23" x2="16" y2="23"/>
  </svg>
)
const MicOffIcon = () => (
  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="1" y1="1" x2="23" y2="23"/>
    <path d="M9 9v3a3 3 0 0 0 5.12 2.12M15 9.34V4a3 3 0 0 0-5.94-.6"/>
    <path d="M17 16.95A7 7 0 0 1 5 12v-2m14 0v2c0 .77-.13 1.52-.36 2.22"/>
    <line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/>
  </svg>
)

/* ── Audio Visualizer (animated bars while on call) ─────────── */
function AudioVisualizer() {
  const bars = Array.from({ length: 12 }, (_, i) => ({
    delay: `${i * 0.08}s`,
    duration: `${0.6 + Math.random() * 0.5}s`,
    maxH: `${10 + Math.random() * 24}px`,
  }))
  return (
    <div className="audio-visualizer">
      {bars.map((b, i) => (
        <div
          key={i}
          className="audio-bar"
          style={{ '--delay': b.delay, '--duration': b.duration, '--max-h': b.maxH }}
        />
      ))}
    </div>
  )
}

const BACKEND_URL = (
  import.meta.env.VITE_BACKEND_URL ||
  import.meta.env.BACKEND_URL ||
  ''
).replace(/\/+$/, '')

/* ── Main App ──────────────────────────────────────────────── */
export default function App() {
  const [active, setActive] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [status, setStatus] = useState('disconnected') // disconnected | connecting | connected
  const audioRef = useRef(null)
  const roomRef = useRef(null)

  const statusLabels = {
    disconnected: 'Ready to connect',
    connecting: 'Connecting…',
    connected: 'On call — speak now!',
  }

  const toggleCall = async () => {
    if (!active) {
      setStatus('connecting')
      try {
        const res = await fetch(`${BACKEND_URL}/token`)
        if (!res.ok) {
          throw new Error(`Failed to fetch token: ${res.statusText}`)
        }
        const data = await res.json()

        const room = new Room()
        roomRef.current = room

        room.on(RoomEvent.TrackSubscribed, (track) => {
          if (track.kind === Track.Kind.Audio) {
            track.attach(audioRef.current)
          }
        })

        room.on(RoomEvent.Disconnected, () => {
          setActive(false)
          setIsMuted(false)
          setStatus('disconnected')
          roomRef.current = null
        })

        await room.connect(data.url, data.token)
        await room.localParticipant.setMicrophoneEnabled(true)

        setActive(true)
        setIsMuted(false)
        setStatus('connected')
      } catch (e) {
        console.error(e)
        setStatus('disconnected')
      }
    } else {
      if (roomRef.current) {
        await roomRef.current.disconnect()
        roomRef.current = null
      }
      setActive(false)
      setIsMuted(false)
      setStatus('disconnected')
    }
  }

  const toggleMic = async () => {
    if (!roomRef.current || !active) return
    const newMuteState = !isMuted
    await roomRef.current.localParticipant.setMicrophoneEnabled(!newMuteState)
    setIsMuted(newMuteState)
  }

  return (
    <>
      {/* Animated background blobs */}
      <div className="bg-blob bg-blob-1" />
      <div className="bg-blob bg-blob-2" />
      <div className="bg-blob bg-blob-3" />

      <div className="salon-page">
        {/* Top Bar */}
        <div className="top-bar">
          <div className="top-bar-brand">
            <span className="top-bar-icon">✂️</span>
            <span className="top-bar-name">Sunrise Salon</span>
          </div>
          <span className="top-bar-location">
            📍 Indiranagar, Bengaluru
          </span>
        </div>

        {/* Main Card */}
        <div className="salon-card">
          {/* Mascot */}
          <div className="mascot-wrapper">
            <img src={mascotImg} alt="Sunrise Salon Assistant" className="mascot-img" />
            <div className={`mascot-pulse-ring ${active ? 'active' : ''}`} />
          </div>

          <h1 className="salon-title">Sunrise Salon</h1>
          <p className="salon-subtitle">
            AI Voice Assistant &nbsp;·&nbsp; Bookings, Services &amp; More
          </p>

          {/* Status */}
          <div className={`status-pill ${status}`}>
            <span className="status-dot" />
            {statusLabels[status]}
          </div>

          {/* Audio visualizer while connected */}
          {active && <AudioVisualizer />}

          {/* Chat bubble hint */}
          {!active && (
            <div className="chat-bubble">
              👋 Hi! Tap <strong>Start Call</strong> to speak with me. I can book appointments, check availability, and answer questions!
            </div>
          )}
          {active && !isMuted && (
            <div className="chat-bubble">
              🎙️ I'm listening… ask me about services, pricing, or book an appointment!
            </div>
          )}
          {active && isMuted && (
            <div className="chat-bubble">
              🔇 Microphone muted. Tap <strong>Unmute</strong> when you're ready to speak.
            </div>
          )}

          {/* Buttons */}
          <div className="btn-row">
            <button
              onClick={toggleCall}
              className={`btn ${active ? 'btn-end' : 'btn-call'}`}
            >
              {active ? <PhoneOffIcon /> : <PhoneIcon />}
              {active ? 'End Call' : 'Start Call'}
            </button>

            {active && (
              <button
                onClick={toggleMic}
                className={`btn btn-mute ${isMuted ? 'muted' : ''}`}
                title={isMuted ? 'Unmute' : 'Mute'}
              >
                {isMuted ? <MicOffIcon /> : <MicIcon />}
              </button>
            )}
          </div>
        </div>

        {/* Info Cards */}
        <div className="info-row">
          <div className="info-card">
            <span className="info-card-icon">🕐</span>
            <span className="info-card-label">Hours</span>
            <span className="info-card-value">Mon–Sat · 9 AM – 8 PM</span>
          </div>
          <div className="info-card">
            <span className="info-card-icon">💇</span>
            <span className="info-card-label">Services</span>
            <span className="info-card-value">Cuts, Colour, Spa &amp; Facials</span>
          </div>
          <div className="info-card">
            <span className="info-card-icon">💳</span>
            <span className="info-card-label">Payment</span>
            <span className="info-card-value">Cash, UPI &amp; Cards</span>
          </div>
        </div>

        <div className="salon-footer">
          12 Lake Road, Indiranagar, Bengaluru &nbsp;·&nbsp; Closed Sundays
        </div>
      </div>

      {/* Hidden audio element for agent voice output */}
      <audio ref={audioRef} autoPlay />
    </>
  )
}