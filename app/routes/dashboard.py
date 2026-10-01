from datetime import date, timedelta
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from ..models import Appointment

dashboard_bp=Blueprint("dashboard",__name__,url_prefix="/dashboard")
@dashboard_bp.get("/")
@login_required
def index():
    if not (current_user.is_admin or current_user.is_professional): return redirect(url_for("customer.dashboard"))
    q=Appointment.query.filter_by(business_id=current_user.business_id,date=date.today())
    if current_user.is_professional: q=q.filter_by(professional_id=current_user.professional_id)
    today=q.order_by(Appointment.start_time).all()
    q2=Appointment.query.filter_by(business_id=current_user.business_id,status="pending")
    if current_user.is_professional: q2=q2.filter_by(professional_id=current_user.professional_id)
    pending=q2.count()
    q3=Appointment.query.filter(Appointment.business_id==current_user.business_id,Appointment.date>=date.today(),Appointment.date<=date.today()+timedelta(days=7),Appointment.status.in_(["pending","confirmed"]))
    if current_user.is_professional: q3=q3.filter_by(professional_id=current_user.professional_id)
    week=q3.count()
    return render_template("dashboard/index.html",appointments=today,pending=pending,week=week,today=date.today())
