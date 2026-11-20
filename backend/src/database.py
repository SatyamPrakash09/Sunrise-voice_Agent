import os
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import get_settings
settings = get_settings()

DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
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
  id = Column(Integer, primary_key=True, autoincrement=True)
  customer_name = Column(String, nullable=False)
  service = Column(String, nullable=False)
  stylist = Column(String, nullable=False)
  slot_time = Column(DateTime, nullable=False, unique=True)  # Prevents double booking


def seed_data(db_session):
  if db_session.query(Stylist).count() > 0:
    return  # Already seeded

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
              " discounts right now."
              "No membership or package info"
              "Free cancellation up to 2 hours before."
              "30 minute slots, one slot per booking. Closed Sundays. Timezone Asia/Kolkata (IST)."
          ),
      ),
  ]

  db_session.add_all(stylists + services + faqs)
  db_session.commit()


from sqlalchemy import inspect

def init_db():
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    print("Tables created:", inspector.get_table_names())

    session = SessionLocal()
    try:
        seed_data(session)
    finally:
        session.close()

