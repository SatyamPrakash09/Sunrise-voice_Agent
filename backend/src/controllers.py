from database import FAQ, Service, Stylist, AsyncSessionLocal, Appointment
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy import or_
import re

_IST = ZoneInfo("Asia/Kolkata")


from datetime import timedelta

def _parse_datetime(slot_str: str) -> datetime | None:
    """Robustly parse ISO8601, relative dates ('today', 'tomorrow', day names), and times into a naive datetime in IST."""
    now = datetime.now(_IST).replace(tzinfo=None)
    if not slot_str or not slot_str.strip():
        return now.replace(second=0, microsecond=0)

    s = slot_str.strip().lower()

    if s in ("today", "now"):
        return now.replace(second=0, microsecond=0)
    if s == "tomorrow":
        return (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)

    weekdays = {
        "monday": 0, "mon": 0,
        "tuesday": 1, "tue": 1, "tues": 1,
        "wednesday": 2, "wed": 2,
        "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
        "friday": 4, "fri": 4,
        "saturday": 5, "sat": 5,
        "sunday": 6, "sun": 6,
    }
    for wname, wday in weekdays.items():
        if s == wname:
            days_ahead = (wday - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            target_date = (now + timedelta(days=days_ahead)).date()
            return datetime(target_date.year, target_date.month, target_date.day, 10, 0, 0)

    clean = re.sub(r"[zZ]$", "", slot_str.strip())
    clean = re.sub(r"([+-]\d{2}:?\d{2})$", "", clean).strip()
    if " " in clean and "T" not in clean:
        clean = clean.replace(" ", "T")

    # Time-only e.g. "11:00", "17:30"
    time_match = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$", clean)
    if time_match:
        h = int(time_match.group(1))
        m = int(time_match.group(2))
        return datetime(now.year, now.month, now.day, h, m, 0)

    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y",
    ):
        try:
            return datetime.strptime(clean[:len(datetime.now().strftime(fmt))], fmt)
        except Exception:
            pass

    try:
        dt = datetime.fromisoformat(clean)
        return dt.replace(tzinfo=None)
    except Exception:
        pass

    return None


async def _get_open_slots(db, stylist: Stylist, date_obj) -> list[str]:
    """Return all available 30-minute slot strings (e.g. ['10:00 AM', '10:30 AM']) for a stylist on a date."""
    start_dt = datetime.strptime(stylist.start_time, "%H:%M")
    end_dt = datetime.strptime(stylist.end_time, "%H:%M")

    start_day = datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0)
    end_day = datetime(date_obj.year, date_obj.month, date_obj.day, 23, 59, 59)
    apt_res = await db.execute(
        select(Appointment).filter(
            Appointment.stylist == stylist.name,
            Appointment.slot_time >= start_day,
            Appointment.slot_time <= end_day,
            Appointment.status != "Cancelled",
        )
    )
    booked_times = {a.slot_time.time() for a in apt_res.scalars().all()}

    open_slots = []
    curr = start_dt
    while curr < end_dt:
        if curr.time() not in booked_times:
            open_slots.append(curr.strftime("%I:%M %p"))
        curr += timedelta(minutes=30)
    return open_slots


async def get_stylist_from_db(stylist_name: str = ""):
    async with AsyncSessionLocal() as db:
        try:
            clean = (stylist_name or "").strip()
            if not clean or clean.lower() in ("all", "any", "stylists", "staff", "who", "anyone", "everyone"):
                result = await db.execute(select(Stylist))
                stylists = result.scalars().all()
                if not stylists:
                    return "Our stylists are Anita Rao, Rahul Shetty, and Kavya Nair."
                lines = [
                    f"{s.name} ({s.specialties}, {s.working_days}, {s.start_time} to {s.end_time})"
                    for s in stylists
                ]
                return "We have 3 stylists at Sunrise Salon: " + "; ".join(lines)

            stmt = select(Stylist).filter(
                or_(
                    Stylist.name.ilike(f"%{clean}%"),
                    Stylist.specialties.ilike(f"%{clean}%"),
                )
            )
            result = await db.execute(stmt)
            stylists = result.scalars().all()

            if not stylists:
                return (
                    f"I couldn't find a stylist matching '{clean}'. "
                    "Our stylists are Anita Rao (haircuts & styling), "
                    "Rahul Shetty (hair colour & spa), and Kavya Nair (facials & clean-ups)."
                )

            results = []
            for s in stylists:
                results.append(
                    f"{s.name} specializes in {s.specialties}. "
                    f"Working days: {s.working_days}, Hours: {s.start_time} to {s.end_time}."
                )
            return " ".join(results)
        except Exception as e:
            print(f"Error in get_stylist_from_db: {e}")
            return "Our stylists are Anita Rao, Rahul Shetty, and Kavya Nair."


