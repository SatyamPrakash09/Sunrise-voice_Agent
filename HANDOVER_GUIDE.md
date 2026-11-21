# 💇 Sunrise Salon — Voice Assistant Handover Guide

> **Welcome to your new AI Voice Receptionist!**  
> This guide is specially prepared for the salon owner, managers, and front-desk team. It explains everything you need to know in plain, everyday language — no technical background required!

---

## 🌟 1. Welcome & Overview

Congratulations! Sunrise Salon now has an intelligent **AI Voice Receptionist** that answers customer calls directly from your website or phone interface.

### What it does for your salon:
- **Answers instantly:** Welcomes callers warmly and professionally in natural Indian English.
- **Checks availability in real time:** Knows exactly which stylist is working, what time they are free, and who is already booked.
- **Takes appointments:** Collects the customer's full name, desired service, preferred stylist, and time slot.
- **Prevents double bookings:** Ensures no two clients are ever booked with the same stylist at the same time.
- **Answers customer queries:** Tells callers about service pricing, directions in Indiranagar, parking options, accepted payment modes (UPI, cards, cash), and salon policies.
- **Handles cancellations:** Allows customers to cancel or reschedule politely according to your salon rules.

---

## 📍 2. Your Salon Setup & Information

The assistant is currently pre-configured with the exact details of Sunrise Salon:

### 🏠 Location & General Hours
- **Address:** 12 Lake Road, Indiranagar, Bengaluru
- **Working Days:** Monday to Saturday (Closed on Sundays)
- **General Salon Hours:** 9:00 AM – 8:00 PM IST
- **Appointment Slot Length:** 30 minutes per appointment

---

### ✂️ Your Stylists & Their Working Hours

| Stylist | Specialties | Working Days | Working Hours |
|---|---|---|---|
| **Anita Rao** | Haircuts & styling | Monday to Saturday | 10:00 AM – 2:00 PM |
| **Rahul Shetty** | Hair colour & Hair spa | Tuesday, Thursday, Saturday | 4:00 PM – 8:00 PM |
| **Kavya Nair** | Facials & Clean-ups | Monday, Wednesday, Friday | 9:00 AM – 1:00 PM |

*Note: The assistant will never let a client book Anita outside 10 AM – 2 PM, or book Rahul on a Wednesday, ensuring your team's schedules are strictly respected.*

---

### 🏷️ Services & Price List

| Service | Stylist Assigned | Price |
|---|---|---|
| **Women's Haircut** | Anita Rao | Rs 600 |
| **Men's Haircut** | Anita Rao | Rs 400 |
| **Blow dry & Styling** | Anita Rao | Rs 500 |
| **Hair Colour** | Rahul Shetty | From Rs 2,500 *(depends on length)* |
| **Hair Spa** | Rahul Shetty | Rs 1,200 |
| **Facial** | Kavya Nair | Rs 1,500 |
| **Clean-up** | Kavya Nair | Rs 800 |

---

### 📜 Salon Policies Explained to Callers
- **Payment Modes:** Cash, UPI (Google Pay, PhonePe, Paytm), and debit/credit cards.
- **Parking:** Street parking only on Lake Road.
- **Walk-ins:** Walk-in clients are always welcome, but clients with confirmed appointments are given priority.
- **Cancellations:** Free cancellation up to 2 hours before the scheduled slot.
- **Late Arrivals:** If a customer is more than 15 minutes late, their appointment may be moved to the next available opening so subsequent appointments aren't delayed.

---

## ⏳ 3. Important Note: "Wake-up Time" on Free Plan

The voice assistant server is currently hosted on **Render's Free Tier**.

### What you need to know:
1. **Sleep Mode:** When nobody has visited the website or made a call for 15 minutes, Render puts the server to "sleep" to save computing resources.
2. **First Call Delay:** When a customer clicks **"Start Call"** after the server has been asleep, it takes about **50 to 90 seconds** for the server to wake up and connect.
3. **Smooth Once Awake:** Once awake, the assistant responds instantly with zero delay for all subsequent calls.

### Tip for Salon Staff:
- If you or your team want to test the assistant before business hours, simply click **"Start Call"** once in the morning to wake it up!
- If you notice heavy customer call volume in the future, the server can easily be upgraded to Render's starter plan ($7/month) which stays awake 24/7 with zero waiting time.

---

## 🗣️ 4. How the Customer Call Works

Here is a typical flow when a customer uses the voice assistant:

```
Customer clicks "Start Call"
        │
        ▼
Assistant greets:
"Hello! Welcome to Sunrise Salon. How can I help you with your appointment today?"
        │
        ▼
Customer: "I want a haircut with Anita this Friday at 11 AM."
        │
        ▼
Assistant checks database:
• Confirms Friday is a working day for Anita
• Confirms 11:00 AM is between 10:00 AM and 2:00 PM
• Confirms nobody else has booked Anita at 11:00 AM
        │
        ▼
Assistant asks for customer name & confirms booking:
"Great! Anita is available. May I have your full name please?"
        │
        ▼
Customer: "My name is Priya Sharma."
        │
        ▼
Assistant: "Thank you Priya! Your haircut appointment with Anita Rao is confirmed for Friday at 11:00 AM."
```

---

## 📋 5. Day-to-Day Staff Checklist

1. **Viewing Appointments:**
   - Appointments booked by the AI are saved with the customer's full name, service, stylist, and date/time.
   - Front desk staff can check the database or request your developer to connect a simple daily Google Sheet or WhatsApp notification if desired.
2. **Walk-ins vs AI Bookings:**
   - If a walk-in walks into the salon, staff can check the schedule to ensure the stylist is not reserved for an AI booking in that half-hour slot.
3. **If a Customer Reschedules by Phone:**
   - The assistant allows callers to cancel by saying: *"I want to cancel my appointment with Anita on Friday at 11 AM."*

---

## 🛠️ 6. How to Make Updates in the Future

Whenever you have changes in your salon:

| If you want to... | What to do |
|---|---|
| **Change prices** (e.g. increase haircut to Rs 700) | Ask your developer or update the `services` table in the database. |
| **Change stylist hours or days** | Update the `stylists` table with new times or days. |
| **Add a new stylist** | Add a new row with the stylist's name, specialties, and hours. |
| **Add a new service** | Add the service name, price, and responsible stylist. |
| **Update policies or location** | Update the `faqs` table with the new text. |

*All updates take effect immediately without needing to reprogram the AI.*

---

## 📞 7. Quick Help & FAQ for Salon Staff

**Q: What happens if a customer speaks with a strong accent?**  
A: The assistant uses Deepgram Nova-3 speech recognition, specifically tuned for Indian English accents and terms like "Rs 600", "UPI", "clean-up", and local names like "Anita Rao" and "Rahul Shetty".

**Q: Can a customer book for a past date or Sunday?**  
A: No. The assistant checks the real-time calendar and clock (IST). It strictly refuses past dates, past times of the day, and Sundays.

**Q: Can two customers book the same slot?**  
A: No. The system has built-in automatic locks that prevent double bookings. If two people try to book the same stylist at the same time, the second person will be politely asked to choose another time.

---

*Thank you for choosing AI technology to elevate your salon's customer experience!*
