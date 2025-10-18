from app.config.db import Base, engine
from app.models.User import User

print("📦 Membuat tabel database...")
Base.metadata.create_all(bind=engine)
print("✅ Tabel berhasil dibuat!")
