from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from ..models import User, Business
from .. import db

auth_bp=Blueprint("auth",__name__)
def redirect_after_login(): return redirect(url_for("dashboard.index" if (current_user.is_admin or current_user.is_professional) else "customer.dashboard"))
@auth_bp.route("/login",methods=["GET","POST"])
def login():
    if current_user.is_authenticated: return redirect_after_login()
    if request.method=="POST":
        user=User.query.filter_by(email=request.form.get("email","").strip().lower()).first()
        if user and check_password_hash(user.password_hash,request.form.get("password","")): login_user(user); return redirect_after_login()
        flash("E-mail ou senha inválidos.","error")
    return render_template("login.html")
@auth_bp.route("/cadastro",methods=["GET","POST"])
def register():
    if current_user.is_authenticated: return redirect_after_login()
    if request.method=="POST":
        name=request.form.get("name","").strip(); email=request.form.get("email","").strip().lower(); phone=request.form.get("phone","").strip(); password=request.form.get("password",""); confirm=request.form.get("confirm_password","")
        if not all([name,email,phone,password]): flash("Preencha todos os campos.","error")
        elif len(password)<6: flash("A senha deve ter pelo menos 6 caracteres.","error")
        elif password!=confirm: flash("As senhas não coincidem.","error")
        elif User.query.filter_by(email=email).first(): flash("Esse e-mail já está cadastrado.","error")
        else:
            business=Business.query.first(); user=User(name=name,email=email,phone=phone,password_hash=generate_password_hash(password),role="customer",business_id=business.id); db.session.add(user); db.session.commit(); login_user(user); flash("Conta criada!","success"); return redirect(url_for("customer.dashboard"))
    return render_template("register.html")
@auth_bp.post("/logout")
def logout(): logout_user(); return redirect(url_for("auth.login"))
