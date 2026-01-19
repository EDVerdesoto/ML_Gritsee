from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
u = User(username="KAtest", hashed_password=get_password_hash("gritsee2023"))
db.add(u)
db.commit()
print("Usuario creado.")