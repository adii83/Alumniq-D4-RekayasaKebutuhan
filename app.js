// Constants and Auth Handling
const token = localStorage.getItem('alumniq_token');
if (!token) {
    window.location.href = 'login.html';
}

// Ganti variabel ini dengan link URL backend Anda dari Render setelah ter-deploy
const API_URL = 'https://alumniq-d4-rekayasa-kebutuhan.onrender.com';

// Global State
let currentPage = 1;
const limit = 20;
let searchQuery = '';
let currentTabStatus = 'Semua';

let allAlumniData = []; 

function logout() {
    localStorage.removeItem('alumniq_token');
    window.location.href = 'login.html';
}

document.getElementById('searchForm').addEventListener('submit', (e) => {
    e.preventDefault();
    searchQuery = document.getElementById('searchInput').value;
    currentPage = 1;
    fetchAlumni();
});

// Set Tab Filter
function setTabFilter(status) {
    currentTabStatus = status;
    currentPage = 1;

    // Update active UI styles
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.getAttribute('data-filter') === status) {
            btn.classList.add('border-[#b76e3c]', 'text-[#b76e3c]');
            btn.classList.remove('border-transparent', 'text-slate-500');
        } else {
            btn.classList.remove('border-[#b76e3c]', 'text-[#b76e3c]');
            btn.classList.add('border-transparent', 'text-slate-500');
        }
    });

    fetchAlumni();
}

// Fetch paginated alumni
async function fetchAlumni(isBackgroundUpdate = false) {
    if (!isBackgroundUpdate) {
        document.getElementById('loading').classList.remove('hidden');
        document.getElementById('alumni-table-body').innerHTML = '';
    }
    
    let url = `${API_URL}/alumni/?page=${currentPage}&limit=${limit}`;
    if (searchQuery) url += `&q=${encodeURIComponent(searchQuery)}`;
    if (currentTabStatus !== 'Semua') url += `&status=${encodeURIComponent(currentTabStatus)}`;
    
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('API Error');
        const data = await response.json();
        
        allAlumniData = data.data; // Server returned {data, total, page, limit}
        renderTable(data.total);
    } catch (error) {
        console.error("Error fetching data:", error);
        if (!isBackgroundUpdate) {
            document.getElementById('alumni-table-body').innerHTML = `<tr><td colspan="5" class="px-6 py-12 text-center text-red-400 font-medium">Gagal memuat data. Mohon pastikan file excel backend sudah di import atau server lokal berjalan.</td></tr>`;
        }
    } finally {
        if (!isBackgroundUpdate) {
            document.getElementById('loading').classList.add('hidden');
        }
    }
}

