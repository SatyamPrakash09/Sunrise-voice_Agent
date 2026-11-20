from database import book_slot_safely, init_db
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, room_io, function_tool
from livekit.agents import AgentSession, Agent
from livekit.plugins import silero, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

init_db()


class SalonAssistant(Agent):

    def __init__(self, tools=None):
        super().__init__(
            instructions=(
                "You are a professional, polite voice receptionist for Sunrise"
                " Salon in Indiranagar, Bengaluru. Answer questions strictly from"
                " business data. Never invent pricing, membership plans, or"
                " unoffered services. If unsure, admit it. Use tools to check"
                " availability and book slots."
            ),
            tools=tools or [],
        )


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    @function_tool
    def book_appointment(
        customer_name: str, service: str, stylist: str, slot_time: str
    ):
        """Book a salon appointment for a customer with a specific stylist and time."""
        return book_slot_safely(customer_name, service, stylist, slot_time)

    session = AgentSession(
        stt="assemblyai/universal-streaming:en",  # Speech-to-text provider
        llm="openai/gpt-4.1-mini",                # Language model for responses
        tts="cartesia/sonic-3",                   # Text-to-speech voice
        vad=silero.VAD.load(),                    # Voice activity detection
        turn_detection=MultilingualModel(),
    )

    assistant = SalonAssistant(tools=[book_appointment])
    await session.start(
        agent=assistant,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=noise_cancellation.BVC(),  # Background voice cancellation
            ),
        ),
    )

    await session.say(
        "Hello! Welcome to Sunrise Salon. How can I help you with your"
        " appointment today?",
        allow_interruptions=True,
    )


if __name__ == "__main__":
    # Run the worker pointing to LiveKit Cloud / Server
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
