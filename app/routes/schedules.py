from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .. import db
from ..models import Professional, Schedule, AvailabilityException, Appointment, Holiday

schedules_bp = Blueprint("schedules", __name__, url_prefix="/dashboard/schedules")
DAYS={1:"Segunda",2:"Terça",3:"Quarta",4:"Quinta",5:"Sexta",6:"Sábado",7:"Domingo"}

def admin_only(): return current_user.is_admin or current_user.is_professional

@schedules_bp.get("/")
@login_required
def index():
    if not admin_only(): return redirect(url_for("customer.dashboard"))
    professionals=Professional.query.filter_by(id=current_user.professional_id,active=True).all() if current_user.is_professional else Professional.query.filter_by(business_id=current_user.business_id,active=True).all()
    exceptions=AvailabilityException.query.join(Professional).filter(Professional.business_id==current_user.business_id,AvailabilityException.date>=date.today()).order_by(AvailabilityException.date).all()
    holidays=Holiday.query.filter_by(business_id=current_user.business_id).filter(Holiday.date>=date.today()).order_by(Holiday.date).all()
    return render_template("dashboard/schedules.html",professionals=professionals,exceptions=exceptions,holidays=holidays,days=DAYS,business=current_user.business,now_date=date.today().isoformat())

@schedules_bp.post("/create")
@login_required
def create():
    if not admin_only(): return redirect(url_for("customer.dashboard"))
    p=db.session.get(Professional,request.form.get("professional_id",type=int))
    if current_user.is_professional: p=db.session.get(Professional,current_user.professional_id)
    weekday=request.form.get("weekday",type=int); start=request.form.get("start_time",""); end=request.form.get("end_time","")
    if not p or p.business_id!=current_user.business_id or weekday not in range(1,8) or not start or not end or start>=end: flash("Horário inválido.","error"); return redirect(url_for("schedules.index"))
    overlap=Schedule.query.filter_by(professional_id=p.id,weekday=weekday).filter(Schedule.start_time<end,Schedule.end_time>start).first()
    if overlap: flash("Esse horário se sobrepõe a outro.","error")
    else: db.session.add(Schedule(professional_id=p.id,weekday=weekday,start_time=start,end_time=end)); db.session.commit(); flash("Horário adicionado.","success")
    return redirect(url_for("schedules.index"))

@schedules_bp.post("/delete/<int:schedule_id>")
@login_required
def delete(schedule_id):
    if not admin_only(): return redirect(url_for("customer.dashboard"))
    s=db.session.get(Schedule,schedule_id)
    if s and s.professional.business_id==current_user.business_id and (current_user.is_admin or s.professional_id==current_user.professional_id): db.session.delete(s); db.session.commit(); flash("Horário removido.","success")
    return redirect(url_for("schedules.index"))

@schedules_bp.post("/exception")
@login_required
def exception():
    if not admin_only(): return redirect(url_for("customer.dashboard"))
    p=db.session.get(Professional,request.form.get("professional_id",type=int));
    if current_user.is_professional: p=db.session.get(Professional,current_user.professional_id)
    kind=request.form.get("kind","day_off"); ds=request.form.get("date",""); reason=request.form.get("reason","").strip() or "Bloqueio"
    try: d=datetime.strptime(ds,"%Y-%m-%d").date()
    except ValueError: flash("Data inválida.","error"); return redirect(url_for("schedules.index"))
    if not p or p.business_id!=current_user.business_id: flash("Profissional inválido.","error"); return redirect(url_for("schedules.index"))
    start=request.form.get("start_time") or None; end=request.form.get("end_time") or None
    if kind=="blocked_time" and (not start or not end or start>=end): flash("Informe início e fim do bloqueio.","error"); return redirect(url_for("schedules.index"))
    db.session.add(AvailabilityException(professional_id=p.id,date=d,kind=kind,start_time=start,end_time=end,reason=reason)); db.session.commit(); flash("Exceção cadastrada.","success"); return redirect(url_for("schedules.index"))