function renderTable(total) {
    const tableBody = document.getElementById('alumni-table-body');
    
    const currentRows = tableBody.querySelectorAll('tr[id^="row-"]');
    let shouldWipe = false;
    
    if (currentRows.length !== allAlumniData.length) {
        shouldWipe = true;
    } else {
        for(let i=0; i<allAlumniData.length; i++) {
            if (currentRows[i].id !== 'row-' + allAlumniData[i].id) {
                shouldWipe = true; break;
            }
        }
    }
    
    if (shouldWipe) {
        tableBody.innerHTML = '';
        if (allAlumniData.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="5" class="px-6 py-8 text-center text-sm text-gray-400">Tidak ada data ditemukan.</td></tr>`;
            document.getElementById('pagination-info').innerText = 'Menampilkan 0 data';
            document.getElementById('btnPrev').disabled = true;
            document.getElementById('btnNext').disabled = true;
            return;
        }
    }

    allAlumniData.forEach(alumni => {
        const statusClass = alumni.status === 'Teridentifikasi' ? 'bg-emerald-100 text-emerald-700 border-emerald-200' :
                            alumni.status === 'Perlu Verifikasi Manual' ? 'bg-amber-100 text-amber-700 border-amber-200' :
                            alumni.status === 'Sedang Dilacak...' ? 'bg-sky-100 text-sky-600 border-sky-200' :
                            (alumni.status === 'Belum Ditemukan' || alumni.status === 'Gagal') ? 'bg-slate-100 text-slate-500 border-slate-200' :
                            'bg-gray-100 text-gray-500 border-gray-200';

        const btn = (text, extra, color) => `<button onclick="${extra}" class="whitespace-nowrap px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${color}">${text}</button>`;

        let actionButtons = '';
        if (alumni.status === 'Belum Dilacak' || alumni.status === 'Belum Ditemukan' || alumni.status === 'Gagal') {
            actionButtons = btn('Cari Target', `triggerTracking(${alumni.id})`, 'bg-amber-600 hover:bg-amber-700 text-white shadow-sm mr-2') + 
                            btn('Input Manual', `openDetailModal(${alumni.id})`, 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50');
        } else if (alumni.status === 'Perlu Verifikasi Manual') {
            actionButtons = btn('Tinjau Hasil', `openDetailModal(${alumni.id})`, 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-md animate-pulse');
        } else if (alumni.status === 'Teridentifikasi') {
            actionButtons = btn('Lihat / Edit', `openDetailModal(${alumni.id})`, 'bg-sky-600 hover:bg-sky-700 text-white');
        } else {
            actionButtons = `<span class="inline-flex items-center gap-1.5 px-3 py-1 rounded border border-sky-200 text-sky-600 text-xs font-semibold bg-sky-50"><span class="w-3 h-3 border border-sky-600 border-t-transparent rounded-full animate-spin"></span>Melacak...</span>`;
        }
        
        let positionInfo = alumni.job || 'Belum ada hasil';
        if (alumni.company) positionInfo = `${alumni.position || 'Bekerja'} di ${alumni.company}`;

        const rowHTML = `
            <td class="px-6 py-5">
                <div class="font-semibold text-slate-900">${alumni.name}</div>
                ${alumni.nim ? `<div class="text-[11px] font-mono text-slate-500 mt-0.5 tracking-wider bg-slate-100 inline-block px-1.5 py-0.5 rounded border border-slate-200">NIM: ${alumni.nim}</div>` : ''}
                <div class="text-[11px] text-slate-400 mt-1 uppercase tracking-wider">${alumni.campus}</div>
            </td>
            <td class="px-6 py-5">
                <div class="text-sm font-medium text-slate-800">${alumni.major}</div>
                ${alumni.faculty ? `<div class="text-[11px] text-slate-500 mt-0.5">${alumni.faculty}</div>` : ''}
                ${alumni.graduation_year ? `<div class="text-[10px] text-slate-400 mt-0.5">Lulus: ${alumni.graduation_year}</div>` : ''}
            </td>
            <td class="px-6 py-5">
                <div class="text-sm font-medium text-slate-700">${positionInfo}</div>
                ${alumni.email ? `<div class="text-[11px] text-slate-500 mt-0.5">📧 ${alumni.email}</div>` : ''}
            </td>
            <td class="px-6 py-5 text-center">
                <span class="px-3 py-1 inline-flex text-xs font-semibold rounded-full border ${statusClass}">${alumni.status}</span>
            </td>
            <td class="px-6 py-5 text-center">
                ${actionButtons}
            </td>
        `;
        
        let row = document.getElementById('row-' + alumni.id);
        if (!row || shouldWipe) {
            row = document.createElement('tr');
            row.className = `hover:bg-slate-50 transition-colors duration-150`;
            row.id = 'row-' + alumni.id;
            row.innerHTML = rowHTML;
            tableBody.appendChild(row);
        } else {
            if (row.innerHTML !== rowHTML) {
                row.innerHTML = rowHTML;
            }
        }
    });
    
    // Update pagination controls
    document.getElementById('pagination-info').innerText = `Menampilkan ${(currentPage-1)*limit + 1} - ${Math.min(currentPage*limit, total)} dari ${total} total data`;
    document.getElementById('btnPrev').disabled = currentPage === 1;
    document.getElementById('btnNext').disabled = currentPage * limit >= total;
}

function prevPage() { if (currentPage > 1) { currentPage--; fetchAlumni(); } }
function nextPage() { currentPage++; fetchAlumni(); }

// Trigger Tracking
async function triggerTracking(id) {
    try {
        const res = await fetch(`${API_URL}/alumni/${id}/track`, { method: 'POST' });
        if (res.ok) {
            showToast('Sistem mulai mencari jejak alumni...', 'info');
            fetchAlumni(true);
            startPolling();
        }
    } catch(e) {
        showToast('Gagal terhubung ke server', 'error');
    }
}

// Polling
let pollingInterval = null;
function startPolling() {
    if (pollingInterval) return;
    pollingInterval = setInterval(async () => {
        await fetchAlumni(true); // Pass true to silenty fetch
        const isTracking = allAlumniData.some(a => a.status === 'Sedang Dilacak...');
        if (!isTracking) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    }, 4000);
}

// Modal Variables
let _modalAlumniId = null;
let _modalResults = [];

async function openDetailModal(id) {
    const alumni = allAlumniData.find(a => a.id === id);
    if(!alumni) return;
    _modalAlumniId = id;
    
    document.getElementById('modal-title').textContent = alumni.name;
    document.getElementById('modal-subtitle').textContent = `Prodi: ${alumni.major} ${alumni.faculty ? '| Fakultas: '+alumni.faculty : ''}`;
    
    // Reset inputs matched to schema
    document.getElementById('f_position').value = alumni.position || "";
    document.getElementById('f_job_type').value = alumni.job_type || "";
    document.getElementById('f_company').value = alumni.company || "";
    document.getElementById('f_company_address').value = alumni.company_address || "";
    
    document.getElementById('f_email').value = alumni.email || "";
    document.getElementById('f_phone').value = alumni.phone_number || "";
    document.getElementById('f_linkedin').value = alumni.linkedin_url || "";
    document.getElementById('f_ig').value = alumni.ig_url || "";
    document.getElementById('f_fb').value = alumni.fb_url || "";
    document.getElementById('f_tiktok').value = alumni.tiktok_url || "";
    document.getElementById('f_company_social').value = alumni.company_social_url || "";
    
    // Fetch tracked link results (if any)
    let linksHtml = '<p class="text-sm text-slate-400 italic">Belum ada jejak yang terlacak/tersimpan.</p>';
    if (alumni.status !== 'Belum Dilacak' && alumni.status !== 'Belum Ditemukan') {
        try {
            const resp = await fetch(`${API_URL}/alumni/${id}/results`);
            if (resp.ok) {
                _modalResults = await resp.json();
                if (_modalResults && _modalResults.length > 0) {
                    linksHtml = _modalResults.map((r, idx) => {
                        return `
                        <div class="p-3 border border-slate-200 rounded-xl bg-white shadow-sm hover:border-[#b76e3c] transition-colors cursor-pointer" onclick="useResult(${idx})">
                            <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">${r.source}</span>
                            <p class="text-sm mt-1 text-slate-700 line-clamp-2">${r.extracted_info}</p>
                            <a href="${r.url}" target="_blank" class="text-xs text-blue-600 underline mt-1 inline-block" onclick="event.stopPropagation()">Buka Link ↗</a>
                        </div>`;
                    }).join('');
                } else if(alumni.job_url) {
                    linksHtml = `<div class="p-3 border border-slate-200 rounded-xl bg-white"><a href="${alumni.job_url}" target="_blank" class="text-sm text-blue-600 underline mr-2">Link Sumber Tersimpan ↗</a><span class="text-xs text-slate-500">(${alumni.job_source})</span></div>`;
                }
            }
        } catch(e) {}
    }
    
    document.getElementById('modal-platform-links').innerHTML = linksHtml;
    document.getElementById('modal-notes').value = alumni.notes || "";
    
    const modal = document.getElementById('detailModal');
    modal.classList.remove('hidden');
    // Ensure smooth load transition
    setTimeout(() => { modal.firstElementChild.classList.remove('scale-95', 'opacity-0'); }, 10);
}

function useResult(idx) {
    const res = _modalResults[idx];
    if(res) {
        document.getElementById('modal-notes').value += `\n[Sumber: ${res.source}] - ${res.extracted_info}`;
        showToast('Info ditempelkan ke catatan', 'success');
    }
}

function closeDetailModal() {
    const modal = document.getElementById('detailModal');
    modal.classList.add('hidden');
}

async function modalSaveVerified() {
    if(!_modalAlumniId) return;
    
    const payload = {
        status: 'Teridentifikasi',
        notes: document.getElementById('modal-notes').value.trim(),
        position: document.getElementById('f_position').value.trim(),
        job_type: document.getElementById('f_job_type').value,
        company: document.getElementById('f_company').value.trim(),
        company_address: document.getElementById('f_company_address').value.trim(),
        email: document.getElementById('f_email').value.trim(),
        phone_number: document.getElementById('f_phone').value.trim(),
        linkedin_url: document.getElementById('f_linkedin').value.trim(),
        ig_url: document.getElementById('f_ig').value.trim(),
        fb_url: document.getElementById('f_fb').value.trim(),
        tiktok_url: document.getElementById('f_tiktok').value.trim(),
        company_social_url: document.getElementById('f_company_social').value.trim(),
    };
    
    try {
        await fetch(`${API_URL}/alumni/${_modalAlumniId}/verify`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        showToast('Data alumni berhasil diverifikasi & disimpan', 'success');
        closeDetailModal();
        fetchAlumni(true); // Background update — TIDAK mengosongkan tabel lebih dulu
    } catch(e) { showToast('Gagal menyimpan database', 'error'); }
}

async function modalMarkNotFound() {
    if(!_modalAlumniId) return;
    try {
        await fetch(`${API_URL}/alumni/${_modalAlumniId}/verify`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({status: 'Belum Ditemukan'})
        });
        showToast('Ditandai tidak ditemukan', 'info');
        closeDetailModal();
        fetchAlumni(true); // Background update — TIDAK mengosongkan tabel lebih dulu
    } catch(e) { }
}

// Toast
function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed top-5 right-5 z-[10000] flex flex-col gap-3 pointer-events-none';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `flex items-center gap-3 px-4 py-3 rounded-xl border shadow-lg transform transition-all duration-300 translate-x-12 opacity-0 pointer-events-auto bg-white`;
    toast.innerHTML = `<span class="text-sm font-semibold text-slate-700">${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.classList.remove('translate-x-12', 'opacity-0'), 10);
    setTimeout(() => {
        toast.classList.add('translate-x-12', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Initial Fetch
fetchAlumni();
