from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import time
import random
import requests
from urllib.parse import quote_plus, urlparse
from bs4 import BeautifulSoup
import os
import hmac
import json
import base64
import hashlib
import secrets

import models, schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistem Pelacakan Alumni API")

TOKEN_TTL_SECONDS = int(os.getenv("TOKEN_TTL_SECONDS", "28800"))
LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
LOGIN_WINDOW_SECONDS = int(os.getenv("LOGIN_WINDOW_SECONDS", "600"))
LOGIN_LOCKOUT_SECONDS = int(os.getenv("LOGIN_LOCKOUT_SECONDS", "900"))
_login_attempts: dict[str, dict] = {}


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def get_secret_key() -> str:
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise HTTPException(
            status_code=500,
            detail="SECRET_KEY belum dikonfigurasi pada environment server.",
        )
    return secret_key


def get_admin_username() -> str:
    username = os.getenv("ADMIN_USERNAME")
    if not username:
        raise HTTPException(
            status_code=500,
            detail="ADMIN_USERNAME belum dikonfigurasi pada environment server.",
        )
    return username


def get_admin_password() -> str:
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        raise HTTPException(
            status_code=500,
            detail="ADMIN_PASSWORD belum dikonfigurasi pada environment server.",
        )
    return password


def create_token(username: str) -> str:
    secret_key = get_secret_key()
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
        "jti": secrets.token_urlsafe(12),
    }
    header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_base64url_encode(signature)}"