async def get_faq_from_db(topic: str = ""):
    async with AsyncSessionLocal() as db:
        try:
            clean = (topic or "").strip().lower()
            all_result = await db.execute(select(FAQ))
            all_faqs = all_result.scalars().all()

            if not clean or clean in ("all", "faq", "faqs", "help", "information", "general"):
                return " ".join([f.content for f in all_faqs])

            if any(k in clean for k in ("cancel", "reschedul", "late", "polic", "rule", "sunday", "discount")):
                category_key = "Policies"
            elif any(k in clean for k in ("park", "walk", "locat", "address", "where")):
                category_key = "Walk-ins & Parking"
            elif any(k in clean for k in ("pay", "upi", "card", "cash", "money", "cost", "price", "method")):
                category_key = "Payment"
            else:
                category_key = clean

            stmt = select(FAQ).filter(
                or_(
                    FAQ.category.ilike(f"%{category_key}%"),
                    FAQ.content.ilike(f"%{clean}%"),
                )
            )
            result = await db.execute(stmt)
            matched = result.scalars().all()

            if matched:
                return " ".join([f.content for f in matched])

            return (
                "Sunrise Salon is located at 12 Lake Road, Indiranagar, Bengaluru. "
                "We accept cash, UPI, and cards. Walk-ins are welcome though bookings are served first. "
                "Free cancellation up to 2 hours before your appointment. Closed on Sundays."
            )
        except Exception as e:
            print(f"Error in get_faq_from_db: {e}")
            return (
                "Sunrise Salon is located at 12 Lake Road, Indiranagar, Bengaluru. "
                "We accept cash, UPI, and cards. Free cancellation up to 2 hours before."
            )


async def get_service_from_db(service_name: str = ""):
    async with AsyncSessionLocal() as db:
        try:
            clean = (service_name or "").strip()
            if not clean or clean.lower() in ("all", "services", "menu", "list", "options", "anything", "what do you have", "what services"):
                result = await db.execute(select(Service))
                services = result.scalars().all()
                lines = [f"{s.service_name} ({s.price}, with {s.stylist_name})" for s in services]
                return "Sunrise Salon offers: " + ", ".join(lines) + "."

            stmt = select(Service).filter(
                or_(
                    Service.service_name.ilike(f"%{clean}%"),
                    Service.stylist_name.ilike(f"%{clean}%"),
                )
            )
            result = await db.execute(stmt)
            services = result.scalars().all()

            if not services:
                all_res = await db.execute(select(Service))
                avail = ", ".join([s.service_name for s in all_res.scalars().all()])
                return (
                    f"Sorry, we don't offer '{service_name}' at Sunrise Salon. "
                    f"Our available services are: {avail}."
                )

            lines = [f"{s.service_name} with {s.stylist_name} costs {s.price}" for s in services]
            return ". ".join(lines) + "."
        except Exception as e:
            print(f"Error in get_service_from_db: {e}")
            return "Sunrise Salon offers haircuts, blow dry, hair colour, hair spa, facials, and clean-ups."


