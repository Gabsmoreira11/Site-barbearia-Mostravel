from flask_login import UserMixin
from .. import db

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(120),nullable=False)
    email=db.Column(db.String(160),unique=True,nullable=False,index=True)
    password_hash=db.Column(db.String(255),nullable=False)
    role=db.Column(db.String(30),nullable=False,default="customer") # customer | admin | professional
    business_id=db.Column(db.Integer,db.ForeignKey("businesses.id"),nullable=False)
    phone=db.Column(db.String(30),nullable=True)
    professional_id=db.Column(db.Integer,db.ForeignKey("professionals.id"),nullable=True)
    business=db.relationship("Business",back_populates="users")
    professional=db.relationship("Professional",back_populates="user",foreign_keys=[professional_id])
    appointments=db.relationship("Appointment",back_populates="client",foreign_keys="Appointment.client_user_id")
    @property
    def is_customer(self): return self.role=="customer"
    @property
    def is_admin(self): return self.role=="admin"
    @property
    def is_professional(self): return self.role=="professional"
