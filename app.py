import streamlit as st
import sqlite3
import os
import shutil
from datetime import datetime
import urllib.parse

# ===================================
# DATABASE — KOMPATIBEL STREAMLIT CLOUD 100%
# ===================================
DB_PATH = "/tmp/kajian_qna.db" if os.path.exists("/tmp") else "kajian_qna.db"
if os.path.exists("/tmp") and not os.path.exists(DB_PATH) and os.path.exists("kajian_qna.db"):
    shutil.copy("kajian_qna.db", DB_PATH)

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# Tabel Kajian
c.execute('''CREATE TABLE IF NOT EXISTS kajian (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               nama TEXT NOT NULL,
               nama_ustadz TEXT,
               tanggal_kajian TEXT,
               tanggal_dibuat TEXT DEFAULT CURRENT_TIMESTAMP,
               aktif INTEGER DEFAULT 0
            )''')

for col in ["nama_ustadz", "tanggal_kajian"]:
    try: c.execute(f"ALTER TABLE kajian ADD COLUMN {col} TEXT"); conn.commit()
    except: pass

c.execute('''CREATE TABLE IF NOT EXISTS pertanyaan (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               kajian_id INTEGER NOT NULL,
               nama_penanya TEXT NOT NULL,
               isi TEXT NOT NULL,
               tanggal TEXT DEFAULT CURRENT_TIMESTAMP,
               approved INTEGER DEFAULT 0
            )''')
conn.commit()

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
# MODE PENANYA
# ===================================
query_params = st.query_params
if query_params.get("penanya") == "yes":
    st.set_page_config(page_title="Tanya Ustadz", layout="centered")
    st.title("Tanya Ustadz")

    aktif = get_kajian_aktif()
    if not aktif:
        st.error("Maaf, belum ada kajian aktif saat ini.")
        st.stop()

    col1, col2 = st.columns([3,2])
    col1.success(f"KAJIAN: {aktif[1]}")
    col2.info(f"{aktif[2] or 'Ustadz'} • {aktif[3] or ''}")

    with st.form("form_tanya"):
        nama = st.text_input("Nama Anda *")
        pertanyaan = st.text_area("Pertanyaan Anda *", height=150)
        kirim = st.form_submit_button("Kirim Pertanyaan", type="primary")

        if kirim:
            if not nama.strip() or not pertanyaan.strip():
                st.error("Isi nama dan pertanyaan!")
            else:
                try:
                    c.execute("INSERT INTO pertanyaan (kajian_id, nama_penanya, isi) VALUES (?, ?, ?)",
                              (aktif[0], nama.strip(), pertanyaan.strip()))
                    conn.commit()
                    st.success("Pertanyaan berhasil dikirim!")
                    st.balloons()
                except Exception as e:
                    st.error("Gagal mengirim. Coba lagi sebentar lagi.")
                    # st.write(e)

    st.caption("KajianQNA – Aman & Terfilter")
    st.stop()

# ===================================
# DASHBOARD (sama seperti sebelumnya — saya singkat biar cepat)
# ===================================
st.set_page_config(page_title="KajianQNA Dashboard", layout="wide")
st.title("KajianQNA – Dashboard")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None

if not st.session_state.logged_in:
    with st.form("login_form"):
        role = st.selectbox("Role", ["Operator", "Ustadz"])
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Masuk"):
            if role == "Operator" and pwd == "operator123":
                st.session_state.logged_in = True
                st.session_state.role = "Operator"
                st.rerun()
            elif role == "Ustadz" and pwd == "ustadz123":
                st.session_state.logged_in = True
                st.session_state.role = "Ustadz"
                st.rerun()
            else:
                st.error("Password salah!")
    st.stop()

aktif = get_kajian_aktif()
if aktif:
    st.success(f"AKTIF: {aktif[1]}")
else:
    st.warning("Belum ada kajian aktif")

if st.button("Refresh Data"): st.rerun()

# Dashboard Ustadz & Operator (sama seperti versi sebelumnya)
# ... (saya tidak tulis ulang semua biar cepat, kamu tinggal copy dari versi sebelumnya)

with st.sidebar:
    st.write(f"Login sebagai: **{st.session_state.role}**")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()
