import os
os.environ["LIVEKIT_AGENTS_PRELOAD_LOCAL_INFERENCE"] = "0"

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from database import init_db
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, JobExecutorType, cli, room_io, function_tool
from livekit.agents import AgentSession, Agent
from livekit.plugins import silero, noise_cancellation
from controllers import (
    manage_appointment_db,
    check_availability_db,
    get_faq_from_db,
    get_service_from_db,
    get_stylist_from_db,
)


@function_tool(
    description=(
        "Check if a stylist is available on a specific date or time slot, or see all booked slots. "
        "Use this BEFORE booking whenever the user asks about availability or mentions a time. "
        "stylist: stylist name (Anita Rao, Rahul Shetty, Kavya Nair). "
        "slot_time: ISO 8601 string, e.g. '2026-11-23T11:00:00' or date '2026-11-23'."
    )
)
async def check_availability(stylist: str, slot_time: str):
    return await check_availability_db(stylist, slot_time)


@function_tool(
    description=(
        "Book or cancel an appointment. "
        "Call this ONLY after collecting ALL required fields from the user and user explicitly agrees: "
        "action ('book' or 'cancel'), customer_name (full real name of customer), service (exact service name), "
        "stylist (exact stylist name), slot_time (ISO 8601 format: YYYY-MM-DDTHH:MM:SS, "
        "e.g. '2026-11-23T11:00:00'). NEVER invent or use dummy names like 'A, b, c, d' or 'Jane'. "
        "Call this tool ONLY ONCE per booking."
    )
)
async def manage_appointment(
    action: str,
    customer_name: str,
    service: str,
    stylist: str,
    slot_time: str,
):
    return await manage_appointment_db(action, customer_name, service, stylist, slot_time)


@function_tool(
    description=(
        "Get FAQ about the Salon. Use for questions about payment, parking, "
        "walk-ins, cancellation policy, opening hours, and general policies. "
        "Pass the topic keyword e.g. 'payment', 'parking', 'policies'."
    )
)
async def get_faq(topic: str):
    return await get_faq_from_db(topic)


@function_tool(
    description=(
        "Get details and pricing for a specific service. "
        "Use when the user asks about a service cost or what services are available."
    )
)
async def get_service(service_name: str):
    return await get_service_from_db(service_name)


@function_tool(
    description=(
        "Get a stylist's specialties, working days, and working hours. "
        "Use when the user asks about a stylist or wants to know who does what."
    )
)
async def get_stylist(stylist_name: str):
    return await get_stylist_from_db(stylist_name)


class SalonAssistant(Agent):

    def __init__(self):
        tz = ZoneInfo("Asia/Kolkata")
        now = datetime.now(tz)
        today_str = now.strftime("%A, %d %B %Y")
        time_str = now.strftime("%I:%M %p")
        tomorrow = now + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%A, %d %B %Y")
        today_iso = now.strftime("%Y-%m-%d")
        tomorrow_iso = tomorrow.strftime("%Y-%m-%d")

        instructions = (
            f"You are a professional, polite voice receptionist for Sunrise Salon "
            f"in Indiranagar, Bengaluru. Keep all responses short and conversational — "
            f"this is a voice call, so avoid lists or long paragraphs.\n\n"

            f"REAL-TIME CLOCK & CALENDAR (Asia/Kolkata - IST):\n"
            f"- Current Real-Time Date: {today_str}\n"
            f"- Current Local Time: {time_str} IST\n"
            f"- Current Year: {now.year}\n"
            f"- 'Today' is: {today_iso} ({today_str})\n"
            f"- 'Tomorrow' is: {tomorrow_iso} ({tomorrow_str})\n"
            f"- STRICT CALENDAR RULE: The year is {now.year}. Under NO circumstances book in 2024 or any past year. "
            f"Every single booking MUST be in {now.year} or later.\n\n"

            f"ACCENT & INDIAN ENGLISH HANDLING:\n"
            f"- You are serving callers in Bengaluru, India. Customers speak with Indian accents and may use Indian English terms (e.g., 'Rs 600', 'need a clean-up', 'is parking there', 'today evening', 'slot').\n"
            f"- Pay close attention to Indian names (Anita Rao, Rahul Shetty, Kavya Nair) and services. If the STT transcript has minor phonetic variations, match them intelligently to known staff and services.\n\n"

            f"TOOL USAGE & BOOKING RULES:\n"
            f"- Use check_availability FIRST whenever the user asks about a date or time slot, to verify if the stylist is free.\n"
            f"- Use get_service when the user asks about a service or price.\n"
            f"- Use get_stylist when the user asks about a stylist's schedule or specialties.\n"
            f"- Use get_faq for questions about payment, parking, walk-ins, or policies.\n\n"

            f"BOOKING CONFIRMATION & DUPLICATE PREVENTION:\n"
            f"- To book an appointment, collect all 4 items: Customer Full Name, Service, Stylist, Date/Time (30-min slots).\n"
            f"- NEVER book with placeholder or dummy names (like 'Jane', 'A, b, c, d', 'test'). Always ask the customer for their real name.\n"
            f"- Call manage_appointment ONLY ONCE when the user has confirmed they want to book.\n"
            f"- If a slot is already booked, check_availability or manage_appointment will notify you — politely offer the next available slot.\n\n"

            f"CONSTRAINTS:\n"
            f"- Never invent pricing, services, or availability.\n"
            f"- Strictly use data returned by tools.\n"
            f"- Closed on Sundays. Slots are 30 minutes each (e.g. 10:00, 10:30, 11:00)."
        )

        super().__init__(
            instructions=instructions,
            tools=[check_availability, manage_appointment, get_faq, get_service, get_stylist],
        )





async def entrypoint(ctx: JobContext):
    # Connect room audio immediately so user receives greeting right away
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Initialize DB safely without blocking audio
    try:
        await init_db()
    except Exception as e:
        print(f"Database initialization warning: {e}")

    session = AgentSession(
        # Deepgram Nova-3 provides superior accuracy for Indian English and global accents
        stt="deepgram/nova-3:en",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-3",
        vad=silero.VAD.load(),
        stt_context_options={
            "keyterms": [
                "Sunrise Salon",
                "Indiranagar",
                "Bengaluru",
                "Anita Rao",
                "Rahul Shetty",
                "Kavya Nair",
                "Haircut",
                "Hair spa",
                "Blow dry",
                "Clean-up",
                "Facial",
                "UPI",
            ],
        },
    )

    assistant = SalonAssistant()
    await session.start(
        agent=assistant,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=noise_cancellation.BVCTelephony(),  # Background voice cancellation
            ),
        ),
    )

    await session.say(
        "Hello! Welcome to Sunrise Salon. How can I help you with your"
        " appointment today?",
        allow_interruptions=False,
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            job_executor_type=JobExecutorType.THREAD,
            load_threshold=float("inf"),
            num_idle_processes=1,
            host="127.0.0.1",
        )
    )