async def check_availability_db(stylist_name: str = "any", slot_time: str = ""):
    async with AsyncSessionLocal() as db:
        try:
            dt = _parse_datetime(slot_time)
            if not dt:
                dt = datetime.now(_IST).replace(tzinfo=None)

            # Check if requested date is Sunday
            if dt.weekday() == 6:
                next_mon = dt + timedelta(days=1)
                return (
                    f"Sunrise Salon is closed on Sundays ({dt.strftime('%d %B %Y')}). "
                    f"Our working days are Monday through Saturday. "
                    f"Would you like to check availability for Monday, {next_mon.strftime('%d %B %Y')}?"
                )

            day_name = dt.strftime("%a")
            clean_stylist = (stylist_name or "").strip()
            is_any_stylist = not clean_stylist or clean_stylist.lower() in ("any", "all", "anyone", "someone", "either")

            stylists_res = await db.execute(select(Stylist))
            all_stylists = stylists_res.scalars().all()

            working_stylists = [
                s for s in all_stylists
                if day_name in [d.strip() for d in s.working_days.split(",")]
            ]

            if not working_stylists:
                return f"No stylists work on {dt.strftime('%A')}s. Sunrise Salon is open Monday to Saturday."

            # Determine whether caller provided a specific time or just a date
            raw_s = (slot_time or "").strip().lower()
            has_specific_time = ("t" in raw_s or ":" in raw_s or any(k in raw_s for k in ("am", "pm", "morning", "evening", "afternoon")))

            # Checking ALL stylists
            if is_any_stylist:
                if has_specific_time:
                    slot_t = dt.time()
                    available_stylists = []
                    for s in working_stylists:
                        st = datetime.strptime(s.start_time, "%H:%M").time()
                        et = datetime.strptime(s.end_time, "%H:%M").time()
                        if st <= slot_t < et:
                            apt_res = await db.execute(
                                select(Appointment).filter(
                                    Appointment.stylist == s.name,
                                    Appointment.slot_time == dt,
                                    Appointment.status != "Cancelled",
                                )
                            )
                            if not apt_res.scalars().first():
                                available_stylists.append(f"{s.name} ({s.specialties})")

                    if available_stylists:
                        return (
                            f"At {dt.strftime('%I:%M %p on %A, %d %B %Y')}, "
                            f"the following stylists are available: {', '.join(available_stylists)}."
                        )
                    else:
                        suggestions = []
                        for s in working_stylists:
                            open_slots = await _get_open_slots(db, s, dt.date())
                            if open_slots:
                                suggestions.append(f"{s.name}: {', '.join(open_slots[:3])}")
                        sug_text = f" Available alternative times on {dt.strftime('%A')}: " + "; ".join(suggestions) if suggestions else ""
                        return (
                            f"Sorry, no stylists are available at {dt.strftime('%I:%M %p on %A, %d %B %Y')}.{sug_text}"
                        )
                else:
                    day_summary = []
                    for s in working_stylists:
                        open_slots = await _get_open_slots(db, s, dt.date())
                        if open_slots:
                            day_summary.append(
                                f"{s.name} ({s.specialties}, {s.start_time}-{s.end_time}, available slots include {', '.join(open_slots[:4])})"
                            )
                        else:
                            day_summary.append(f"{s.name} ({s.specialties}, fully booked)")

                    return (
                        f"On {dt.strftime('%A, %d %B %Y')}, our available stylists are: "
                        + "; ".join(day_summary)
                        + ". What time slot would you like?"
                    )

            # Specific stylist
            stmt = select(Stylist).filter(Stylist.name.ilike(f"%{clean_stylist}%"))
            result = await db.execute(stmt)
            stylist = result.scalars().first()
            if not stylist:
                names = ", ".join([s.name for s in all_stylists])
                return f"Stylist '{stylist_name}' was not found. Our stylists are {names}."

            w_days = [d.strip() for d in stylist.working_days.split(",")]
            if day_name not in w_days:
                return (
                    f"{stylist.name} does not work on {dt.strftime('%A')}s. "
                    f"Working days for {stylist.name}: {stylist.working_days}."
                )

            if has_specific_time:
                slot_t = dt.time()
                st = datetime.strptime(stylist.start_time, "%H:%M").time()
                et = datetime.strptime(stylist.end_time, "%H:%M").time()
                if not (st <= slot_t < et):
                    return (
                        f"{stylist.name} is only available between {stylist.start_time} "
                        f"and {stylist.end_time} on {dt.strftime('%A')}s. "
                        f"The requested time {dt.strftime('%I:%M %p')} is outside working hours."
                    )

                apt_stmt = select(Appointment).filter(
                    Appointment.stylist == stylist.name,
                    Appointment.slot_time == dt,
                    Appointment.status != "Cancelled",
                )
                apt_result = await db.execute(apt_stmt)
                existing = apt_result.scalars().first()
                if existing:
                    open_slots = await _get_open_slots(db, stylist, dt.date())
                    sug = f" Available slots for {stylist.name} on {dt.strftime('%A')} are: {', '.join(open_slots[:4])}." if open_slots else ""
                    return (
                        f"The slot at {dt.strftime('%I:%M %p on %A, %d %B %Y')} with {stylist.name} is already booked.{sug}"
                    )
                else:
                    return f"The slot at {dt.strftime('%I:%M %p on %A, %d %B %Y')} with {stylist.name} is available!"
            else:
                open_slots = await _get_open_slots(db, stylist, dt.date())
                if open_slots:
                    return (
                        f"{stylist.name} is available on {dt.strftime('%A, %d %B %Y')} "
                        f"from {stylist.start_time} to {stylist.end_time}. "
                        f"Available 30-minute slots: {', '.join(open_slots)}."
                    )
                else:
                    return f"{stylist.name} has no available slots left on {dt.strftime('%A, %d %B %Y')}."

        except Exception as e:
            return f"Error checking availability: {str(e)}"


