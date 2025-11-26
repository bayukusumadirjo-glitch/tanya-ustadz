import streamlit as st
import sqlite3
import os
from datetime import datetime
import urllib.parse

# ===================================
# DATABASE — FIX TOTAL UNTUK STREAMLIT CLOUD
# ===================================
DB_PATH = "/tmp/kajian_qna.db"

# Hapus database lama kalau ada (biar bersih total dari error kolom)
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

# Buat database baru dari nol
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# Tabel Kajian
c.execute('''CREATE TABLE kajian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                nama_ustadz TEXT,
                tanggal_kajian TEXT,
                tanggal_dibuat TEXT DEFAULT (datetime('now')),
                aktif INTEGER DEFAULT 0
             )''')

# Tabel Pertanyaan — PASTI ADA KOLOM 'isi'
c.execute('''CREATE TABLE pertanyaan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kajian_id INTEGER NOT NULL,
                nama_penanya TEXT NOT NULL,
                isi TEXT NOT NULL,
                tanggal TEXT DEFAULT (datetime('now')),
                approved INTEGER DEFAULT 0
             )''')

conn.commit()

# ===================================
# KONFIGURASI
# ===================================
PASS_OPERATOR = "operator123"   # GANTI KALAU MAU
PASS_USTADZ = "ustadz123"       # GANTI KALAU MAU
LINK_DEPLOY = "https://tanya-ustadz-dirj.streamlit.app"  # GANTI SETELAH DEPLOY

# ===================================
# FUNGSI BANTU
# ===================================
def get_kajian_aktif():
    c.execute("SELECT id, nama, nama_ustadz, tanggal_kajian FROM kajian WHERE aktif = 1")
    return c.fetchone()

def set_kajian_aktif(kajian_id):
    c.execute("UPDATE kajian SET aktif = 0")
    c.execute("UPDATE kajian SET aktif = 1 WHERE id = ?", (kajian_id,))
    conn.commit()

# ===================================
# MODE PENANYA (QR)
# ===================================
if st.query_params.get("penanya") == "yes":
    st.set_page_config(page_title="Tanya Ustadz", layout="centered")
    st.title("Tanya Ustadz")

    aktif = get_kajian_aktif()
    if not aktif:
        st.error("Maaf, belum ada kajian aktif.")
        st.stop()

    st.success(f"KAJIAN: {aktif[1]}")
    st.info(f"{aktif[2] or 'Ustadz'} • {aktif[3] or ''}")

    with st.form("form_tanya"):
        nama = st.text_input("Nama Anda *")
        pertanyaan = st.text_area("Pertanyaan Anda *", height=150)
        kirim = st.form_submit_button("Kirim Pertanyaan", type="primary")

        if kirim:
            if nama.strip() and pertanyaan.strip():
                c.execute("INSERT INTO pertanyaan (kajian_id, nama_penanya, isi) VALUES (?, ?, ?)",
                          (aktif[0], nama.strip(), pertanyaan.strip()))
                conn.commit()
                st.success("Pertanyaan berhasil dikirim! Menunggu moderasi.")
                st.balloons()
            else:
                st.error("Harap isi nama dan pertanyaan!")

    st.caption("KajianQNA – Aman, terfilter, rahasia terjaga")
    st.stop()

# ===================================
# DASHBOARD UTAMA
# ===================================
st.set_page_config(page_title="KajianQNA Dashboard", layout="wide")
st.title("KajianQNA – Sistem Tanya Jawab")

# Login tahan refresh
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None

# LOGIN
if not st.session_state.logged_in:
    st.markdown("### Login Dashboard")
    col1, col2 = st.columns([1, 3])
    with col1:
        role = st.selectbox("Role", ["Operator", "Ustadz"])
        pwd = st.text_input("Password", type="password")
        if st.button("Masuk", type="primary"):
            if role == "Operator" and pwd == PASS_OPERATOR:
                st.session_state.logged_in = True
                st.session_state.role = "Operator"
                st.rerun()
            elif role == "Ustadz" and pwd == PASS_USTADZ:
                st.session_state.logged_in = True
                st.session_state.role = "Ustadz"
                st.rerun()
            else:
                st.error("Password salah!")
    st.stop()

