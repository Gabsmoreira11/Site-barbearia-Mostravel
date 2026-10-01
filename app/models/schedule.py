from .. import db

class Schedule(db.Model):
    __tablename__ = "schedules"

    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False)
    weekday = db.Column(db.Integer, nullable=False)  # 1=segunda ... 7=domingo
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)

    professional = db.relationship("Professional", back_populates="schedules")
