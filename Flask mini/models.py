

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Officer(db.Model):
    """Admin/officer account able to log and update violations."""
    __tablename__ = "officers"

    id = db.Column(db.Integer, primary_key=True)
    badge_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)


class Violation(db.Model):
    __tablename__ = "violations"

    id = db.Column(db.Integer, primary_key=True)
    challan_no = db.Column(db.String(20), unique=True, nullable=False)  # e.g. CH-2026-000123
    vehicle_number = db.Column(db.String(20), nullable=False, index=True)
    violation_type = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    violation_date = db.Column(db.Date, nullable=False)
    fine_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(10), nullable=False, default="Unpaid")  # Unpaid / Paid
    officer_id = db.Column(db.Integer, db.ForeignKey("officers.id"), nullable=True)
    qr_filename = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)

    officer = db.relationship("Officer", backref="violations")

    def to_dict(self):
        return {
            "id": self.id,
            "challan_no": self.challan_no,
            "vehicle_number": self.vehicle_number,
            "violation_type": self.violation_type,
            "location": self.location,
            "violation_date": self.violation_date.strftime("%d %b %Y"),
            "fine_amount": self.fine_amount,
            "status": self.status,
        }
