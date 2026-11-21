from database import FAQ, Service, Stylist, AsyncSessionLocal, Appointment
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

async def get_stylist_from_db(stylist_name: str):
  async with AsyncSessionLocal() as db:
    try:
      stmt = select(Stylist)
      if stylist_name:
        stmt = stmt.filter(Stylist.name.ilike(f"%{stylist_name}%"))

      result = await db.execute(stmt)
      stylists = result.scalars().all()

      if not stylists:
        return "I couldn't find any information for that stylist "

      results = []
      for s in stylists:
        results.append(
            f"{s.name} specializes in {s.specialties}. Working days:"
            f" {s.working_days}, Hours: {s.start_time} to {s.end_time}"
        )
      return " ".join(results)
    except Exception as e:
      print(e)
      return "I couldn't find any information for that stylist "


async def get_faq_from_db(topic: str):
  async with AsyncSessionLocal() as db:
    try:
      stmt = select(FAQ).filter(FAQ.category.ilike(f"%{topic}%"))
      result = await db.execute(stmt)
      faq = result.scalars().first()

      if not faq:
        return "I couldn't find any information for that faq topic "
      return faq.content
    except Exception as e:
      print(e)
      return "I couldn't find any information for that faq topic "


async def get_service_from_db(service_name: str):
  async with AsyncSessionLocal() as db:
    try:
      stmt = select(Service).filter(
          Service.service_name.ilike(f"%{service_name}%")
      )
      result = await db.execute(stmt)
      service = result.scalars().first()

      if not service:
        return f"Sorry, we don't offer {service_name} at Sunrise Salon "
      return (
          f"{service.service_name} with {service.stylist_name} at Sunrise"
          f" Salon costs {service.price}"
      )
    except Exception as e:
      print(e)
      return "I couldn't find any information for that service "



async def check_availability_db(stylist_name: str, slot_time: str):
  async with AsyncSessionLocal() as db:
    try:
      # 1. Normalize stylist name
      stmt = select(Stylist).filter(Stylist.name.ilike(f"%{stylist_name.strip()}%"))
      result = await db.execute(stmt)
      stylist = result.scalars().first()
      if not stylist:
        return f"Stylist '{stylist_name}' not found. Our stylists are Anita Rao, Rahul Shetty, and Kavya Nair."

      # 2. Parse slot_time
      try:
        dt = datetime.fromisoformat(slot_time)
      except ValueError:
        try:
          dt = datetime.strptime(slot_time[:10], "%Y-%m-%d")
        except ValueError:
          return (
              f"Invalid date format '{slot_time}'. "
              "Please provide an ISO date/time like YYYY-MM-DDTHH:MM:SS."
          )

      # 3. Check working days
      day_name = dt.strftime("%a")  # Mon, Tue, Wed, Thu, Fri, Sat, Sun
      working_days = [d.strip() for d in stylist.working_days.split(",")]
      if day_name not in working_days:
        return (
            f"{stylist.name} does not work on {dt.strftime('%A')}s. "
            f"Working days: {stylist.working_days}."
        )

      # 4. If a specific time was requested
      if "T" in slot_time or len(slot_time) > 10:
        slot_t = dt.time()
        start_t = datetime.strptime(stylist.start_time, "%H:%M").time()
        end_t = datetime.strptime(stylist.end_time, "%H:%M").time()
        if not (start_t <= slot_t < end_t):
          return (
              f"{stylist.name} is only available between {stylist.start_time} "
              f"and {stylist.end_time}."
          )

        apt_stmt = select(Appointment).filter(
            Appointment.stylist == stylist.name,
            Appointment.slot_time == dt,
        )
        apt_result = await db.execute(apt_stmt)
        existing = apt_result.scalars().first()
        if existing:
          return f"The slot at {dt.strftime('%I:%M %p on %A, %d %B %Y')} with {stylist.name} is already booked."
        else:
          return f"The slot at {dt.strftime('%I:%M %p on %A, %d %B %Y')} with {stylist.name} is available!"
      else:
        # Check all booked slots for the day
        start_day = datetime(dt.year, dt.month, dt.day, 0, 0, 0)
        end_day = datetime(dt.year, dt.month, dt.day, 23, 59, 59)
        apt_stmt = select(Appointment).filter(
            Appointment.stylist == stylist.name,
            Appointment.slot_time >= start_day,
            Appointment.slot_time <= end_day,
        )
        apt_result = await db.execute(apt_stmt)
        booked = [a.slot_time.strftime("%I:%M %p") for a in apt_result.scalars().all()]
        if booked:
          return (
              f"{stylist.name} works on {dt.strftime('%A, %d %B %Y')} from "
              f"{stylist.start_time} to {stylist.end_time}. "
              f"Booked slots: {', '.join(booked)}."
          )
        else:
          return (
              f"{stylist.name} works on {dt.strftime('%A, %d %B %Y')} from "
              f"{stylist.start_time} to {stylist.end_time}. "
              "All 30-minute slots are currently available."
          )

    except Exception as e:
      return f"Error checking availability: {str(e)}"


