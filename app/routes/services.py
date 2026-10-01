from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .. import db
from ..models import Service

services_bp = Blueprint("services", __name__, url_prefix="/dashboard/services")

@services_bp.get("/")
@login_required
def index():
    if not current_user.is_admin:
        return redirect(url_for("customer.dashboard"))
    services = Service.query.filter_by(business_id=current_user.business_id).all()
    return render_template("dashboard/services.html", services=services)

@services_bp.post("/create")
@login_required
def create():
    if not current_user.is_admin:
        return redirect(url_for("customer.dashboard"))
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    price = request.form.get("price", "0").replace(",", ".")
    duration = request.form.get("duration", "30")

    try:
        price = float(price)
        duration = int(duration)
    except ValueError:
        flash("Preço ou duração inválidos.", "error")
        return redirect(url_for("services.index"))

    if not name or price < 0 or duration <= 0:
        flash("Preencha os dados corretamente.", "error")
        return redirect(url_for("services.index"))

    db.session.add(Service(
        business_id=current_user.business_id,
        name=name,
        description=description,
        price=price,
        duration=duration,
        active=True
    ))
    db.session.commit()
    flash("Serviço criado.", "success")
    return redirect(url_for("services.index"))
