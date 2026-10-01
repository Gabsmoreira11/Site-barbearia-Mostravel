from datetime import datetime, timedelta, date
from urllib.parse import quote
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .. import db
from ..models import Appointment, Professional, Service, User

appointments_bp=Blueprint("appointments",__name__,url_prefix="/dashboard/appointments")

def admin(): return current_user.is_admin or current_user.is_professional

def wa_link(phone,msg):
    number="".join(c for c in (phone or "") if c.isdigit())
    return f"https://wa.me/{number}?text={quote(msg)}" if number else "#"

@appointments_bp.get("/")
@login_required
def index():
    if not admin(): return redirect(url_for("customer.dashboard"))
    status=request.args.get("status",""); selected_date=request.args.get("date","")
    q=Appointment.query.filter_by(business_id=current_user.business_id)
    if current_user.is_professional: q=q.filter_by(professional_id=current_user.professional_id)
    if status: q=q.filter_by(status=status)
    if selected_date:
        try: q=q.filter_by(date=datetime.strptime(selected_date,"%Y-%m-%d").date())
        except ValueError: pass
    appointments=q.order_by(Appointment.date.desc(),Appointment.start_time).all()
    return render_template("dashboard/appointments.html",appointments=appointments,filter_status=status,filter_date=selected_date,wa_link=wa_link)

@appointments_bp.route("/novo",methods=["GET","POST"])
@login_required
def create():
    if not current_user.is_admin: return redirect(url_for("dashboard.index"))
    pros=Professional.query.filter_by(id=current_user.professional_id,active=True).all() if current_user.is_professional else Professional.query.filter_by(business_id=current_user.business_id,active=True).all(); services=Service.query.filter_by(business_id=current_user.business_id,active=True).all(); clients=User.query.filter_by(business_id=current_user.business_id,role="customer").order_by(User.name).all()
    if request.method=="POST":
        try:
            p=db.session.get(Professional,request.form.get("professional_id",type=int)); s=db.session.get(Service,request.form.get("service_id",type=int)); c=db.session.get(User,request.form.get("client_user_id",type=int)); d=datetime.strptime(request.form.get("date",""),"%Y-%m-%d").date(); start=datetime.strptime(request.form.get("start_time",""),"%H:%M").time()
        except (ValueError,TypeError): flash("Dados inválidos.","error"); return redirect(url_for("appointments.create"))
        if not p or not s or not c or p.business_id!=current_user.business_id or s.business_id!=current_user.business_id or c.business_id!=current_user.business_id: flash("Dados inválidos.","error"); return redirect(url_for("appointments.create"))
        end=(datetime.combine(d,start)+timedelta(minutes=s.duration)).time()
        conflict=Appointment.query.filter_by(professional_id=p.id,date=d).filter(Appointment.status.in_(["pending","confirmed"])).filter(Appointment.start_time<end.strftime("%H:%M"),Appointment.end_time>start.strftime("%H:%M")).first()
        if conflict: flash("Já existe atendimento nesse horário.","error"); return redirect(url_for("appointments.create"))
        is_encaixe=request.form.get("is_encaixe")=="on"
        if not is_encaixe:
            from .customer import slots_for
            if start.strftime("%H:%M") not in slots_for(p,s,d): flash("Esse horário não está disponível pela agenda. Marque 'encaixe' se for autorizado.","error"); return redirect(url_for("appointments.create"))
        a=Appointment(business_id=current_user.business_id,professional_id=p.id,service_id=s.id,client_user_id=c.id,client_name=c.name,client_phone=c.phone or "",date=d,start_time=start.strftime("%H:%M"),end_time=end.strftime("%H:%M"),status="confirmed",source="manual",is_encaixe=is_encaixe,notes=request.form.get("notes",""))
        db.session.add(a); db.session.commit(); flash("Agendamento criado.","success"); return redirect(url_for("appointments.index"))
    return render_template("dashboard/new_appointment.html",professionals=pros,services=services,clients=clients,today=date.today())

@appointments_bp.post("/<int:appointment_id>/confirm")
@login_required
def confirm(appointment_id):
    if not admin(): return redirect(url_for("customer.dashboard"))
    a=db.session.get(Appointment,appointment_id)
    if a and a.business_id==current_user.business_id and (current_user.is_admin or a.professional_id==current_user.professional_id): a.status="confirmed"; db.session.commit(); flash("Agendamento confirmado.","success")
    return redirect(url_for("appointments.index"))

@appointments_bp.post("/<int:appointment_id>/complete")
@login_required
def complete(appointment_id):
    if not admin(): return redirect(url_for("customer.dashboard"))
    a=db.session.get(Appointment,appointment_id)
    if a and a.business_id==current_user.business_id and (current_user.is_admin or a.professional_id==current_user.professional_id): a.status="completed"; db.session.commit(); flash("Atendimento concluído.","success")
    return redirect(url_for("appointments.index"))

@appointments_bp.post("/<int:appointment_id>/cancel")
@login_required
def cancel(appointment_id):
    if not admin(): return redirect(url_for("customer.dashboard"))
    a=db.session.get(Appointment,appointment_id)
    if a and a.business_id==current_user.business_id and (current_user.is_admin or a.professional_id==current_user.professional_id): a.status="cancelled"; db.session.commit(); flash("Agendamento cancelado.","success")
    return redirect(url_for("appointments.index"))

@appointments_bp.get("/<int:appointment_id>/whatsapp")
@login_required
def whatsapp(appointment_id):
    if not admin(): return redirect(url_for("customer.dashboard"))
    a=db.session.get(Appointment,appointment_id)
    if not a or a.business_id!=current_user.business_id: return redirect(url_for("appointments.index"))
    msg=f"Olá, {a.client_name}! Sobre seu agendamento na {a.business.name}: {a.service.name} com {a.professional.name}, dia {a.date.strftime('%d/%m/%Y')} às {a.start_time}. Status: {a.status}."
    return redirect(wa_link(a.client_phone,msg))

@appointments_bp.get("/clientes")
@login_required
def clients():
    if not current_user.is_admin: return redirect(url_for("dashboard.index"))
    clients=User.query.filter_by(business_id=current_user.business_id,role="customer").order_by(User.name).all()
    return render_template("dashboard/clients.html",clients=clients,wa_link=wa_link)

@appointments_bp.get("/clientes/<int:user_id>")
@login_required
def client_detail(user_id):
    if not admin(): return redirect(url_for("customer.dashboard"))
    client=db.session.get(User,user_id)
    if not client or client.business_id!=current_user.business_id or not client.is_customer: return redirect(url_for("appointments.clients"))
    appointments=Appointment.query.filter_by(client_user_id=client.id).order_by(Appointment.date.desc(),Appointment.start_time.desc()).all()
    return render_template("dashboard/client_detail.html",client=client,appointments=appointments,wa_link=wa_link)
