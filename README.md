Cloud Kitchen API
A Django REST Framework backend for a cloud kitchen: menus, kitchen orders, order status tracking, payments and invoices (with PDF download).
Tech Stack
Python 3, Django 6.1
Django REST Framework
django-filter, django-cors-headers, SimpleJWT
ReportLab (invoice PDFs)
Setup
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations
python manage.py migrate

# 4. Create an admin user
python manage.py createsuperuser

# 5. Run the server
python manage.py runserver
The API runs at http://127.0.0.1:8000/.
Authentication
All protected endpoints use Basic Auth (username and password).
Requests without credentials return 403 Forbidden.
Delete and admin-only actions require an admin user.
Endpoints
Menus
Method
URL
Description
GET
/api/menus/
List menu items
POST
/api/menus/
Create a menu item
GET
/api/menus/<id>/
Get one menu item
PUT / PATCH
/api/menus/<id>/
Update a menu item
DELETE
/api/menus/<id>/
Delete a menu item
Kitchen Orders and Users
Method
URL
Description
GET
/api/kitchen-orders/
List kitchen orders
GET
/api/users/
List users (admin only)
Orders
Method
URL
Description
GET
/api/orders/<id>/timeline/
Order status timeline
GET
/api/orders/pending/
Pending orders
GET
/api/orders/in_progress/
In-progress orders
GET
/api/orders/statistics/
Order counts by status
Payments
Method
URL
Description
POST
/api/payments/
Create a payment
GET
/api/payments/list/
List all payments
Invoices
Method
URL
Description
GET
/api/invoices/
List invoices
POST
/api/invoices/
Create an invoice from an order
GET
/api/invoices/<uuid>/
Invoice detail
PATCH
/api/invoices/<uuid>/
Update an invoice
DELETE
/api/invoices/<uuid>/
Delete an invoice
POST
/api/invoices/<uuid>/mark-paid/
Record a payment
POST
/api/invoices/<uuid>/cancel/
Cancel an invoice
GET
/api/invoices/stats/
Revenue and status statistics
GET
/api/invoices/<uuid>/download/
Download the invoice as PDF
Note: URLs must end with a trailing slash /, and invoice URLs use the invoice id (UUID), not the invoice number.
Testing
All endpoints were tested manually in Postman:
Without login: protected endpoints return 403
With Basic Auth: list/detail return 200, create returns 201, delete returns 204
Deleted items return 404
Invoice stats exclude cancelled and refunded invoices from revenue and pending totals
Author
Gowsika