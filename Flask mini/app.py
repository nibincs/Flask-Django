
import os
import io
import qrcode
from datetime import datetime, date
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, send_from_directory, abort
)

from models import db, Violation, Officer

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
QR_FOLDER = os.path.join(BASE_DIR, "qr_codes")
os.makedirs(QR_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'violations.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

VIOLATION_TYPES = [
    "No Helmet", "Overspeeding", "Signal Jump", "No Seatbelt",
    "Wrong Parking", "Drunk Driving", "No Documents", "Triple Riding",
    "Using Phone While Driving", "No Number Plate",
]
def login_required(view_fn):
    @wraps(view_fn)
    def wrapped(*args, **kwargs):
        if not session.get("officer_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return view_fn(*args, **kwargs)
    return wrapped


def generate_challan_no():
    year = datetime.utcnow().year
    count = Violation.query.count() + 1
    return f"CH-{year}-{count:06d}"


def generate_qr_code(challan_no):
    """Generate a QR code pointing at the public status page and save it to disk."""
    public_url = url_for("public_status", challan_no=challan_no, _external=True)
    img = qrcode.make(public_url, box_size=8, border=2)
    filename = f"{challan_no}.png"
    img.save(os.path.join(QR_FOLDER, filename))
    return filename

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        badge_id = request.form.get("badge_id", "").strip()
        password = request.form.get("password", "")
        officer = Officer.query.filter_by(badge_id=badge_id).first()
        if officer and officer.check_password(password):
            session["officer_id"] = officer.id
            session["officer_name"] = officer.name
            flash(f"Welcome back, Officer {officer.name}.", "success")
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)
        flash("Invalid badge ID or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    total = Violation.query.count()
    unpaid = Violation.query.filter_by(status="Unpaid").count()
    paid = Violation.query.filter_by(status="Paid").count()
    total_fines = db.session.query(db.func.sum(Violation.fine_amount)).scalar() or 0
    recovered = db.session.query(db.func.sum(Violation.fine_amount)).filter(
        Violation.status == "Paid"
    ).scalar() or 0
    recent = Violation.query.order_by(Violation.created_at.desc()).limit(6).all()

    return render_template(
        "index.html",
        total=total, unpaid=unpaid, paid=paid,
        total_fines=total_fines, recovered=recovered,
        recent=recent,
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_violation():
    if request.method == "POST":
        try:
            vehicle_number = request.form["vehicle_number"].strip().upper()
            violation_type = request.form["violation_type"].strip()
            location = request.form["location"].strip()
            violation_date = datetime.strptime(request.form["violation_date"], "%Y-%m-%d").date()
            fine_amount = float(request.form["fine_amount"])
        except (KeyError, ValueError):
            flash("Please fill every field with valid values.", "danger")
            return render_template("add_violation.html", violation_types=VIOLATION_TYPES, today=date.today().isoformat())

        challan_no = generate_challan_no()

        violation = Violation(
            challan_no=challan_no,
            vehicle_number=vehicle_number,
            violation_type=violation_type,
            location=location,
            violation_date=violation_date,
            fine_amount=fine_amount,
            status="Unpaid",
            officer_id=session.get("officer_id"),
        )
        db.session.add(violation)
        db.session.commit()

        qr_filename = generate_qr_code(challan_no)
        violation.qr_filename = qr_filename
        db.session.commit()

        flash(f"Challan {challan_no} logged successfully.", "success")
        return redirect(url_for("challan_detail", challan_no=challan_no))

    return render_template("add_violation.html", violation_types=VIOLATION_TYPES, today=date.today().isoformat())


@app.route("/history")
@login_required
def history():
    query = Violation.query

    vehicle = request.args.get("vehicle", "").strip().upper()
    status = request.args.get("status", "").strip()
    v_type = request.args.get("type", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    if vehicle:
        query = query.filter(Violation.vehicle_number.contains(vehicle))
    if status in ("Paid", "Unpaid"):
        query = query.filter_by(status=status)
    if v_type:
        query = query.filter_by(violation_type=v_type)
    if date_from:
        query = query.filter(Violation.violation_date >= datetime.strptime(date_from, "%Y-%m-%d").date())
    if date_to:
        query = query.filter(Violation.violation_date <= datetime.strptime(date_to, "%Y-%m-%d").date())

    results = query.order_by(Violation.violation_date.desc()).all()

    return render_template(
        "history.html",
        results=results,
        violation_types=VIOLATION_TYPES,
        filters=request.args,
    )


@app.route("/challan/<challan_no>")
@login_required
def challan_detail(challan_no):
    violation = Violation.query.filter_by(challan_no=challan_no).first_or_404()
    return render_template("challan_detail.html", v=violation)



@app.route("/violation/<int:violation_id>/toggle-status", methods=["POST"])
@login_required
def toggle_status(violation_id):
    violation = Violation.query.get_or_404(violation_id)
    if violation.status == "Unpaid":
        violation.status = "Paid"
        violation.paid_at = datetime.utcnow()
        flash(f"Challan {violation.challan_no} marked as Paid.", "success")
    else:
        violation.status = "Unpaid"
        violation.paid_at = None
        flash(f"Challan {violation.challan_no} marked as Unpaid.", "warning")
    db.session.commit()
    return redirect(request.referrer or url_for("history"))


@app.route("/status/<challan_no>")
def public_status(challan_no):
    violation = Violation.query.filter_by(challan_no=challan_no).first_or_404()
    return render_template("status.html", v=violation)


@app.route("/qr_codes/<filename>")
def qr_code_file(filename):
    return send_from_directory(QR_FOLDER, filename)



@app.cli.command("init-db")
def init_db():
    """Usage: flask --app app.py init-db"""
    db.create_all()
    if not Officer.query.filter_by(badge_id="ADMIN001").first():
        officer = Officer(badge_id="ADMIN001", name="Duty Officer")
        officer.set_password("admin123")
        db.session.add(officer)
        db.session.commit()
        print("Created default officer -> badge_id: ADMIN001 / password: admin123")
    print("Database initialised.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not Officer.query.filter_by(badge_id="ADMIN001").first():
            officer = Officer(badge_id="ADMIN001", name="Duty Officer")
            officer.set_password("admin123")
            db.session.add(officer)
            db.session.commit()
            print("Default officer created -> badge_id: ADMIN001 / password: admin123")
    app.run(debug=True)
