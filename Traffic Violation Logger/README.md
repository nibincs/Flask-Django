# Smart Traffic Violation Logger

A Flask mini-project for logging and tracking traffic violations, with
auto-generated QR codes that lead to a public "check your challan" page.

## Structure

```
traffic_logger/
├── app.py                 # Flask routes / backend logic
├── models.py               # SQLAlchemy models (Officer, Violation)
├── requirements.txt
├── static/
│   └── css/style.css       # Design system (challan/ticket theme)
├── templates/               # Jinja2 frontend templates
│   ├── base.html            # Shared sidebar layout
│   ├── index.html           # Dashboard
│   ├── add_violation.html   # Add-violation form
│   ├── history.html         # Search / filter history
│   ├── challan_detail.html  # Single challan + QR code (officer view)
│   ├── status.html          # Public status page (reached via QR scan)
│   └── login.html           # Officer login
└── qr_codes/                # Generated QR code images (created at runtime)
```

## Setup

```bash
cd traffic_logger
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

python app.py
```

The first run automatically creates `violations.db` (SQLite) and a default
officer account:

- **Badge ID:** `ADMIN001`
- **Password:** `admin123`

Change this in `app.py` (or add more officers) before deploying for real.

Then open **http://127.0.0.1:5000**.

## How it works

- **Log Violation** — officer fills in vehicle number, violation type,
  location, date and fine. A unique challan number (`CH-2026-000001`, ...)
  and a QR code are generated automatically. New records start as `Unpaid`.
- **Violation History** — search by vehicle number, and filter by status,
  violation type, or date range.
- **Challan detail** — shows the ticket, its QR code, and a public link.
  Scanning the QR code (or opening the link) takes anyone — no login
  needed — to a public page showing the violation and payment status.
- **Mark Paid / Unpaid** — one click from the history table or the challan
  detail page.

## Notes for extending it

- Swap the `Mark Paid` button for a real payment gateway webhook that
  flips `status` to `Paid` automatically.
- `qr_filename` is stored per record, so QR images are only generated once,
  at creation time — regenerate them if you ever change the domain the
  app is hosted on (the QR encodes an absolute URL).
- Add more officer accounts via `flask --app app.py shell` and the
  `Officer` model, or extend `/login` with a registration form.
