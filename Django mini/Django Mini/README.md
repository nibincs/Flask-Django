# Smart Expense Tracker (Django)

A lightweight web app to log, categorize, filter, and visualize personal expenses.

## Features implemented
- **User authentication** — signup/login/logout via Django's built-in `User` model; each user only sees their own expenses.
- **Add expenses** — description, amount, date, optional notes.
- **Smart category prediction** — keyword-matching against the description (see `tracker/utils.py`), live-suggested via a small JSON endpoint as you type, editable before saving.
- **Date-wise filtering** — Today / This Week / This Month / All Time on both the dashboard and the expense list, plus category filtering on the list page.
- **Edit / delete expenses** — edit pre-fills the form; delete asks for confirmation.
- **Visualization** — Chart.js pie chart of spending by category on the dashboard, plus summary cards for total spent and transaction count.
- **Export** — download all expenses as CSV or a formatted PDF (via ReportLab).

## Tech stack
- Backend: Python 3 + Django (SQLite database)
- Frontend: HTML5, Bootstrap 5, Chart.js (via CDN)
- PDF export: ReportLab

## Setup (Windows / VS Code, Python 3.12)

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations
python manage.py makemigrations
python manage.py migrate

# 4. (Optional) create an admin account
python manage.py createsuperuser

# 5. Run the dev server
python manage.py runserver
```

Then open http://127.0.0.1:8000/ and sign up for an account.

## Project structure
```
expense_tracker/       Django project settings, root urls.py
tracker/                Main app
  models.py              Expense model
  forms.py                SignUp + Expense forms
  views.py                 Auth, CRUD, filtering, chart data, CSV/PDF export
  utils.py                  Keyword-based category prediction
  urls.py
  admin.py
templates/tracker/      All HTML templates (base, dashboard, forms, lists, auth)
static/css/style.css    Shared styling
requirements.txt
```

## Notes / possible extensions
- Category prediction currently uses a keyword dictionary (`tracker/utils.py`). It's structured so it can be swapped for an NLP/ML classifier later without touching the calling code.
- For production, remember to set `DEBUG = False`, configure `ALLOWED_HOSTS`, and move `SECRET_KEY` into an environment variable.
