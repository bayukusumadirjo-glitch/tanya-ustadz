import streamlit as st
import sqlite3
import os
from datetime import datetime
import urllib.parse

# ===================================
# KONFIGURASI
# ===================================
PASS_OPERATOR = "operator123"   # GANTI SESUAI KEINGINAN
PASS_USTADZ = "ustadz123"       # GANTI SESUAI KEINGINAN

# GANTI INI SETELAH DEPLOY!
LINK_DEPLOY = "https://tanya-ustadz-dirj.streamlit.app"  # UBAH SETELAH DAPAT LINK PERMANEN

# ===================================
# DATABASE SETUP — KHUSUS STREAMLIT CLOUD (PAKAI /tmp/ BIAR BISA TULIS!)
# ===================================
DB_PATH = "/tmp/kajian_qna.db"  # /tmp writable di cloud

# Buat database baru jika belum ada (ini kunci: otomatis create tabel)
if not os.path.exists(DB_PATH):
    conn_init = sqlite3.connect(DB_PATH)
    c_init = conn_init.cursor()
    # Tabel Kajian
    c_init.execute('''CREATE TABLE kajian (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nama TEXT NOT NULL,
                        nama_ustadz TEXT,
                        tanggal_kajian TEXT,
                        tanggal_dibuat TEXT DEFAULT (datetime('now')),
                        aktif INTEGER DEFAULT 0
                     )''')
    # Tabel Pertanyaan
    c_init.execute('''CREATE TABLE pertanyaan (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        kajian_id INTEGER NOT NULL,
                        nama_penanya TEXT NOT NULL,
                        isi TEXT NOT NULL,
                        tanggal TEXT DEFAULT (datetime('now')),
                        approved INTEGER DEFAULT 0
                     )''')
    conn_init.commit()
    conn_init.close()
    st.info("Database dibuat baru di /tmp/ (normal di cloud)")

