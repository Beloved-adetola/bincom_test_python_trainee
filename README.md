# Bincom Test (Django + MySQL)

Implements:
- Q1: Polling unit results (Delta only)
- Q2: LGA summed totals computed from PU results (announced LGA results shown only for comparison)
- Q3: Add new polling unit + store results for all parties

## Setup
1) Create venv and install:
   pip install -r requirements.txt

2) Create MySQL DB `bincom_test` and import `bincom_test.sql`.
   On Windows, phpMyAdmin Import is easiest (XAMPP).

3) Edit DB creds in `bincom_project/bincom/settings.py`.

## Run
cd bincom_project
python manage.py runserver
Open http://127.0.0.1:8000/
