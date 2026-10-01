from .. import db

class AvailabilityException(db.Model):
    __tablename__ = "availability_exceptions"
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    kind = db.Column(db.String(30), nullable=False, default="day_off")  # day_off | blocked_time | special_hours
    start_time = db.Column(db.String(5), nullable=True)
    end_time = db.Column(db.String(5), nullable=True)
    reason = db.Column(db.String(120), nullable=True)
    professional = db.relationship("Professional", back_populates="exceptions")
