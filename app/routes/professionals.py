from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from .. import db
from ..models import Professional, User

professionals_bp=Blueprint("professionals",__name__,url_prefix="/dashboard/professionals")
@professionals_bp.get("/")
@login_required
def index():
    if not current_user.is_admin: return redirect(url_for("dashboard.index"))
    professionals=Professional.query.filter_by(business_id=current_user.business_id).all()
    return render_template("dashboard/professionals.html",professionals=professionals)
@professionals_bp.post("/create")
@login_required
def create():
    if not current_user.is_admin: return redirect(url_for("dashboard.index"))
    name=request.form.get("name","").strip(); email=request.form.get("email","").strip().lower(); phone=request.form.get("phone","").strip(); password=request.form.get("password","")
    if not name or not email or not password: flash("Nome, e-mail e senha são obrigatórios para criar o acesso do barbeiro.","error"); return redirect(url_for("professionals.index"))
    if User.query.filter_by(email=email).first(): flash("Esse e-mail já está cadastrado.","error"); return redirect(url_for("professionals.index"))
    p=Professional(name=name,email=email,phone=phone,active=True,business_id=current_user.business_id); db.session.add(p); db.session.flush(); db.session.add(User(name=name,email=email,phone=phone,password_hash=generate_password_hash(password),role="professional",business_id=current_user.business_id,professional_id=p.id)); db.session.commit(); flash("Barbeiro criado com acesso próprio.","success"); return redirect(url_for("professionals.index"))
