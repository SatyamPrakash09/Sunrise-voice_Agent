import { Room, RoomEvent, Track } from 'livekit-client'
import {  useRef, useState } from 'react'

export default function App() {
  const [active, setActive] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [status, setStatus] = useState('Disconnected')
  const audioRef = useRef(null)
  const roomRef = useRef(null)

  const toggleCall = async () => {
    if (!active) {
      setStatus('Connecting to LiveKit...')
      try {
        const res = await fetch('/token')
        const data = await res.json()

        const room = new Room()
        roomRef.current = room

        room.on(
            RoomEvent.TrackSubscribed,
            (track, publication, participant) => {
              if (track.kind === Track.Kind.Audio) {
                track.attach(audioRef.current)
              }
            }
        )

        await room.connect(data.url, data.token)
        await room.localParticipant.setMicrophoneEnabled(true)

        setActive(true)
        setIsMuted(false)
        setStatus('Connected - Speak now!')
      } catch (e) {
        console.error(e)
        setStatus('Connection failed.')
      }
    } else {
      if (roomRef.current) {
        await roomRef.current.disconnect()
      }
      setActive(false)
      setIsMuted(false)
      setStatus('Disconnected')
    }
  }

  // Toggle Microphone Mute / Unmute
  const toggleMic = async () => {
    if (!roomRef.current || !active) return

    const newMuteState = !isMuted
    // setMicrophoneEnabled(false) mutes the track; true unmutes it
    await roomRef.current.localParticipant.setMicrophoneEnabled(
        !newMuteState
    )
    setIsMuted(newMuteState)
  }

  return (
      <div className="bg-gray-900 text-white flex flex-col items-center justify-center h-screen">
        <div className="bg-gray-800 p-8 rounded-2xl shadow-2xl text-center max-w-md w-full border border-gray-700">
          <h1 className="text-2xl font-bold mb-2">Sunrise Salon</h1>
          <p className="text-gray-400 text-sm mb-6">
            AI Voice Receptionist for bookings, hours, and services.
          </p>

          <div
              className={`mb-6 text-sm font-medium ${active ? 'text-emerald-400' : 'text-yellow-400'}`}
          >
            Status: {status}
          </div>

          <div className="flex gap-4">
            {/* Call Toggle Button */}
            <button
                onClick={toggleCall}
                className={`flex-1 transition font-semibold py-3 rounded-xl shadow-lg ${
                    active
                        ? 'bg-rose-600 hover:bg-rose-500'
                        : 'bg-emerald-600 hover:bg-emerald-500'
                }`}
            >
              {active ? 'End Call' : 'Start Call'}
            </button>

            {/* Microphone Mute/Unmute Button (Visible only when in a call) */}
            {active && (
                <button
                    onClick={toggleMic}
                    className={`px-5 transition font-semibold py-3 rounded-xl shadow-lg ${
                        isMuted
                            ? 'bg-amber-600 hover:bg-amber-500'
                            : 'bg-gray-700 hover:bg-gray-600 border border-gray-600'
                    }`}
                >
                  {isMuted ? 'Unmute' : 'Mute'}
                </button>
            )}
          </div>
        </div>

        {/* Hidden audio element for agent voice output */}
        <audio ref={audioRef} autoPlay />
      </div>
  )
}