async def manage_appointment_db(
    action: str,
    customer_name: str,
    service: str,
    stylist: str,
    slot_time: str,
):
  async with AsyncSessionLocal() as db:
    try:
      # Validate and parse the ISO 8601 datetime string from the LLM.
      try:
        parsed_time = datetime.fromisoformat(slot_time)
      except ValueError:
        return (
            f"Invalid date/time format '{slot_time}'. "
            "Please use ISO 8601 format: YYYY-MM-DDTHH:MM:SS "
            "(e.g. 2026-11-23T11:00:00)."
        )

      # Prevent booking in the past
      cmp_time = parsed_time.replace(tzinfo=None) if parsed_time.tzinfo else parsed_time
      if cmp_time < datetime.now():
        return (
            f"Cannot book an appointment in the past ({slot_time}). "
            f"Today is {datetime.now().strftime('%Y-%m-%d')}. "
            "Please select a current or upcoming slot."
        )
      parsed_time = cmp_time

      # Normalize stylist name to canonical database entry
      stylist_stmt = select(Stylist).filter(Stylist.name.ilike(f"%{stylist.strip()}%"))
      stylist_res = await db.execute(stylist_stmt)
      stylist_obj = stylist_res.scalars().first()
      if stylist_obj:
        stylist = stylist_obj.name
      else:
        return f"Stylist '{stylist}' is not recognized. Our stylists are Anita Rao, Rahul Shetty, and Kavya Nair."

      # ── Validate working day ──────────────────────────────────────
      day_name = parsed_time.strftime("%a")  # Mon, Tue, …
      working_days = [d.strip() for d in stylist_obj.working_days.split(",")]
      if day_name not in working_days:
        return (
            f"{stylist} does not work on {parsed_time.strftime('%A')}s. "
            f"Working days: {stylist_obj.working_days}."
        )

      # ── Validate working hours ────────────────────────────────────
      slot_t = parsed_time.time()
      start_t = datetime.strptime(stylist_obj.start_time, "%H:%M").time()
      end_t = datetime.strptime(stylist_obj.end_time, "%H:%M").time()
      if not (start_t <= slot_t < end_t):
        return (
            f"{stylist} is only available between "
            f"{stylist_obj.start_time} and {stylist_obj.end_time}. "
            f"The requested time {parsed_time.strftime('%I:%M %p')} is outside working hours."
        )

      # ── Validate 30-minute slot alignment ─────────────────────────
      if parsed_time.minute not in (0, 30) or parsed_time.second != 0:
        return (
            "Appointments must start on the hour or half-hour "
            "(e.g. 10:00, 10:30, 11:00). "
            f"The requested time {parsed_time.strftime('%I:%M %p')} is not a valid slot."
        )

      # Normalize service name
      service_stmt = select(Service).filter(Service.service_name.ilike(f"%{service.strip()}%"))
      service_res = await db.execute(service_stmt)
      service_obj = service_res.scalars().first()
      if service_obj:
        service = service_obj.service_name

      clean_customer = customer_name.strip()

      if action.lower() == "book":
        # 1. Row-level lock on the stylist slot to prevent double-booking
        stmt = (
            select(Appointment)
            .filter(
                Appointment.stylist == stylist,
                Appointment.slot_time == parsed_time,
            )
            .with_for_update()
        )
        result = await db.execute(stmt)
        existing = result.scalars().first()

        if existing:
          if existing.customer_name.lower() == clean_customer.lower():
            return f"You already have a confirmed appointment for {service} with {stylist} at {slot_time}."
          return f"Sorry, the slot at {slot_time} with {stylist} is already booked."

        # 2. Check if this customer already has an appointment at this exact slot
        cust_stmt = (
            select(Appointment)
            .filter(
                Appointment.customer_name.ilike(clean_customer),
                Appointment.slot_time == parsed_time,
            )
        )
        cust_result = await db.execute(cust_stmt)
        if cust_result.scalars().first():
          return f"{clean_customer} already has an appointment booked at {slot_time}."

        new_apt = Appointment(
            customer_name=clean_customer,
            service=service,
            stylist=stylist,
            slot_time=parsed_time,
            status="Confirmed",
        )
        db.add(new_apt)

        # 3. Catch the race condition: if another session committed the
        #    same (stylist, slot_time) between our SELECT and INSERT,
        #    PostgreSQL raises a UniqueViolationError.  Handle it
        #    gracefully so the user sees a friendly message instead of
        #    raw SQL.
        try:
          await db.commit()
        except IntegrityError:
          await db.rollback()
          return (
              f"Sorry, the slot at {slot_time} with {stylist} was just "
              "booked by someone else. Please choose another time."
          )

        return f"Successfully booked {service} with {stylist} for {clean_customer} at {slot_time}."

      elif action.lower() == "cancel":
        stmt = (
            select(Appointment)
            .filter(
                Appointment.customer_name.ilike(f"%{clean_customer}%"),
                Appointment.stylist == stylist,
                Appointment.slot_time == parsed_time,
            )
            .with_for_update()
        )
        result = await db.execute(stmt)
        apt = result.scalars().first()

        if not apt:
          return "I couldn't find an appointment matching those details to cancel."

        await db.delete(apt)
        await db.commit()

        return (
            f"Your appointment with {stylist} at {slot_time} has been successfully"
            " cancelled."
        )

      return "Invalid action. Use 'book' or 'cancel'."

    except Exception as e:
      await db.rollback()
      return f"Operation failed: {str(e)}"







