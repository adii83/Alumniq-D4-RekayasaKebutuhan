import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import os
import time

def recreate_db():
    print("Recreating database tables...")
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)

def import_excel(filepath: str):
    print(f"Reading excel: {filepath}")
    
    start_time = time.time()
    df = pd.read_excel(filepath)
    print(f"Total rows found: {len(df)}")
    
    col_name = None
    col_nim = None
    col_major = None
    col_faculty = None
    col_year = None
    
    for c in df.columns:
        if "Nama" in str(c): col_name = c
        if "NIM" in str(c): col_nim = c
        if "Program Studi" in str(c): col_major = c
        if "Fakultas" in str(c): col_faculty = c
        if "Tahun Lulus" in str(c) or "Tdi" in str(c): col_year = c

    if not col_name:
        print("Kolom 'Nama Lulusan' tidak ditemukan.")
        return

    # Buang nan
    df[col_name] = df[col_name].fillna("")
    df = df[df[col_name].str.strip() != ""]
    df = df.iloc[::-1].reset_index(drop=True)

    db: Session = SessionLocal()
    
    try:
        recreate_db()

        records = []
        count = 0
        
        # Iterasi efisien ke dictionaries
        data_dicts = df.to_dict('records')
        
        for row in data_dicts:
            name = str(row.get(col_name, "")).strip()
            
            # Extract safe values
            nim_val = row.get(col_nim)
            nim = str(int(nim_val)) if pd.notnull(nim_val) and isinstance(nim_val, float) else str(nim_val) if pd.notnull(nim_val) else None
            
            major = str(row.get(col_major, "Tidak Diketahui")).strip()
            faculty = str(row.get(col_faculty, "")).strip() if pd.notnull(row.get(col_faculty)) else None
            
            year_val = row.get(col_year)
            year = str(int(year_val)) if pd.notnull(year_val) and isinstance(year_val, float) else str(year_val) if pd.notnull(year_val) else None

            if name:
                alumni = models.Alumni(
                    nim=nim,
                    name=name,
                    campus="Universitas Muhammadiyah Malang",
                    faculty=faculty,
                    major=major,
                    graduation_year=year,
                    status="Belum Dilacak"
                )
                records.append(alumni)
                count += 1
                
                # Bulk insert chunking (per 10,000)
                if count % 10000 == 0:
                    db.bulk_save_objects(records)
                    db.commit()
                    records = []
                    print(f"Inserted {count} records...")

        # Insert sisa array
        if records:
            db.bulk_save_objects(records)
            db.commit()
            
        print(f"Berhasil import TOTAL {count} profil alumni ke database dalam {round(time.time() - start_time, 2)} detik.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    file_path = r"../Data Alumni.xlsx"
    import_excel(file_path)