async def check_appointment_db(customer_name: str, date: str | None = None):
    """Check or lookup existing appointments for a customer."""
    async with AsyncSessionLocal() as db:
        try:
            clean_name = (customer_name or "").strip()
            if not clean_name:
                return "Please provide the customer name to look up appointments."

            stmt = select(Appointment).filter(
                Appointment.customer_name.ilike(f"%{clean_name}%"),
                Appointment.status != "Cancelled",
            ).order_by(Appointment.slot_time.asc())

            result = await db.execute(stmt)
            appointments = result.scalars().all()

            if not appointments:
                return (
                    f"I couldn't find any active appointments under the name '{clean_name}'. "
                    "Would you like to book an appointment?"
                )

            details = []
            for a in appointments:
                dt_str = a.slot_time.strftime("%A, %d %B %Y at %I:%M %p")
                details.append(
                    f"{a.service} with {a.stylist} on {dt_str} (Status: {a.status})"
                )

            return (
                f"Found {len(appointments)} appointment(s) for {clean_name}: "
                + "; ".join(details)
                + "."
            )
        except Exception as e:
            return f"Error checking appointment: {str(e)}"


async def manage_appointment_db(
    action: str,
    customer_name: str,
    service: str = "",
    stylist: str = "",
    slot_time: str = "",
):
    action_clean = (action or "").strip().lower()

    if action_clean in ("check", "lookup", "view", "status", "find", "get"):
        return await check_appointment_db(customer_name)

    async with AsyncSessionLocal() as db:
        try:
            parsed_time = _parse_datetime(slot_time)
            if not parsed_time:
                return (
                    f"Invalid date/time format '{slot_time}'. "
                    "Please provide the appointment date and time (e.g. '2026-11-24T17:00:00')."
                )

            # Prevent Sunday booking
            if parsed_time.weekday() == 6:
                next_mon = parsed_time + timedelta(days=1)
                return (
                    f"Sunrise Salon is closed on Sundays ({parsed_time.strftime('%d %B %Y')}). "
                    f"Please select a slot from Monday to Saturday (e.g. Monday, {next_mon.strftime('%d %B %Y')})."
                )

            # Prevent booking in past
            parsed_time = parsed_time.replace(tzinfo=None)
            slot_ist = parsed_time.replace(tzinfo=_IST)
            now_ist = datetime.now(_IST)

            if action_clean == "book" and slot_ist < now_ist:
                return (
                    f"Cannot book an appointment in the past. "
                    f"Current time is {now_ist.strftime('%A, %d %B %Y %I:%M %p')} IST. "
                    "Please select an upcoming slot."
                )

            # Normalize service name first
            clean_service = (service or "").strip()
            service_obj = None
            if clean_service:
                service_stmt = select(Service).filter(Service.service_name.ilike(f"%{clean_service}%"))
                service_res = await db.execute(service_stmt)
                service_obj = service_res.scalars().first()
                if service_obj:
                    service_name = service_obj.service_name
                else:
                    service_name = clean_service
            else:
                service_name = "Salon Service"

            # Normalize or deduce stylist name
            clean_stylist = (stylist or "").strip()
            if not clean_stylist or clean_stylist.lower() in ("any", "anyone", "stylist", "default", "staff", "all"):
                if service_obj:
                    clean_stylist = service_obj.stylist_name
                else:
                    if any(k in service_name.lower() for k in ("color", "colour", "spa")):
                        clean_stylist = "Rahul Shetty"
                    elif any(k in service_name.lower() for k in ("facial", "clean")):
                        clean_stylist = "Kavya Nair"
                    else:
                        clean_stylist = "Anita Rao"

            stylist_stmt = select(Stylist).filter(Stylist.name.ilike(f"%{clean_stylist}%"))
            stylist_res = await db.execute(stylist_stmt)
            stylist_obj = stylist_res.scalars().first()
            if stylist_obj:
                stylist_name = stylist_obj.name
            else:
                return f"Stylist '{stylist}' is not recognized. Our stylists are Anita Rao, Rahul Shetty, and Kavya Nair."

            clean_customer = (customer_name or "").strip()
            if not clean_customer:
                return "Customer name is required to book or cancel an appointment."

            # Validate working day
            day_name = parsed_time.strftime("%a")
            working_days = [d.strip() for d in stylist_obj.working_days.split(",")]
            if day_name not in working_days:
                return (
                    f"{stylist_name} does not work on {parsed_time.strftime('%A')}s. "
                    f"Working days for {stylist_name}: {stylist_obj.working_days}."
                )

            # Validate working hours
            slot_t = parsed_time.time()
            start_t = datetime.strptime(stylist_obj.start_time, "%H:%M").time()
            end_t = datetime.strptime(stylist_obj.end_time, "%H:%M").time()
            if not (start_t <= slot_t < end_t):
                return (
                    f"{stylist_name} is only available between "
                    f"{stylist_obj.start_time} and {stylist_obj.end_time}. "
                    f"The requested time {parsed_time.strftime('%I:%M %p')} is outside working hours."
                )

            # Align seconds/minutes to 30-min slot
            if parsed_time.second != 0 or parsed_time.microsecond != 0:
                parsed_time = parsed_time.replace(second=0, microsecond=0)
            if parsed_time.minute not in (0, 30):
                rounded_min = 30 if 15 < parsed_time.minute <= 45 else 0
                if parsed_time.minute > 45:
                    parsed_time = parsed_time.replace(minute=0, hour=(parsed_time.hour + 1) % 24)
                else:
                    parsed_time = parsed_time.replace(minute=rounded_min)

            if action_clean == "book":
                stmt = (
                    select(Appointment)
                    .filter(
                        Appointment.stylist == stylist_name,
                        Appointment.slot_time == parsed_time,
                        Appointment.status != "Cancelled",
                    )
                    .with_for_update()
                )
                result = await db.execute(stmt)
                existing = result.scalars().first()

                if existing:
                    if existing.customer_name.lower() == clean_customer.lower():
                        return (
                            f"You already have a confirmed appointment for {existing.service} "
                            f"with {stylist_name} at {parsed_time.strftime('%I:%M %p on %A, %d %B %Y')}."
                        )
                    open_slots = await _get_open_slots(db, stylist_obj, parsed_time.date())
                    sug = f" Available alternative slots for {stylist_name} on {parsed_time.strftime('%A')} are: {', '.join(open_slots[:4])}." if open_slots else ""
                    return (
                        f"Sorry, the slot at {parsed_time.strftime('%I:%M %p on %A, %d %B %Y')} "
                        f"with {stylist_name} is already booked.{sug}"
                    )

                cust_stmt = (
                    select(Appointment)
                    .filter(
                        Appointment.customer_name.ilike(clean_customer),
                        Appointment.slot_time == parsed_time,
                        Appointment.status != "Cancelled",
                    )
                )
                cust_result = await db.execute(cust_stmt)
                if cust_result.scalars().first():
                    return f"{clean_customer} already has an appointment booked at {parsed_time.strftime('%I:%M %p on %A, %d %B %Y')}."

                new_apt = Appointment(
                    customer_name=clean_customer,
                    service=service_name,
                    stylist=stylist_name,
                    slot_time=parsed_time,
                    status="Confirmed",
                )
                db.add(new_apt)

                try:
                    await db.commit()
                except IntegrityError:
                    await db.rollback()
                    return (
                        f"Sorry, the slot at {parsed_time.strftime('%I:%M %p on %A, %d %B %Y')} "
                        f"with {stylist_name} was just booked. Please choose another time."
                    )

                return (
                    f"Successfully booked {service_name} with {stylist_name} "
                    f"for {clean_customer} on {parsed_time.strftime('%A, %d %B %Y at %I:%M %p')}."
                )

            elif action_clean == "cancel":
                stmt = (
                    select(Appointment)
                    .filter(
                        Appointment.customer_name.ilike(f"%{clean_customer}%"),
                        Appointment.status != "Cancelled",
                    )
                    .with_for_update()
                )
                result = await db.execute(stmt)
                apts = result.scalars().all()

                if not apts:
                    return f"I couldn't find an active appointment for {clean_customer} to cancel."

                target_apt = None
                for a in apts:
                    if stylist_name and a.stylist.lower() == stylist_name.lower():
                        if parsed_time and a.slot_time == parsed_time:
                            target_apt = a
                            break
                        target_apt = a
                    elif parsed_time and a.slot_time == parsed_time:
                        target_apt = a
                        break

                if not target_apt:
                    target_apt = apts[0]

                target_apt.status = "Cancelled"
                await db.commit()

                return (
                    f"Your appointment for {target_apt.service} with {target_apt.stylist} on "
                    f"{target_apt.slot_time.strftime('%A, %d %B %Y at %I:%M %p')} has been cancelled."
                )

            return "Invalid action. Use 'book', 'cancel', or 'check'."

        except Exception as e:
            await db.rollback()
            return f"Operation failed: {str(e)}"









