from .. import db

class Business(db.Model):
    __tablename__ = "businesses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    instagram = db.Column(db.String(120), nullable=True)
    min_notice_hours = db.Column(db.Integer, nullable=False, default=2)
    max_days_ahead = db.Column(db.Integer, nullable=False, default=60)
    slot_interval = db.Column(db.Integer, nullable=False, default=30)

    users = db.relationship("User", back_populates="business", cascade="all, delete-orphan")
    professionals = db.relationship("Professional", back_populates="business", cascade="all, delete-orphan")
    services = db.relationship("Service", back_populates="business", cascade="all, delete-orphan")
    appointments = db.relationship("Appointment", back_populates="business", cascade="all, delete-orphan")
    holidays = db.relationship("Holiday", back_populates="business", cascade="all, delete-orphan")
