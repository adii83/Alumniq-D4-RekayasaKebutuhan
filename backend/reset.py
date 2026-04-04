from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text("UPDATE alumni SET status = 'Belum Ditemukan', job = 'Pelacakan gagal (Error di background)' WHERE status = 'Sedang Dilacak...'"))
        conn.commit()
    print("Database Reset OK - Semua 'Sedang Dilacak...' diubah jadi 'Belum Ditemukan'")
except Exception as e:
    print(f"Error resetting database: {e}")
