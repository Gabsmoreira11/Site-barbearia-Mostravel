from datetime import date, datetime, timedelta
from urllib.parse import quote
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .. import db
from ..models import Appointment, Professional, Service, Schedule, AvailabilityException, Holiday

customer_bp = Blueprint("customer", __name__, url_prefix="/cliente")


def parse_time(value):
    return datetime.strptime(value, "%H:%M").time()


def intervals(professional, selected_date):
    business = professional.business
    if Holiday.query.filter_by(business_id=business.id, date=selected_date).first():
        return []
    exception = AvailabilityException.query.filter_by(professional_id=professional.id, date=selected_date).all()
    if any(e.kind == "day_off" for e in exception):
        return []
    base = [(parse_time(s.start_time), parse_time(s.end_time)) for s in
            Schedule.query.filter_by(professional_id=professional.id, weekday=selected_date.isoweekday()).order_by(Schedule.start_time).all()]
    if not base:
        return []
    special = [e for e in exception if e.kind == "special_hours" and e.start_time and e.end_time]
    if special:
        base = [(parse_time(e.start_time), parse_time(e.end_time)) for e in special]
    blocked = [(parse_time(e.start_time), parse_time(e.end_time)) for e in exception if e.kind == "blocked_time" and e.start_time and e.end_time]
    return [(a, b) for a, b in base if not any(a < be and b > bs for bs, be in blocked)]


def slots_for(professional, service, selected_date):
    business = professional.business
    today = date.today()
    if selected_date < today or selected_date > today + timedelta(days=business.max_days_ahead):
        return []
    if selected_date == today and datetime.now() + timedelta(hours=business.min_notice_hours) >= datetime.combine(selected_date, datetime.max.time()):
        return []
    work = intervals(professional, selected_date)
    if not work:
        return []
    appointments = Appointment.query.filter_by(professional_id=professional.id, date=selected_date).filter(
        Appointment.status.in_(["pending", "confirmed"])
    ).all()
    interval = max(5, business.slot_interval)
    result = []
    for start, finish in work:
        current = datetime.combine(selected_date, start)
        end_dt = datetime.combine(selected_date, finish)
        while current + timedelta(minutes=service.duration) <= end_dt:
            slot_start = current.time()
            slot_end = (current + timedelta(minutes=service.duration)).time()
            if selected_date == today and current < datetime.now() + timedelta(hours=business.min_notice_hours):
                current += timedelta(minutes=interval); continue
            conflict = any(slot_start < parse_time(a.end_time) and slot_end > parse_time(a.start_time) for a in appointments)
            blocked = any(slot_start < be and slot_end > bs for bs, be in [
                (parse_time(e.start_time), parse_time(e.end_time)) for e in AvailabilityException.query.filter_by(professional_id=professional.id, date=selected_date, kind="blocked_time").all() if e.start_time and e.end_time
            ])
            if not conflict and not blocked:
                result.append(current.strftime("%H:%M"))
            current += timedelta(minutes=interval)
    return result


def calendar_days(professional, start, end):
    result=[]; cursor=start; business=professional.business
    while cursor <= end:
        times=[]
        for service in Service.query.filter_by(business_id=business.id, active=True).all():
            times.extend(slots_for(professional, service, cursor))
        times=set(times)
        blocked=AvailabilityException.query.filter_by(professional_id=professional.id,date=cursor).filter(AvailabilityException.kind=="day_off").first()
        holiday=Holiday.query.filter_by(business_id=business.id,date=cursor).first()
        schedules=Schedule.query.filter_by(professional_id=professional.id,weekday=cursor.isoweekday()).count()
        appointments=Appointment.query.filter_by(professional_id=professional.id,date=cursor).filter(Appointment.status.in_(["pending","confirmed"])).count()
        if holiday: state="holiday"; label=holiday.name
        elif blocked: state="blocked"; label=blocked.reason or "Folga"
        elif not schedules: state="closed"; label="Não trabalha"
        elif not times: state="full"; label="Lotado"
        elif len(times) <= 3: state="few"; label="Poucos horários"
        else: state="open"; label="Disponível"
        result.append({"date":cursor.isoformat(),"state":state,"label":label,"appointments":appointments,"remaining":len(times)})
        cursor += timedelta(days=1)
    return result

