from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AlumniBase(BaseModel):
    nim: Optional[str] = None
    name: str
    campus: Optional[str] = "Universitas Muhammadiyah Malang"
    faculty: Optional[str] = None
    major: Optional[str] = "Informatika"
    graduation_year: Optional[str] = None
    source_platforms: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    ig_url: Optional[str] = None
    fb_url: Optional[str] = None
    tiktok_url: Optional[str] = None
    company: Optional[str] = None
    company_address: Optional[str] = None
    position: Optional[str] = None
    job_type: Optional[str] = None
    company_social_url: Optional[str] = None

class AlumniCreate(AlumniBase):
    pass

class AlumniResponse(AlumniBase):
    id: int
    status: str
    job: Optional[str] = "Belum ada hasil"
    job_source: Optional[str] = None
    job_url: Optional[str] = None
    profile_pic_url: Optional[str] = None
    notes: Optional[str] = None
    last_tracked: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaginatedAlumniResponse(BaseModel):
    data: List[AlumniResponse]
    total: int
    page: int
    limit: int

class TrackingResultBase(BaseModel):
    alumni_id: int
    source: str
    url: str
    extracted_info: str
    confidence_score: str

class TrackingResultResponse(TrackingResultBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
