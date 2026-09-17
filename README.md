# 📱 Cookdin WhatsApp Automation POC

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.103+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Status](https://img.shields.io/badge/Status-R&D_POC-green.svg)]()

> A fully automated Proof of Concept for the **Cookdin AI-Ready WhatsApp Automation & Notification System**. 

## 📋 Executive Summary

Application events (such as booking, payment, cancellation, and completion) currently require manual or separate customer communication. This R&D project demonstrates an **end-to-end automated architecture** to trigger WhatsApp messages automatically when backend events occur.

> **⚠️ POC Limitation:** Access to the Cookdin production/staging backend and real application event system was not available during development. Therefore, application events are simulated locally. The API contract is designed so that it can later be connected to the actual Cookdin backend.

To avoid Meta's sandbox limitations during development, this POC includes a fully-functional **Mock/Simulator Provider**. We utilize **FastAPI Background Tasks** to automatically simulate the lifecycle of Meta's webhooks, allowing stakeholders to watch the entire data pipeline run automatically without manual intervention.

---

## 🏗️ System Architecture

```text
[ Simulated Cookdin Event ]
            │
            ▼
[ POST /api/v1/notify ]
            │
            ▼
[ Validate Event Payload ]
            │
            ▼
[ Check Customer + Opt-in ] ──(NO)──► [ Skip & Log ]
            │ (YES)
            ▼
[ Select WhatsApp Template ]
            │
            ▼
[ Notification Engine ]
            │
            ▼
[ WhatsApp Provider Interface ]
       ↙          ↘
  [ Mock ]     [ Meta ]
       │          │
       ▼          ▼
   [ Message Sent ]
            │
            ▼
   [ Database Log ]
            │
            ▼
 [ Automated Webhooks ] 
(DELIVERED / READ / FAILED)
            │
            ▼
 [ Auto-Retry if Failed ]
```

---

## 🛠️ Tech Stack

- **Backend Framework:** FastAPI (Python)
- **Background Processing:** FastAPI BackgroundTasks (Simulating Celery/Cron)
- **Database:** SQLite with SQLAlchemy ORM
- **Data Validation:** Pydantic
- **Frontend Dashboard:** HTML5, Vanilla JS, Tailwind CSS
- **External Integration:** Meta WhatsApp Cloud API

---

## 🚀 Key Integrations & Event Flow

### 1. Supported Event Types
The system strictly validates the following application boundaries:
- `REGISTRATION`
- `BOOKING_CREATED`
- `BOOKING_CONFIRMED`
- `PAYMENT_SUCCESS`
- `PAYMENT_FAILED`
- `BOOKING_REMINDER`
- `BOOKING_CANCELLED`
- `REFUND_PROCESSED`
- `BOOKING_COMPLETED`

### 2. Template Mapping
The Notification Engine maps abstract events to approved WhatsApp templates (e.g., `booking_created` → `cookdin_booking_created`).

### 3. Automated Webhook Lifecycle
The Mock Provider uses background tasks to hit the `POST /webhook/whatsapp` endpoint automatically, simulating the real-time delivery receipt lifecycle:
- **Success Flow:** `SENT` → `DELIVERED` → `READ`
- **Error Flow:** `SENT` → `FAILED`

### 4. Automated Retry Engine
If a webhook returns a `FAILED` status, the background engine catches it and automatically schedules a retry event without human intervention.

---

## 🗄️ Database Design

The local POC uses SQLite, but the schema is designed for eventual migration to PostgreSQL.

- **`customers`** *(Theoretical)*: Tracks `customer_id`, `phone`, and `whatsapp_opt_in`.
- **`bookings`** *(Theoretical)*: Core business logic.
- **`notification_logs`** *(Implemented)*: 
  - `id` (PK)
  - `event_type`
  - `customer_phone`
  - `status` (pending, sent, delivered, read, failed)
  - `message_id` (Mapped to Meta Webhooks)
  - `retry_count`
  - `provider_used` (mock or meta)

---

## 🔌 API Specification

### Sample Event Request (`POST /api/v1/notify`)
```json
{
  "event_type": "BOOKING_CREATED",
  "customer_phone": "+919876543210",
  "customer_id": "C101",
  "whatsapp_opt_in": true,
  "event_data": {
    "booking_id": "CD001"
  }
}
```

### Sample Event Response
```json
{
  "status": "success",
  "message": "Dispatched to provider",
  "log_id": 1,
  "message_id": "wamid.mock_a1b2c3d4"
}
```

---

## ⚙️ Local Setup & Installation

### Prerequisites
- Python 3.9+
- Git

### 1. Clone & Initialize
```bash
git clone https://github.com/Sivaranjani-Chinnadurai/Cookdin-whatsapp-poc.git
cd cookdin-whatsapp-poc
python -m venv venv
```

### 2. Activate Virtual Environment
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Server
```bash
uvicorn app.main:app --reload
```

> **Troubleshooting Note:** If you encounter a `500 Internal Server Error` during development or after pulling new code, it is likely due to an SQLite schema mismatch. Simply delete the `whatsapp_poc.db` file and restart the server to generate a fresh database.

---

## ⚖️ POC vs. Production Implementation

| Feature | POC State | Production Target |
|---------|-----------|-------------------|
| **Database** | SQLite | PostgreSQL |
| **Provider** | Mock Simulator (with BackgroundTasks) | Real Meta WhatsApp Provider |
| **Events** | Simulated via UI Dashboard | Triggered by existing Cookdin backend |
| **Webhooks** | Automated via Background Simulation | Automated via Meta Graph API |
| **Retries** | Automated via BackgroundTasks | Automated via Celery / Redis |