# Koneksi utama
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# Tambah kolom jika belum ada (aman)
for col in ["nama_ustadz", "tanggal_kajian"]:
    try:
        c.execute(f"ALTER TABLE kajian ADD COLUMN {col} TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Sudah ada

# ===================================
# FUNGSI BANTU
# ===================================
def get_kajian_aktif():
    c.execute("SELECT id, nama, nama_ustadz, tanggal_kajian FROM kajian WHERE aktif = 1")
    result = c.fetchone()
    return result  # None jika tidak ada

def set_kajian_aktif(kajian_id):
    c.execute("UPDATE kajian SET aktif = 0")  # Matikan semua
    c.execute("UPDATE kajian SET aktif = 1 WHERE id = ?", (kajian_id,))
    conn.commit()

# ===================================
# MODE PENANYA (dari QR) — INI YANG SUDAH DIPERBAIKI
# ===================================
query_params = st.query_params
if query_params.get("penanya") == "yes":
    st.set_page_config(page_title="Tanya Ustadz", layout="centered")
    st.title("📩 Tanya Ustadz")

    aktif = get_kajian_aktif()
    if not aktif:
        st.error("❌ Maaf, saat ini belum ada kajian aktif.")
        st.info("Hubungi operator untuk mengaktifkan kajian.")
        st.stop()

    # Tampilkan info kajian
    col1, col2 = st.columns([3, 2])
    col1.success(f"**KAJIAN AKTIF:** {aktif[1]}")
    col2.info(f"**Ustadz:** {aktif[2] or 'Belum ditentukan'} • **Tanggal:** {aktif[3] or 'Belum ditentukan'}")

    # Form pertanyaan
    with st.form("form_pertanyaan"):
        nama = st.text_input("Nama Anda *", placeholder="Wajib diisi")
        pertanyaan = st.text_area("Pertanyaan Anda *", height=150, placeholder="Tuliskan pertanyaan Anda di sini...")
        kirim = st.form_submit_button("Kirim Pertanyaan", type="primary")

        if kirim:
            if not nama.strip() or not pertanyaan.strip():
                st.error("Nama dan pertanyaan wajib diisi!")
            else:
                try:
                    # INSERT YANG SUDAH DIPERBAIKI — FORMAT SQL BENAR, TANPA NEWLINE MASALAH
                    c.execute("INSERT INTO pertanyaan (kajian_id, nama_penanya, isi) VALUES (?, ?, ?)",
                              (aktif[0], nama.strip(), pertanyaan.strip()))
                    conn.commit()
                    st.success("✅ Pertanyaan berhasil dikirim! Menunggu moderasi operator.")
                    st.balloons()
                    st.rerun()  # Refresh untuk kosongkan form
                except sqlite3.OperationalError as e:
                    st.error(f"Database error: {str(e)} (Cek log app untuk detail)")
                except Exception as e:
                    st.error("Gagal mengirim. Coba lagi nanti.")
                    st.caption(f"Detail error: {str(e)}")  # Untuk debug, hapus nanti

    st.caption("KajianQNA – Rahasia terjaga, pertanyaan terfilter")
    st.stop()

# ===================================
# DASHBOARD UTAMA (Operator & Ustadz)
# ===================================
st.set_page_config(page_title="KajianQNA Dashboard", layout="wide")
st.title("🕌 KajianQNA – Sistem Tanya Jawab Ustadz")

# Session state untuk login (tahan refresh)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None

# ===================================
# LOGIN
# ===================================
if not st.session_state.logged_in:
    st.markdown("### 🔐 Login Dashboard")
    col1, _ = st.columns([1, 2])
    with col1:
        role = st.selectbox("Pilih Role", ["Operator", "Ustadz"])
        pwd = st.text_input("Password", type="password")
        if st.button("Masuk", type="primary", use_container_width=True):
            if role == "Operator" and pwd == PASS_OPERATOR:
                st.session_state.logged_in = True
                st.session_state.role = "Operator"
                st.success("Login Operator berhasil!")
                st.rerun()
            elif role == "Ustadz" and pwd == PASS_USTADZ:
                st.session_state.logged_in = True
                st.session_state.role = "Ustadz"
                st.success("Login Ustadz berhasil!")
                st.rerun()
            else:
                st.error("Password salah!")
    st.stop()

# ===================================
# INFO KAJIAN AKTIF
# ===================================
aktif = get_kajian_aktif()
if aktif:
    st.success(f"**KAJIAN AKTIF:** {aktif[1]}")
    st.info(f"Ustadz: {aktif[2] or '-'} | Tanggal: {aktif[3] or '-'}")
else:
    st.warning("⚠️ Belum ada kajian aktif")

# Tombol Refresh Manual
if st.button("🔄 Refresh Data", type="secondary"):
    st.rerun()

# ===================================
# DASHBOARD USTADZ
# ===================================
if st.session_state.role == "Ustadz":
    st.header("👳 Dashboard Ustadz")
    if not aktif:
        st.info("Belum ada kajian aktif.")
    else:
        st.subheader(f"Pertanyaan untuk: {aktif[1]}")
        c.execute("SELECT nama_penanya, isi, tanggal FROM pertanyaan WHERE kajian_id = ? AND approved = 1 ORDER BY tanggal DESC", (aktif[0],))
        rows = c.fetchall()
        if not rows:
            st.info("Belum ada pertanyaan yang di-approve.")
        else:
            for nama, isi, tgl in rows:
                tgl_display = tgl.split('.')[0] if '.' in tgl else tgl
                with st.expander(f"👤 {nama} • {tgl_display}"):
                    st.markdown(f"**{isi}**")

# ===================================
# DASHBOARD OPERATOR
# ===================================
elif st.session_state.role == "Operator":
    st.header("🛠️ Dashboard Operator")
    tab1, tab2, tab3 = st.tabs(["Kelola Kajian", "Moderasi Pertanyaan", "QR Code Tetap"])

    with tab1:
        st.subheader("📝 Buat Kajian Baru")
        with st.form("new_kajian"):
            nama = st.text_input("Nama Kajian *")
            ustadz = st.text_input("Nama Ustadz")
            tgl = st.date_input("Tanggal Kajian", datetime.now())
            if st.form_submit_button("Buat Kajian", type="primary"):
                if nama.strip():
                    c.execute("INSERT INTO kajian (nama, nama_ustadz, tanggal_kajian) VALUES (?, ?, ?)",
                              (nama.strip(), ustadz or None, str(tgl)))
                    conn.commit()
                    st.success("Kajian berhasil dibuat!")
                    st.rerun()
                else:
                    st.error("Nama kajian wajib diisi!")

        st.markdown("---")
        st.subheader("📋 Daftar Kajian")
        c.execute("SELECT id, nama, nama_ustadz, tanggal_kajian, aktif FROM kajian ORDER BY tanggal_dibuat DESC")
        kajians = c.fetchall()
        if not kajians:
            st.info("Belum ada kajian.")
        else:
            for row in kajians:
                c1, c2, c3, c4, c5 = st.columns([4, 2, 2, 2, 1])
                c1.write(f"**{row[1]}**")
                c2.write(row[2] or "-")
                c3.write(row[3] or "-")
                if row[4] == 1:
                    c4.success("✅ AKTIF")
                else:
                    if c4.button("Aktifkan", key=f"aktif_{row[0]}"):
                        set_kajian_aktif(row[0])
                        st.rerun()
                if c5.button("🗑️ Hapus", key=f"del_{row[0]}", type="secondary"):
                    c.execute("DELETE FROM pertanyaan WHERE kajian_id = ?", (row[0],))
                    c.execute("DELETE FROM kajian WHERE id = ?", (row[0],))
                    conn.commit()
                    st.rerun()

    with tab2:
        st.subheader("🔍 Moderasi Pertanyaan")
        if not aktif:
            st.info("Belum ada kajian aktif.")
        else:
            c.execute("SELECT id, nama_penanya, isi, tanggal FROM pertanyaan WHERE kajian_id = ? AND approved = 0 ORDER BY tanggal DESC", (aktif[0],))
            waiting = c.fetchall()
            if not waiting:
                st.success("Semua pertanyaan sudah dimoderasi!")
            else:
                for p in waiting:
                    tgl = p[3].split('.')[0] if '.' in p[3] else p[3]
                    with st.container(border=True):
                        st.write(f"**{p[1]}** • {tgl}")
                        st.info(p[2])
                        col1, col2 = st.columns(2)
                        if col1.button("✅ Approve", key=f"ok_{p[0]}"):
                            c.execute("UPDATE pertanyaan SET approved = 1 WHERE id = ?", (p[0],))
                            conn.commit()
                            st.rerun()
                        if col2.button("❌ Tolak", key=f"no_{p[0]}", type="secondary"):
                            c.execute("DELETE FROM pertanyaan WHERE id = ?", (p[0],))
                            conn.commit()
                            st.rerun()
                    st.markdown("---")

    with tab3:
        st.success("🖼️ QR CODE TETAP – CETAK SEKALI, PAKAI SELAMANYA!")
        qr_link = f"{LINK_DEPLOY}?penanya=yes"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=600x600&data={urllib.parse.quote(qr_link)}"
        col1, col2 = st.columns(2)
        col1.image(qr_url, width=300, caption="Scan QR ini untuk mode penanya")
        col2.code(qr_link)
        st.info("**Tips:** Cetak & tempel di masjid. QR otomatis ikut kajian aktif!")

# ===================================
# SIDEBAR & LOGOUT
# ===================================
with st.sidebar:
    if st.session_state.logged_in:
        st.success(f"Login sebagai: **{st.session_state.role}**")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

st.sidebar.caption("KajianQNA v5.0 – Stabil di Streamlit Cloud!")
