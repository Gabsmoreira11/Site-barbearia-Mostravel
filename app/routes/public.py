from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from ..models import Business, Professional, Service

public_bp = Blueprint("public", __name__)

@public_bp.get("/")
def home():
    business=Business.query.first()
    services=Service.query.filter_by(business_id=business.id, active=True).all()
    professionals=Professional.query.filter_by(business_id=business.id, active=True).all()
    return render_template("public/index.html", business=business, services=services, professionals=professionals)