@schedules_bp.post("/unblock-day")
@login_required
def unblock_day():
    if not admin_only(): return redirect(url_for("customer.dashboard"))
    e=db.session.get(AvailabilityException,request.form.get("exception_id",type=int))
    if e and e.professional.business_id==current_user.business_id and (current_user.is_admin or e.professional_id==current_user.professional_id): db.session.delete(e); db.session.commit(); flash("Exceção removida.","success")
    return redirect(url_for("schedules.index"))

@schedules_bp.post("/holiday")
@login_required
def holiday():
    if not current_user.is_admin: return redirect(url_for("customer.dashboard"))
    ds=request.form.get("date",""); name=request.form.get("name","").strip()
    try: d=datetime.strptime(ds,"%Y-%m-%d").date()
    except ValueError: flash("Data inválida.","error"); return redirect(url_for("schedules.index"))
    if not name: flash("Informe o nome do feriado.","error")
    else: db.session.add(Holiday(business_id=current_user.business_id,date=d,name=name)); db.session.commit(); flash("Feriado cadastrado.","success")
    return redirect(url_for("schedules.index"))

@schedules_bp.post("/holiday/<int:holiday_id>/delete")
@login_required
def holiday_delete(holiday_id):
    if not current_user.is_admin: return redirect(url_for("customer.dashboard"))
    h=db.session.get(Holiday,holiday_id)
    if h and h.business_id==current_user.business_id: db.session.delete(h); db.session.commit(); flash("Feriado removido.","success")
    return redirect(url_for("schedules.index"))

@schedules_bp.post("/settings")
@login_required
def settings():
    if not current_user.is_admin: return redirect(url_for("customer.dashboard"))
    b=current_user.business
    try:
        b.min_notice_hours=max(0,int(request.form.get("min_notice_hours",2))); b.max_days_ahead=max(1,int(request.form.get("max_days_ahead",60))); b.slot_interval=max(5,int(request.form.get("slot_interval",30)))
    except ValueError: flash("Configurações inválidas.","error"); return redirect(url_for("schedules.index"))
    db.session.commit(); flash("Regras da agenda atualizadas.","success"); return redirect(url_for("schedules.index"))

@schedules_bp.get("/api/calendar")
@login_required
def calendar():
    if not admin_only(): return jsonify({"error":"Não autorizado"}),403
    pid=request.args.get("professional_id",type=int)
    try: start=datetime.strptime(request.args.get("start",""),"%Y-%m-%d").date(); end=datetime.strptime(request.args.get("end",""),"%Y-%m-%d").date()
    except ValueError: return jsonify({"error":"Período inválido"}),400
    q=Professional.query.filter_by(id=current_user.professional_id,active=True) if current_user.is_professional else Professional.query.filter_by(business_id=current_user.business_id,active=True)
    if pid: q=q.filter_by(id=pid)
    pros=q.all(); days=[]; cur=start
    while cur<=end:
        items=[]
        for p in pros:
            dayoff=AvailabilityException.query.filter_by(professional_id=p.id,date=cur,kind="day_off").first(); holiday=Holiday.query.filter_by(business_id=p.business_id,date=cur).first()
            schedules=Schedule.query.filter_by(professional_id=p.id,weekday=cur.isoweekday()).all(); apps=Appointment.query.filter_by(professional_id=p.id,date=cur).filter(Appointment.status.in_(["pending","confirmed"])).all()
            blocked=AvailabilityException.query.filter_by(professional_id=p.id,date=cur,kind="blocked_time").all()
            state="holiday" if holiday else "blocked" if dayoff else "closed" if not schedules else "appointments" if apps else "open"
            items.append({"professional_id":p.id,"professional":p.name,"state":state,"appointments":len(apps),"hours":[f"{s.start_time}-{s.end_time}" for s in schedules],"blocked":[f"{x.start_time}-{x.end_time}" for x in blocked]})
        days.append({"date":cur.isoformat(),"items":items}); cur+=timedelta(days=1)
    return jsonify({"days":days})