@customer_bp.get("/")
@login_required
def dashboard():
    appointments=Appointment.query.filter_by(client_user_id=current_user.id).order_by(Appointment.date.desc(), Appointment.start_time).all()
    return render_template("customer/dashboard.html", appointments=appointments, today=date.today())

@customer_bp.get("/agendar")
@login_required
def booking():
    services=Service.query.filter_by(business_id=current_user.business_id, active=True).all()
    professionals=Professional.query.filter_by(business_id=current_user.business_id, active=True).all()
    return render_template("customer/booking.html", services=services, professionals=professionals, user=current_user, today=date.today(), business=current_user.business)

@customer_bp.get("/api/availability")
@login_required
def availability():
    professional=db.session.get(Professional, request.args.get("professional_id", type=int))
    service=db.session.get(Service, request.args.get("service_id", type=int))
    try: selected_date=datetime.strptime(request.args.get("date", ""), "%Y-%m-%d").date()
    except ValueError: return jsonify({"error":"Data inválida."}),400
    if not professional or not service or professional.business_id != current_user.business_id or service.business_id != current_user.business_id:
        return jsonify({"error":"Dados inválidos."}),400
    return jsonify({"available_times":slots_for(professional,service,selected_date)})

@customer_bp.get("/api/calendar")
@login_required
def calendar():
    professional=db.session.get(Professional, request.args.get("professional_id", type=int))
    try:
        start=datetime.strptime(request.args.get("start", ""), "%Y-%m-%d").date(); end=datetime.strptime(request.args.get("end", ""), "%Y-%m-%d").date()
    except ValueError: return jsonify({"error":"Período inválido"}),400
    if not professional or professional.business_id != current_user.business_id: return jsonify({"error":"Profissional inválido"}),400
    return jsonify({"days":calendar_days(professional,start,end)})

@customer_bp.post("/api/agendar")
@login_required
def create():
    data=request.get_json(silent=True) or {}
    try:
        professional=db.session.get(Professional,int(data.get("professional_id")))
        service=db.session.get(Service,int(data.get("service_id")))
        selected_date=datetime.strptime(data.get("date",""),"%Y-%m-%d").date()
        start=parse_time(data.get("start_time",""))
    except (ValueError,TypeError): return jsonify({"error":"Dados inválidos."}),400
    if not professional or not service or professional.business_id != current_user.business_id or service.business_id != current_user.business_id:
        return jsonify({"error":"Dados inválidos."}),400
    if data.get("start_time") not in slots_for(professional,service,selected_date): return jsonify({"error":"Esse horário não está mais disponível."}),409
    end=(datetime.combine(selected_date,start)+timedelta(minutes=service.duration)).time()
    appointment=Appointment(business_id=current_user.business_id,professional_id=professional.id,service_id=service.id,client_user_id=current_user.id,client_name=current_user.name,client_phone=current_user.phone,date=selected_date,start_time=start.strftime("%H:%M"),end_time=end.strftime("%H:%M"),status="pending",source="site",notes=data.get("notes"))
    db.session.add(appointment); db.session.commit()
    msg=quote(f"Olá! Sou {current_user.name}. Solicitei o agendamento #{appointment.id}: {service.name} com {professional.name}, dia {selected_date.strftime('%d/%m/%Y')} às {start.strftime('%H:%M')}. Aguardo a confirmação.")
    phone="".join(ch for ch in (professional.phone or professional.business.phone or "") if ch.isdigit())
    return jsonify({"message":"Pedido enviado! O horário ficou pendente de confirmação.","appointment_id":appointment.id,"whatsapp_url":f"https://wa.me/{phone}?text={msg}" if phone else None}),201

@customer_bp.post("/agendamentos/<int:appointment_id>/cancelar")
@login_required
def cancel(appointment_id):
    appointment=db.session.get(Appointment,appointment_id)
    if not appointment or appointment.client_user_id != current_user.id: flash("Agendamento não encontrado.","error")
    elif appointment.status in ("completed","cancelled"): flash("Esse agendamento não pode mais ser cancelado.","error")
    else: appointment.status="cancelled"; db.session.commit(); flash("Agendamento cancelado.","success")
    return redirect(url_for("customer.dashboard"))