# INFO KAJIAN
aktif = get_kajian_aktif()
if aktif:
    st.success(f"KAJIAN AKTIF: {aktif[1]}")
    st.info(f"Ustadz: {aktif[2] or '-'} | Tanggal: {aktif[3] or '-'}")
else:
    st.warning("Belum ada kajian aktif")

# Tombol refresh manual
if st.button("Refresh Data Sekarang"):
    st.rerun()

# DASHBOARD USTADZ
if st.session_state.role == "Ustadz":
    st.header("Dashboard Ustadz")
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
                tgl = tgl.split('.')[0] if '.' in tgl else tgl
                with st.expander(f"{nama} • {tgl}"):
                    st.write(isi)

# DASHBOARD OPERATOR
elif st.session_state.role == "Operator":
    st.header("Dashboard Operator")
    tab1, tab2, tab3 = st.tabs(["Kelola Kajian", "Moderasi", "QR Tetap"])

    with tab1:
        with st.form("buat_kajian"):
            nama_k = st.text_input("Nama Kajian *")
            ustadz = st.text_input("Nama Ustadz")
            tgl = st.date_input("Tanggal", datetime.now())
            if st.form_submit_button("Buat Kajian"):
                if nama_k.strip():
                    c.execute("INSERT INTO kajian (nama, nama_ustadz, tanggal_kajian) VALUES (?, ?, ?)",
                              (nama_k.strip(), ustadz or None, str(tgl)))
                    conn.commit()
                    st.success("Kajian dibuat!")
                    st.rerun()

        st.markdown("---")
        c.execute("SELECT id, nama, nama_ustadz, tanggal_kajian, aktif FROM kajian ORDER BY tanggal_dibuat DESC")
        for row in c.fetchall():
            cols = st.columns([4, 2, 2, 2, 1])
            cols[0].write(f"**{row[1]}**")
            cols[1].write(row[2] or "-")
            cols[2].write(row[3] or "-")
            if row[4]:
                cols[3].success("AKTIF")
            else:
                if cols[3].button("Aktifkan", key=f"a{row[0]}"):
                    set_kajian_aktif(row[0])
                    st.rerun()
            if cols[4].button("Hapus", key=f"d{row[0]}"):
                c.execute("DELETE FROM pertanyaan WHERE kajian_id = ?", (row[0],))
                c.execute("DELETE FROM kajian WHERE id = ?", (row[0],))
                conn.commit()
                st.rerun()

    with tab2:
        if not aktif:
            st.info("Belum ada kajian aktif")
        else:
            c.execute("SELECT id, nama_penanya, isi, tanggal FROM pertanyaan WHERE kajian_id = ? AND approved = 0 ORDER BY tanggal DESC", (aktif[0],))
            waiting = c.fetchall()
            if not waiting:
                st.success("Semua sudah dimoderasi!")
            else:
                for p in waiting:
                    with st.container(border=True):
                        st.write(f"**{p[1]}** • {p[3].split('.')[0]}")
                        st.info(p[2])
                        c1, c2 = st.columns(2)
                        if c1.button("Approve", key=f"ok{p[0]}"):
                            c.execute("UPDATE pertanyaan SET approved = 1 WHERE id = ?", (p[0],))
                            conn.commit()
                            st.rerun()
                        if c2.button("Tolak", key=f"no{p[0]}"):
                            c.execute("DELETE FROM pertanyaan WHERE id = ?", (p[0],))
                            conn.commit()
                            st.rerun()

    with tab3:
        st.success("QR TETAP – PAKAI SELAMANYA!")
        link = f"{LINK_DEPLOY}?penanya=yes"
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={urllib.parse.quote(link)}"
        col1, col2 = st.columns(2)
        col1.image(qr, width=280)
        col2.code(link)

# SIDEBAR
with st.sidebar:
    st.write(f"**{st.session_state.role}**")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

st.sidebar.caption("KajianQNA • Stabil • Tanpa Auto Refresh")
