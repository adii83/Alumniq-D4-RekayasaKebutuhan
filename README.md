# 🎓 AlumniQ — Intelligent Alumni Tracking System

<div align="center">

![AlumniQ Banner](https://img.shields.io/badge/AlumniQ-Sistem%20Pelacak%20Alumni-orange?style=for-the-badge&logo=graduation-cap)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square&logo=fastapi)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey?style=flat-square&logo=sqlite)
![Playwright](https://img.shields.io/badge/Scraper-Playwright-purple?style=flat-square&logo=playwright)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

**Sistem pelacak alumni berbasis web dengan kecerdasan buatan scraping otomatis**  
*Tugas Daily Project 4 — Rekayasa Kebutuhan (Semester 6)*

</div>

---

## 📋 Deskripsi Proyek

**AlumniQ** adalah sistem informasi berbasis web yang dirancang untuk membantu **Program Studi Teknik Informatika, Universitas Muhammadiyah Malang** dalam melacak dan memverifikasi data karier alumni secara efisien. Sistem ini mengintegrasikan pencarian data otomatis dari internet dengan alur verifikasi manual oleh operator.

### ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 🔐 **Autentikasi Aman** | Sistem login dengan proteksi token untuk akses operator |
| 📊 **Import Data Excel** | Muat massal data alumni dari berkas `.xlsx` (mendukung 140.000+ baris) |
| 🔍 **Pencarian Canggih** | Cari alumni berdasarkan **Nama** atau **NIM** secara real-time |
| 🤖 **Pelacak AI Otomatis** | Scraper berbasis Playwright (Headless Chromium) yang menelusuri Yahoo Search |
| 🗂️ **Filter Status** | Navigasi tab berdasarkan status: Semua / Teridentifikasi / Perlu Verifikasi / Belum Ditemukan |
| ✅ **Verifikasi Manual** | Form input lengkap untuk data pekerjaan & media sosial alumni |
| 📄 **Paginasi Cepat** | Navigasi halaman tanpa reload penuh dengan smart DOM update |

---

## 🛠️ Tech Stack

### Backend
- **Python 3.10+** — bahasa utama
- **FastAPI** — framework REST API modern dan cepat
- **SQLAlchemy** — ORM untuk operasi database
- **SQLite** — database lokal ringan
- **Playwright** — headless browser untuk scraping anti-deteksi bot
- **Pandas** — pemrosesan dan parsing data Excel

### Frontend
- **HTML5 + Vanilla JavaScript** — tanpa framework tambahan
- **Tailwind CSS (via CDN)** — styling modern dan responsif
- **Fetch API** — komunikasi asinkron dengan backend

---

## 🚀 Instalasi & Menjalankan Secara Lokal

### Prasyarat
- Python 3.10 atau lebih baru
- pip (package manager Python)

### Langkah 1: Clone Repository
```bash
git clone https://github.com/USERNAME/REPO_NAME.git
cd REPO_NAME
```

### Langkah 2: Install Dependensi Python
```bash
cd backend
pip install -r requirements.txt
```

### Langkah 3: Install Browser Playwright
```bash
python -m playwright install chromium
```

### Langkah 4: Import Data Alumni dari Excel
> ⚠️ Pastikan berkas `Alumni 2000-2025.xlsx` berada di folder root proyek (satu level di atas `backend/`)
```bash
python import_excel.py
```
Proses ini akan memuat seluruh data alumni (~140.000+ baris) ke database SQLite secara otomatis dalam waktu sekitar 10-30 detik.

### Langkah 5: Jalankan Server Backend
```bash
uvicorn main:app --port 8000
```
Server akan berjalan di: `http://127.0.0.1:8000`

### Langkah 6: Buka Antarmuka Web
Buka `login.html` menggunakan browser Anda (klik kanan → Open with Browser, atau menggunakan ekstensi VS Code Live Server).

> ⚠️ **Catatan Penting:** Jika menggunakan VS Code Live Server, pastikan pengaturan berikut ditambahkan di `.vscode/settings.json` agar Live Server tidak me-refresh browser saat database berubah:
> ```json
> {
>     "liveServer.settings.ignoreFiles": [
>         "backend/**/*.db",
>         "backend/**/*.db-journal"
>     ]
> }
> ```

---

## 🔑 Kredensial Login

| Field | Nilai |
|-------|-------|
| Username | `slamethariyadi` |
| Password | `2023-221` |

---

## 📁 Struktur Proyek

```
Daily Project 4/
├── 📄 index.html              # Halaman utama dashboard alumni
├── 📄 login.html              # Halaman login
├── 📄 app.js                  # Logika frontend (fetch, render, state)
├── 📄 favicon.svg             # Ikon aplikasi
├── 📄 Alumni 2000-2025.xlsx   # Data sumber alumni (tidak di-commit)
│
├── 📁 backend/
│   ├── 📄 main.py             # API utama (FastAPI) + logika scraper
│   ├── 📄 models.py           # Definisi tabel database (SQLAlchemy)
│   ├── 📄 schemas.py          # Schema request/response (Pydantic)
│   ├── 📄 database.py         # Konfigurasi koneksi database
│   ├── 📄 import_excel.py     # Skrip impor data massal dari Excel
│   └── 📄 requirements.txt   # Daftar dependensi Python
│
├── 📁 .vscode/
│   └── 📄 settings.json       # Konfigurasi VS Code (Live Server ignore)
│
├── 📄 .gitignore              # File yang diabaikan Git
├── 📄 render.yaml             # Konfigurasi deployment Render.com
└── 📄 README.md               # Dokumentasi ini
```

---

## 🌐 API Endpoint

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `POST` | `/login` | Autentikasi dan mendapatkan token |
| `GET` | `/alumni/` | Ambil daftar alumni (dengan filter, search, paginasi) |
| `POST` | `/alumni/` | Tambah alumni baru |
| `POST` | `/alumni/{id}/track` | Mulai pelacakan otomatis untuk satu alumni |
| `GET` | `/alumni/{id}/results` | Ambil hasil pelacakan untuk satu alumni |
| `PUT` | `/alumni/{id}/verify` | Simpan data verifikasi manual |

---

## 📊 Alur Kerja Sistem

```
[Import Excel] → [Database SQLite] → [Dashboard Web]
                                           ↓
                              [Cari Target] → [Playwright Scraper]
                                           ↓
                              [Hasil Pencarian Yahoo]
                                           ↓
                              [Verifikasi Manual oleh Operator]
                                           ↓
                              [Status: Teridentifikasi ✅]
```

---

## ⚙️ Konfigurasi Deployment (Render.com)

Proyek ini sudah dilengkapi berkas `render.yaml` untuk kemudahan deployment di [Render.com](https://render.com).

> ⚠️ **Catatan Penting sebelum Deploy:**
> 1. Ganti URL API di `app.js` dan `login.html` dari `http://localhost:8000` ke URL Render Anda.
> 2. SQLite tidak cocok untuk produksi skala besar. Pertimbangkan migrasi ke **PostgreSQL** (tersedia gratis di Render) untuk deployment jangka panjang.
> 3. Playwright di Render memerlukan buildpack khusus — tambahkan Chromium ke environment.

---

## 👨‍💻 Informasi Pengembang

| Field | Detail |
|-------|--------|
| **Nama** | Slamet Hariyadi |
| **NIM** | 202310370311221 |
| **Mata Kuliah** | Rekayasa Kebutuhan — Kelas B |
| **Program Studi** | Teknik Informatika |
| **Universitas** | Universitas Muhammadiyah Malang |
| **Semester** | 6 (2024/2025) |

---

## 📝 Lisensi

Proyek ini dibuat untuk keperluan **tugas akademik** mata kuliah Rekayasa Kebutuhan.  
© 2025 Slamet Hariyadi — Universitas Muhammadiyah Malang.