def verify_token(token: str) -> dict:
    secret_key = get_secret_key()
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_signature = hmac.new(secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
        provided_signature = _base64url_decode(signature_b64)
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise ValueError("Invalid signature")
        payload = json.loads(_base64url_decode(payload_b64).decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("Token expired")
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Token tidak valid atau sudah kedaluwarsa.")


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def ensure_login_allowed(client_ip: str) -> None:
    now = time.time()
    state = _login_attempts.get(client_ip)
    if not state:
        return
    if state.get("locked_until", 0) > now:
        retry_after = int(state["locked_until"] - now)
        raise HTTPException(
            status_code=429,
            detail=f"Terlalu banyak percobaan login. Coba lagi dalam {retry_after} detik.",
        )
    if state.get("window_start", 0) + LOGIN_WINDOW_SECONDS <= now:
        _login_attempts.pop(client_ip, None)


def record_login_failure(client_ip: str) -> None:
    now = time.time()
    state = _login_attempts.get(client_ip)
    if not state or state.get("window_start", 0) + LOGIN_WINDOW_SECONDS <= now:
        state = {"count": 0, "window_start": now, "locked_until": 0}
    state["count"] += 1
    if state["count"] >= LOGIN_MAX_ATTEMPTS:
        state["locked_until"] = now + LOGIN_LOCKOUT_SECONDS
    _login_attempts[client_ip] = state


def clear_login_failures(client_ip: str) -> None:
    _login_attempts.pop(client_ip, None)


def require_auth(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token otorisasi tidak ditemukan.")
    token = authorization.removeprefix("Bearer ").strip()
    payload = verify_token(token)
    return payload.get("sub", "")

@app.on_event("startup")
def reset_stuck_tracking():
    # Fitur canggih: Membersihkan riwayat 'Sedang Dilacak...' yang nyangkut karena server render terputus
    from database import SessionLocal
    import models
    db = SessionLocal()
    try:
        stuck = db.query(models.Alumni).filter(models.Alumni.status == 'Sedang Dilacak...').all()
        for s in stuck:
            s.status = 'Gagal'
        if stuck:
            db.commit()
            print(f"[System] Berhasil me-reset {len(stuck)} data alumni yang tersangkut.")
    except Exception as e:
        pass
    finally:
        db.close()

# Configure CORS for frontend access
origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "https://adii83.github.io",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _fetch_text(url: str, timeout: int = 8) -> str:
    """
    Helper: ambil HTML teks dari sebuah URL dengan headers sederhana.
    Digunakan hanya untuk simulasi tugas, bukan scraping agresif.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AlumniTracker/1.0; +https://example.com)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200 and resp.text:
            return resp.text.lower()
    except Exception:
        return ""
    return ""


def fetch_data_dari_internet(query: str, max_pages: int = 2) -> list[dict]:
    """
    Mengambil kandidat hasil pencarian menggunakan Playwright (Headless Browser).
    Playwright membuka Chromium sungguhan sehingga tidak terdeteksi sebagai bot.
    """
    print(f"[Scraper] Menyelami Internet untuk: \"{query}\"")
    semua_hasil: list[dict] = []

    try:
        from playwright.sync_api import sync_playwright
        from urllib.parse import unquote, urlparse, parse_qs
        import re

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="id-ID",
            )
            page = ctx.new_page()

            for pg in range(max_pages):
                b_code = pg * 10 + 1
                search_url = f"https://search.yahoo.com/search?p={query.replace(' ', '+')}&b={b_code}"
                try:
                    page.goto(search_url, timeout=20000, wait_until="domcontentloaded")
                    page.wait_for_load_state("networkidle", timeout=12000)
                except Exception:
                    pass  # Lanjut walau timeout

                try:
                    page.wait_for_timeout(1200)
                    current_url = page.url
                    page_title = page.title()
                    html = page.content()
                    soup = BeautifulSoup(html, "html.parser")
                except Exception as parse_error:
                    print(f"[Scraper] Gagal membaca konten halaman: {parse_error}")
                    break

                results = soup.select(".compTitle")
                if not results:
                    results = soup.select("h3.title")
                if not results:
                    snippet = " ".join(soup.get_text(" ", strip=True).split())[:500]
                    print(f"[Scraper] Tidak ada selector hasil untuk URL akhir: {current_url}")
                    print(f"[Scraper] Judul halaman: {page_title}")
                    print(f"[Scraper] Potongan konten: {snippet}")
                    break

                ada_hasil = False
                for comp in results:
                    a = comp.select_one("a")
                    if not a:
                        continue
                    title = a.get_text(" ", strip=True)
                    href = a.get("href", "").strip()

                    # Ekstrak URL asli dari redirect Yahoo
                    if "yahoo.com" in href and "RU=" in href:
                        try:
                            parsed = urlparse(href)
                            href = unquote(parse_qs(parsed.query).get("RU", [""])[0])
                        except Exception:
                            pass

                    # Ambil snippet dari blok parent hasil pencarian
                    parent = comp.find_parent("li") or comp.find_parent("div")
                    snip = parent.get_text(" ", strip=True) if parent else comp.get_text(" ", strip=True)
                    snip = snip[:300]  # Batasi panjang

                    if not title or not href or "yahoo.com" in href:
                        continue

                    semua_hasil.append({
                        "sinyal_nama": title,
                        "sinyal_pekerjaan": snip,
                        "sinyal_afiliasi": snip,
                        "sinyal_tahun": "2023",
                        "sumber": "Yahoo Search",
                        "link": href,
                    })
                    ada_hasil = True

                if not ada_hasil:
                    break
                time.sleep(1.5)

            browser.close()

    except Exception as e:
        print(f"[Scraper] Playwright error: {e}")

    print(f"[Scraper] Ditemukan total {len(semua_hasil)} jejak publik.")
    return semua_hasil


def hitung_bobot_kecocokan(alumni: models.Alumni, kandidat: dict) -> tuple[int, int]:
    """
    Hitung skor kecocokan kandidat terhadap profil alumni.
    Mengembalikan (total_skor, match_nama).
    """
    total_skor = 0
    match_nama = 0

    nama_master = (alumni.name or "").strip().lower()
    if not nama_master:
        return 0, 0

    nama_pisah = [p for p in nama_master.split() if p]
    teks_terkumpul = (
        (kandidat.get("sinyal_nama") or "") + " " + (kandidat.get("sinyal_pekerjaan") or "")
    ).lower()

    if nama_master and nama_master in teks_terkumpul:
        match_nama = 60
    else:
        kata_cocok = 0
        for kata in nama_pisah:
            if len(kata) > 2 and kata in teks_terkumpul:
                kata_cocok += 1
        if kata_cocok > 0 and len(nama_pisah) > 0:
            match_nama = int((kata_cocok / len(nama_pisah)) * 40)

    total_skor += match_nama

    nama_kampus = (alumni.campus or "").strip().lower()
    if nama_kampus:
        import re
        pola_kampus = re.compile(
            rf"({re.escape(nama_kampus)}|umm|muhammadiyah malang|universitas muhammadiyah)",
            re.IGNORECASE,
        )
        if pola_kampus.search(teks_terkumpul):
            total_skor += 40

    import re
    prodi = (alumni.major or "").strip().lower()
    kata_prodi = prodi.split(" ")[0] if prodi else ""
    regex_prodi = re.compile(re.escape(kata_prodi), re.IGNORECASE) if kata_prodi else None
    regex_umum = re.compile(
        r"(engineer|developer|software|analyst|dokter|dosen|guru|student|mahasiswa|lulusan|alumni)",
        re.IGNORECASE,
    )

    if (regex_prodi and regex_prodi.search(teks_terkumpul)) or regex_umum.search(teks_terkumpul):
        total_skor += 20

    return total_skor, match_nama


def mock_scraping_task(alumni_id: int): # Tidak lagi butuh db dari argumen
    """
    Pelacakan berbasis Yahoo Search
    """
    from database import SessionLocal
    db = SessionLocal() # Buat session sendiri untuk background task
    try:
        alumni = db.query(models.Alumni).filter(models.Alumni.id == alumni_id).first()
        if not alumni:
            db.close()
            return

        # Hapus hasil pelacakan lama agar tidak menumpuk saat dilacak ulang
        db.query(models.TrackingResult).filter(models.TrackingResult.alumni_id == alumni_id).delete()
        db.commit()

        time.sleep(1) # Reduced initial delay

        # Query berbasis NAMA + UNIVERSITAS (tidak memperdulikan major/prodi)
        # Kami modifikasi agar query lebih general untuk mendapatkan hasil nyata (Bing)
        query1 = f"\"{alumni.name}\" {alumni.campus or ''}".strip()
        query2 = f"{alumni.name} LinkedIn {alumni.campus or ''}".strip()

        kandidat1 = fetch_data_dari_internet(query1)
        kandidat2 = fetch_data_dari_internet(query2) if not kandidat1 else []

        semua_kandidat = kandidat1 + kandidat2
        
        def map_domain_to_platform(link: str) -> str:
            domain = urlparse(link).netloc.lower()
            if "linkedin.com" in domain:
                return "LinkedIn"
            if "scholar.google." in domain:
                return "Google Scholar"
            if "researchgate.net" in domain:
                return "ResearchGate"
            if "orcid.org" in domain:
                return "ORCID"
            if "github.com" in domain:
                return "GitHub"
            if "kaggle.com" in domain:
                return "Kaggle"
            if domain:
                return domain
            return "Google Umum"

        kandidat_potensial: list[dict] = []
        kandidat_terbaik = None
        skor_tertinggi = 0

        for k in semua_kandidat:
            skor, match_nama = hitung_bobot_kecocokan(alumni, k)
            platform = map_domain_to_platform(k.get("link", ""))

            allowed_platforms = [s.strip() for s in (alumni.source_platforms or "").split(',')] if alumni.source_platforms else []
            
            # Jika platform (misal kompasiana.com) tidak ada di allowed_platforms, 
            # kita kategorikan sebagai "Google Umum" atau "Website Perusahaan", 
            # JANGAN DIBUANG jika memang informasinya sangat valid (skor tinggi).
            if allowed_platforms and platform not in allowed_platforms:
                if "Google Umum" in allowed_platforms:
                    platform = "Google Umum"
                elif "Website Perusahaan" in allowed_platforms:
                    platform = "Website Perusahaan"
                else:
                    # Jika user tidak ceklis Google Umum/Situs Perusahaan, 
                    # barulah kita buang hasil dari domain random ini
                    continue

            # Log skor untuk mempermudah debugging
            print(f"[{platform}] M={match_nama} T={skor} | {k.get('sinyal_nama', '')[:50]}...")

            # Kriteria dilonggarkan sedikit agar hasil tidak gampang terbuang
            if match_nama >= 10 and skor >= 30:
                entry = {**k, "skor": skor, "platform": platform}
                kandidat_potensial.append(entry)

        print(f"[Scraper] Dari {len(semua_kandidat)} jejak, {len(kandidat_potensial)} masuk potensial.")

        # Filter unik berdasarkan link (menghindari duplikat dari multi query)
        unik_links = set()
        kandidat_unik = []
        
        for pot in kandidat_potensial:
            link = pot.get("link")
            if link not in unik_links:
                unik_links.add(link)
                kandidat_unik.append(pot)
                
        # Sort: Platform spesifik SELALU di atas Google Umum, lalu by skor, lalu urutan platform
        _platform_order = {
            'LinkedIn': 1, 'Google Scholar': 2, 'ResearchGate': 3,
            'ORCID': 4, 'GitHub': 5, 'Kaggle': 6, 'Website Perusahaan': 7, 'Google Umum': 99
        }
        kandidat_unik.sort(key=lambda x: (
            1 if x.get("platform", "") == "Google Umum" else 0,  # Google Umum selalu terakhir
            -x["skor"],                                           # Skor tertinggi dulu
            _platform_order.get(x.get("platform", ""), 50)        # Urutan platform
        ))
        
        # KANDIDAT TERBAIK ADALAH YANG PERTAMA SETELAH DISORTIR 
        # (Agar sinkron 100% dengan urutan Card di Frontend)
        kandidat_terbaik = kandidat_unik[0] if kandidat_unik else None

        # =====================================================
        # TAHAP PENENTUAN STATUS (Algoritma Kecocokan 70%)
        # Mengikuti logika referensi milik teman pengguna
        # =====================================================
        status_akhir = "Belum Ditemukan"

        if kandidat_terbaik:
            tahun_diperbarui = alumni.graduation_year
            
            # Ekstraksi Tahun
            if not tahun_diperbarui or tahun_diperbarui.strip() == "-" or tahun_diperbarui.strip() == "":
                import re
                teks_bukti = (kandidat_terbaik.get("sinyal_nama", "") + " " + kandidat_terbaik.get("sinyal_pekerjaan", ""))
                match_tahun = re.search(r"\b(19|20)\d{2}\b", teks_bukti)
                if match_tahun:
                    tahun_diperbarui = match_tahun.group(0)
                    
            # Hitung Persentase Kecocokan (Nama + Kampus)
            import re
            kampus = (alumni.campus or "").lower()
            regex_kampus = re.compile(rf"({re.escape(kampus)}|umm|muhammadiyah malang|universitas muhammadiyah)", re.IGNORECASE)
            
            jumlah_kokoh = 0
            for pot in kandidat_unik:
                teks_pot = (pot.get("sinyal_nama", "") + " " + pot.get("sinyal_pekerjaan", "")).lower()
                nama_cocok = (alumni.name or "").lower() in teks_pot if alumni.name else False
                kampus_cocok = bool(regex_kampus.search(teks_pot))
                
                if nama_cocok and kampus_cocok:
                    jumlah_kokoh += 1
                    
            total_kandidat = len(kandidat_unik)
            persen_kokoh = (jumlah_kokoh / total_kandidat * 100) if total_kandidat > 0 else 0
            
            # Keputusan: User minta 'manual saja'. 
            # Jadi kita selalu set 'Perlu Verifikasi Manual' jika ada hasil, 
            # JANGAN otomatis Teridentifikasi agar user bisa cek kartu satu-satu.
            skor_tertinggi = kandidat_terbaik["skor"] if kandidat_terbaik else 0
            if jumlah_kokoh >= 1 or skor_tertinggi >= 40:
                status_akhir = "Perlu Verifikasi Manual"
            else:
                status_akhir = "Belum Ditemukan"
                
            alumni.status = status_akhir
            alumni.graduation_year = tahun_diperbarui
            
            # JANGAN otomatis isi job dan source jika mau proses manual 100%.
            # Biarkan user yang klik 'Simpan Bukti' di modal.
            alumni.job = "Belum diverifikasi (Tinjau Hasil)"
            alumni.job_source = None
            alumni.job_url = None
                
            # TAHAP 8: SIMPAN BUKTI AUDIT
            for pot in kandidat_unik[:10]: # Max 10 log per session
                if pot["skor"] >= 80:
                    conf_label = "Tinggi"
                elif pot["skor"] >= 50:
                    conf_label = "Sedang"
                else:
                    conf_label = "Rendah"

                extracted = (pot.get("sinyal_pekerjaan") or pot.get("sinyal_nama") or "")[:300]
                tr = models.TrackingResult(
                    alumni_id=alumni.id,
                    source=pot["platform"],
                    url=pot.get("link") or "",
                    extracted_info=f"[Skor {pot['skor']}%] {extracted}",
                    confidence_score=conf_label,
                )
                db.add(tr)
                
        else:
            alumni.status = "Belum Ditemukan"
            alumni.job = "Belum ada hasil"
            alumni.job_source = None
        
        alumni.last_tracked = datetime.now()
        db.commit()
        db.close() # Pastikan ditutup manual
        print(f"[Done] Pelacakan selesai untuk ID: {alumni_id}")
    except Exception as e:
        print(f"[Error] Gagal saat pelacakan background: {e}")
        if 'db' in locals():
            try:
                db.rollback()
                alumni.status = "Gagal"
                alumni.last_tracked = datetime.now()
                db.commit()
            except:
                pass
            db.close()

class LoginRequest(schemas.BaseModel):
    username: str
    password: str

@app.post("/login")
def login(request: LoginRequest, http_request: Request):
    client_ip = get_client_ip(http_request)
    ensure_login_allowed(client_ip)

    valid_username = get_admin_username()
    valid_password = get_admin_password()

    if hmac.compare_digest(request.username, valid_username) and hmac.compare_digest(request.password, valid_password):
        clear_login_failures(client_ip)
        return {"token": create_token(valid_username), "expires_in": TOKEN_TTL_SECONDS}

    record_login_failure(client_ip)
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/alumni/", response_model=schemas.AlumniResponse)
def create_alumni(alumni: schemas.AlumniCreate, db: Session = Depends(get_db), _: str = Depends(require_auth)):
    # We no longer check for unique NIM based on user request. 
    # Just insert the new target directly.
    new_alumni = models.Alumni(
        name=alumni.name, 
        campus=alumni.campus,
        major=alumni.major,
        graduation_year=alumni.graduation_year,
        source_platforms=alumni.source_platforms
    )
    db.add(new_alumni)
    db.commit()
    db.refresh(new_alumni)
    return new_alumni

from typing import List, Optional


def build_status_counts(db: Session) -> dict[str, int]:
    counts = {
        "Semua": db.query(models.Alumni).count(),
        "Teridentifikasi": db.query(models.Alumni).filter(models.Alumni.status == "Teridentifikasi").count(),
        "Perlu Verifikasi Manual": db.query(models.Alumni).filter(models.Alumni.status == "Perlu Verifikasi Manual").count(),
        "Belum Ditemukan": db.query(models.Alumni).filter(models.Alumni.status.in_(["Belum Ditemukan", "Belum Dilacak", "Gagal"])).count(),
    }
    return counts

@app.get("/alumni/", response_model=schemas.PaginatedAlumniResponse)
def get_all_alumni(q: Optional[str] = None, status: Optional[str] = None, page: int = 1, limit: int = 20, db: Session = Depends(get_db), _: str = Depends(require_auth)):
    query = db.query(models.Alumni)
    if q:
        # Cari berdasarkan nama atau NIM
        from sqlalchemy import or_
        query = query.filter(or_(
            models.Alumni.name.ilike(f"%{q}%"),
            models.Alumni.nim.ilike(f"%{q}%")
        ))
        
    if status and status != 'Semua':
        if status == 'Belum Ditemukan':
            query = query.filter(models.Alumni.status.in_(['Belum Ditemukan', 'Belum Dilacak', 'Gagal']))
        else:
            query = query.filter(models.Alumni.status == status)
    
    # Sortir secara eksplisit agar baris tidak terpental/hilang dari halaman saat statusnya di-update!
    query = query.order_by(models.Alumni.id.asc())
    
    total = query.count()
    offset = (page - 1) * limit
    data = query.offset(offset).limit(limit).all()
    
    return {
        "data": data,
        "total": total,
        "page": page,
        "limit": limit,
        "status_counts": build_status_counts(db),
    }

@app.post("/alumni/{alumni_id}/track")
def trigger_tracking(alumni_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _: str = Depends(require_auth)):
    alumni = db.query(models.Alumni).filter(models.Alumni.id == alumni_id).first()
    if not alumni:
        raise HTTPException(status_code=404, detail="Alumni not found")
    
    # Change status to Tracking
    alumni.status = "Sedang Dilacak..."
    db.commit()

    # Add the scraping job to background tasks
    # JANGAN teruskan 'db' karena akan ditutup oleh FastAPI sesaat setelah return
    background_tasks.add_task(mock_scraping_task, alumni_id)
    
    return {"message": f"Tracking job started for {alumni.name}"}

@app.get("/alumni/{alumni_id}/results", response_model=List[schemas.TrackingResultResponse])
def get_tracking_results(alumni_id: int, db: Session = Depends(get_db), _: str = Depends(require_auth)):
    return db.query(models.TrackingResult).filter(models.TrackingResult.alumni_id == alumni_id).all()

@app.put("/alumni/{alumni_id}/verify")
def manual_verify(alumni_id: int, payload: dict, db: Session = Depends(get_db), _: str = Depends(require_auth)):
    alumni = db.query(models.Alumni).filter(models.Alumni.id == alumni_id).first()
    if not alumni:
        raise HTTPException(status_code=404, detail="Alumni not found")
    
    if "status" in payload: alumni.status = payload["status"]
    if "notes" in payload: alumni.notes = payload["notes"]
    if "job" in payload: alumni.job = payload["job"]
    if "job_source" in payload: alumni.job_source = payload["job_source"]
    if "job_url" in payload: alumni.job_url = payload["job_url"]
    if "email" in payload: alumni.email = payload["email"]
    if "phone_number" in payload: alumni.phone_number = payload["phone_number"]
    if "linkedin_url" in payload: alumni.linkedin_url = payload["linkedin_url"]
    if "ig_url" in payload: alumni.ig_url = payload["ig_url"]
    if "fb_url" in payload: alumni.fb_url = payload["fb_url"]
    if "tiktok_url" in payload: alumni.tiktok_url = payload["tiktok_url"]
    if "company" in payload: alumni.company = payload["company"]
    if "company_address" in payload: alumni.company_address = payload["company_address"]
    if "position" in payload: alumni.position = payload["position"]
    if "job_type" in payload: alumni.job_type = payload["job_type"]
    if "company_social_url" in payload: alumni.company_social_url = payload["company_social_url"]
    
    db.commit()
    return {"message": "Status updated via manual verification"}

@app.delete("/alumni/{alumni_id}")
def delete_alumni(alumni_id: int, db: Session = Depends(get_db), _: str = Depends(require_auth)):
    alumni = db.query(models.Alumni).filter(models.Alumni.id == alumni_id).first()
    if not alumni:
        raise HTTPException(status_code=404, detail="Alumni not found")
    
    # Delete related tracking results first
    db.query(models.TrackingResult).filter(models.TrackingResult.alumni_id == alumni_id).delete()
    db.delete(alumni)
    db.commit()
    return {"message": f"Alumni {alumni.name} and related data deleted"}
