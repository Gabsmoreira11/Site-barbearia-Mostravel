from .. import db
from datetime import datetime

class Appointment(db.Model):
    __tablename__ = "appointments"
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    client_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    client_name = db.Column(db.String(120), nullable=False)
    client_phone = db.Column(db.String(30), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pending")
    source = db.Column(db.String(30), nullable=False, default="site")  # site | whatsapp | manual
    is_encaixe = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    business = db.relationship("Business", back_populates="appointments")
    professional = db.relationship("Professional", back_populates="appointments")
    service = db.relationship("Service", back_populates="appointments")
    client = db.relationship("User", back_populates="appointments", foreign_keys=[client_user_id])
