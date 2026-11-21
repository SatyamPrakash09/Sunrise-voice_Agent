import os
from config import get_settings
from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint, inspect
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

settings = get_settings()
DATABASE_URL = settings.DATABASE_URL


if DATABASE_URL.startswith("postgres://"):
  DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
  DATABASE_URL = DATABASE_URL.replace(
      "postgresql://", "postgresql+asyncpg://", 1
  )

from sqlalchemy.pool import NullPool

# Create the async engine with NullPool so each job/thread opens and closes its own connection cleanly on its event loop
engine = create_async_engine(DATABASE_URL, echo=False, poolclass=NullPool)

# Create the async session maker
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


class Stylist(Base):
  __tablename__ = "stylists"
  id = Column(Integer, primary_key=True, autoincrement=True)
  name = Column(String, nullable=False)
  specialties = Column(String, nullable=False)
  working_days = Column(String, nullable=False)
  start_time = Column(String, nullable=False)
  end_time = Column(String, nullable=False)


class Service(Base):
  __tablename__ = "services"
  id = Column(Integer, primary_key=True, autoincrement=True)
  service_name = Column(String, nullable=False)
  stylist_name = Column(String, nullable=False)
  price = Column(String, nullable=False)


class FAQ(Base):
  __tablename__ = "faqs"
  id = Column(Integer, primary_key=True, autoincrement=True)
  category = Column(String, nullable=False)
  content = Column(Text, nullable=False)


class Appointment(Base):
  __tablename__ = "appointments"
  __table_args__ = (
      # Prevent double-booking: a stylist can only have one appointment per slot.
      # Using a composite constraint instead of unique=True on slot_time alone,
      # which would (incorrectly) prevent two different stylists from being
      # booked at the same wall-clock time.
      UniqueConstraint("stylist", "slot_time", name="uq_stylist_slot"),
  )
  id = Column(Integer, primary_key=True, autoincrement=True)
  customer_name = Column(String, nullable=False)
  service = Column(String, nullable=False)
  stylist = Column(String, nullable=False)
  slot_time = Column(DateTime, nullable=False)
  status = Column(String, nullable=False, default="Confirmed")



async def seed_data(db_session: AsyncSession):
  from sqlalchemy import select

  # Check if stylists already exist
  result = await db_session.execute(select(Stylist))
  if result.scalars().first():
    return  "Already Done"

  # Seed Stylists
  stylists = [
      Stylist(
          name="Anita Rao",
          specialties="Haircuts and styling",
          working_days="Mon,Tue,Wed,Thu,Fri,Sat",
          start_time="10:00",
          end_time="14:00",
      ),
      Stylist(
          name="Rahul Shetty",
          specialties="Hair colour and hair spa",
          working_days="Tue,Thu,Sat",
          start_time="16:00",
          end_time="20:00",
      ),
      Stylist(
          name="Kavya Nair",
          specialties="Facials and clean-ups",
          working_days="Mon,Wed,Fri",
          start_time="09:00",
          end_time="13:00",
      ),
  ]

  # Seed Services
  services = [
      Service(
          service_name="Haircut (women)",
          stylist_name="Anita Rao",
          price="Rs 600",
      ),
      Service(
          service_name="Haircut (men)",
          stylist_name="Anita Rao",
          price="Rs 400",
      ),
      Service(
          service_name="Blow dry and styling",
          stylist_name="Anita Rao",
          price="Rs 500",
      ),
      Service(
          service_name="Hair colour",
          stylist_name="Rahul Shetty",
          price="From Rs 2,500, depends on hair length",
      ),
      Service(
          service_name="Hair spa",
          stylist_name="Rahul Shetty",
          price="Rs 1,200",
      ),
      Service(
          service_name="Facial",
          stylist_name="Kavya Nair",
          price="Rs 1,500",
      ),
      Service(
          service_name="Clean-up",
          stylist_name="Kavya Nair",
          price="Rs 800",
      ),
  ]

  # Seed FAQs
  faqs = [
      FAQ(
          category="Payment",
          content=(
              "Payment methods accepted: cash, UPI and cards. No membership"
              " or package info on file."
          ),
      ),
      FAQ(
          category="Walk-ins & Parking",
          content=(
              "Walk-ins are welcome, but customers with a booking are served"
              " first. Street parking only. Location: 12 Lake Road, Indiranagar,"
              " Bengaluru."
          ),
      ),
      FAQ(
          category="Policies",
          content=(
              "Free cancellation up to 2 hours before. If more than 15 minutes"
              " late, the booking may be moved to the next free slot. No"
              " discounts right now. No membership or package info. Free"
              " cancellation up to 2 hours before. 30 minute slots, one slot"
              " per booking. Closed Sundays. Timezone Asia/Kolkata (IST)."
          ),
      ),
  ]

  db_session.add_all(stylists + services + faqs)
  await db_session.commit()


_db_initialized = False


async def init_db():
  global _db_initialized
  if _db_initialized:
    return

  # Create tables asynchronously
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

  # Seed data asynchronously
  async with AsyncSessionLocal() as session:
    try:
      await seed_data(session)
    except Exception as e:
      await session.rollback()
      print(f"Error seeding database: {e}")

  _db_initialized = True