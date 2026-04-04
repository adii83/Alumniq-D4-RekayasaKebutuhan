from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base

class Alumni(Base):
    __tablename__ = "alumni"

    id = Column(Integer, primary_key=True, index=True)
    nim = Column(String, index=True, nullable=True)
    name = Column(String, index=True)
    campus = Column(String, default="Universitas Muhammadiyah Malang") 
    faculty = Column(String, nullable=True)
    major = Column(String, default="Informatika")
    graduation_year = Column(String, nullable=True)
    status = Column(String, default="Belum Dilacak") # Belum Dilacak, Perlu Verifikasi, Teridentifikasi
    job = Column(String, nullable=True, default="Belum ada hasil")
    job_source = Column(String, nullable=True) # E.g., LinkedIn, Google Scholar
    job_url = Column(String, nullable=True) # Actual URL from the finding
    source_platforms = Column(String, nullable=True) # Comma-separated list of selected platforms
    profile_pic_url = Column(String, nullable=True)
    notes = Column(String, nullable=True)  # Catatan / Bukti pelacakan manual
    email = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    ig_url = Column(String, nullable=True)
    fb_url = Column(String, nullable=True)
    tiktok_url = Column(String, nullable=True)
    company = Column(String, nullable=True)
    company_address = Column(String, nullable=True)
    position = Column(String, nullable=True)
    job_type = Column(String, nullable=True) # PNS, Swasta, Wirausaha
    company_social_url = Column(String, nullable=True)
    last_tracked = Column(DateTime(timezone=True), nullable=True)

class TrackingResult(Base):
    __tablename__ = "tracking_results"

    id = Column(Integer, primary_key=True, index=True)
    alumni_id = Column(Integer, index=True)
    source = Column(String) # LinkedIn, Google Scholar, dll
    url = Column(String)
    extracted_info = Column(String)
    confidence_score = Column(String) # Rendah, Sedang, Tinggi
    created_at = Column(DateTime(timezone=True), server_default=func.now())
