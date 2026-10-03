# Cloud Kitchen Management System API

A robust backend REST API built with **Django** and **Django REST Framework (DRF)** designed to manage cloud kitchen operations, including menu management, order workflows, payment processing, invoice generation, and delivery tracking.

---

## 🚀 Key Features

- **User Authentication:** Token & Session-based authentication securing protected endpoints.
- **Menu Management:** Categories and Food Items API endpoints.
- **Order & Cart Workflow:** Full order lifecycle tracking via `/api/kitchen-orders/`.
- **Payment Processing:** Integrated endpoint handling transactions and statuses.
- **Invoicing:** Automatic invoice generation with downloadable PDF support.
- **Delivery Tracking:** Logistics management for active orders.
- **Django Administration:** Built-in dashboard for menu and user management.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.x, Django 6.1
- **API Framework:** Django REST Framework (DRF)
- **Database:** SQLite (Development)
- **Version Control:** Git & GitHub

---

## 📂 Primary API Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/admin/` | `GET/POST` | Django Administration Panel |
| `/api/menus/` | `GET` | List all available menu items |
| `/api/kitchen-orders/` | `GET/POST` | Order placement and tracking |
| `/api/payments/list/` | `GET` | View payment transaction history |
| `/api/invoices/` | `GET` | Access generated order invoices |

---

## ⚙️ Local Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/murugagowsi/cloud_kitchen_project.git](https://github.com/murugagowsi/cloud_kitchen_project.git)
   cd cloud_kitchen_project