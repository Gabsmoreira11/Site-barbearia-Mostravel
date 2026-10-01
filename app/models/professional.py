from .. import db
class Professional(db.Model):
    __tablename__="professionals"
    id=db.Column(db.Integer,primary_key=True)
    business_id=db.Column(db.Integer,db.ForeignKey("businesses.id"),nullable=False)
    name=db.Column(db.String(120),nullable=False)
    email=db.Column(db.String(160),nullable=True)
    phone=db.Column(db.String(30),nullable=True)
    active=db.Column(db.Boolean,default=True,nullable=False)
    business=db.relationship("Business",back_populates="professionals")
    user=db.relationship("User",back_populates="professional",foreign_keys="User.professional_id",uselist=False)
    schedules=db.relationship("Schedule",back_populates="professional",cascade="all, delete-orphan")
    appointments=db.relationship("Appointment",back_populates="professional",cascade="all, delete-orphan")
    exceptions=db.relationship("AvailabilityException",back_populates="professional",cascade="all, delete-orphan")
