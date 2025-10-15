# FreeJun Assignment

A simple REST API built using **Django REST Framework** for managing workspace room bookings, cancellations, and availability.

This project is part of the **FreJun Backend Developer Challenge**.

---

## Features

- Book a room for a specific time slot (**9 AM – 6 PM**)
- Cancel existing bookings
- View all current bookings
- Check room availability
- Handles private rooms, conference rooms, and shared desks

---

## Tech Stack

- **Backend:** Django, Django REST Framework
- **Database:** SQLite (for local dev)
- **Container:** Docker, Docker Compose

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com//freejun-assignment.git
cd freejun-assignment

2. Create and Activate Virtual Environment
python -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate

3. Install Dependencies
pip install -r requirements.txt

4. Run Migrations
python manage.py migrate

5. Run Server
python manage.py runserver

```
Server will be available at 👉 http://127.0.0.1:8000/

---
## Docker Setup (Optional)
```bash
To run using Docker:

docker-compose up --build
```
---
## API Endpoints

| Method | Endpoint | Description |
|---------|-----------|-------------|
| **POST** | `/api/v1/bookings/` | Book a room |
| **POST** | `/api/v1/cancel/<booking_id>/` | Cancel a booking |
| **GET** | `/api/v1/bookings/` | View all bookings |
| **GET** | `/api/v1/rooms/available/` | Check available rooms |

---
## Notes

Shared desks allow up to 4 users per slot.

Conference rooms require a team of 3 or more.

Children under 10 count in headcount but not seat count.

Once a booking is canceled, the slot becomes available again.
---
Gandharv Kumar Singh
Software Developer
(Assignment for FreJun Backend Challenge)
