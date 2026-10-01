from pathlib import Path
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

db=SQLAlchemy(); login_manager=LoginManager(); login_manager.login_view="auth.login"

def create_app():
    app=Flask(__name__); app.config.from_object("config.Config"); Path(app.instance_path).mkdir(parents=True,exist_ok=True)
    db.init_app(app); login_manager.init_app(app)
    from .routes.auth import auth_bp
    from .routes.public import public_bp
    from .routes.dashboard import dashboard_bp
    from .routes.professionals import professionals_bp
    from .routes.schedules import schedules_bp
    from .routes.services import services_bp
    from .routes.appointments import appointments_bp
    from .routes.customer import customer_bp
    app.register_blueprint(auth_bp); app.register_blueprint(public_bp); app.register_blueprint(dashboard_bp); app.register_blueprint(professionals_bp); app.register_blueprint(schedules_bp); app.register_blueprint(services_bp); app.register_blueprint(appointments_bp); app.register_blueprint(customer_bp)
    with app.app_context():
        db.create_all(); migrate_sqlite(); seed_database()
    return app

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return db.session.get(User,int(user_id))

def add_column_if_missing(table,column,definition):
    insp=inspect(db.engine)
    if table not in insp.get_table_names(): return
    cols={c["name"] for c in insp.get_columns(table)}
    if column not in cols: db.session.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {definition}'))

def migrate_sqlite():
    add_column_if_missing("businesses","min_notice_hours","INTEGER NOT NULL DEFAULT 2")
    add_column_if_missing("businesses","max_days_ahead","INTEGER NOT NULL DEFAULT 60")
    add_column_if_missing("businesses","slot_interval","INTEGER NOT NULL DEFAULT 30")
    add_column_if_missing("availability_exceptions","kind","VARCHAR(30) NOT NULL DEFAULT 'day_off'")
    add_column_if_missing("availability_exceptions","start_time","VARCHAR(5)")
    add_column_if_missing("availability_exceptions","end_time","VARCHAR(5)")
    add_column_if_missing("appointments","source","VARCHAR(30) NOT NULL DEFAULT 'site'")
    add_column_if_missing("appointments","is_encaixe","BOOLEAN NOT NULL DEFAULT 0")
    add_column_if_missing("appointments","notes","TEXT")
    add_column_if_missing("users","professional_id","INTEGER")
    db.session.commit()

def seed_database():
    from .models import Business,User,Professional,Service,Schedule
    from werkzeug.security import generate_password_hash
    business=Business.query.first()
    if business:
        return
    business=Business(name="Barbearia Prime",phone="5511999999999",address="Av. Exemplo, 123 — Centro",instagram="@barbeariaprime",min_notice_hours=2,max_days_ahead=60,slot_interval=30); db.session.add(business); db.session.flush()
    db.session.add(User(name="Administrador",email="admin@prime.local",password_hash=generate_password_hash("admin123"),role="admin",business_id=business.id))
    pros=[Professional(name="João Silva",email="joao@prime.local",phone="5511988888888",active=True,business_id=business.id),Professional(name="Carlos Souza",email="carlos@prime.local",phone="5511977777777",active=True,business_id=business.id)]
    db.session.add_all(pros); db.session.flush()
    db.session.add(User(name="João Silva",email="joao@prime.local",phone=pros[0].phone,password_hash=generate_password_hash("joao123"),role="professional",business_id=business.id,professional_id=pros[0].id))
    db.session.add(User(name="Carlos Souza",email="carlos@prime.local",phone=pros[1].phone,password_hash=generate_password_hash("carlos123"),role="professional",business_id=business.id,professional_id=pros[1].id))
    db.session.add_all([Service(name="Corte Masculino",description="Corte personalizado.",price=45,duration=30,active=True,business_id=business.id),Service(name="Barba",description="Modelagem e acabamento.",price=30,duration=20,active=True,business_id=business.id),Service(name="Corte + Barba",description="Combo completo.",price=65,duration=50,active=True,business_id=business.id)])
    for p in pros:
        for weekday in range(1,7):
            if weekday==6: db.session.add(Schedule(professional_id=p.id,weekday=6,start_time="09:00",end_time="14:00"))
            else:
                db.session.add(Schedule(professional_id=p.id,weekday=weekday,start_time="09:00",end_time="12:00")); db.session.add(Schedule(professional_id=p.id,weekday=weekday,start_time="13:00",end_time="19:00"))
    db.session.commit()
