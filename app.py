import streamlit as st
import sqlite3
import os
from datetime import datetime
import urllib.parse

# ===================================
# DATABASE — FIX TOTAL: HAPUS LAMA, BUAT BARU!
# ===================================
DB_PATH = "/tmp/kajian_qna.db"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE kajian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                nama_ustadz TEXT,
                tanggal_kajian TEXT,
                tanggal_dibuat TEXT DEFAULT (datetime('now')),
                aktif INTEGER DEFAULT 0
             )''')

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
# FUNGSI
# ===================================
def get_kajian_aktif():
    c.execute("SELECT id, nama, nama_ustadz, tanggal_kajian FROM kajian WHERE aktif = 1")
    return c.fetchone()

# ===================================
# MODE PENANYA
# ===================================
if st.query_params.get("penanya") == "yes":
    st.set_page_config(page_title="Tanya Ustadz", layout="centered")
    st.title("Tanya Ustadz")

    aktif = get_kajian_aktif()
    if not aktif:
        st.error("Belum ada kajian aktif!")
        st.stop()

    st.success(f"KAJIAN: {aktif[1]}")
    st.info(f"{aktif[2] or 'Ustadz'} • {aktif[3] or ''}")

    with st.form("form"):
        nama = st.text_input("Nama Anda *")
        pertanyaan = st.text_area("Pertanyaan Anda *", height=150)
        if st.form_submit_button("Kirim", type="primary"):
            if nama.strip() and pertanyaan.strip():
                c.execute("INSERT INTO pertanyaan (kajian_id, nama_penanya, isi) VALUES (?, ?, ?)",
                          (aktif[0], nama.strip(), pertanyaan.strip()))
                conn.commit()
                st.success("Berhasil dikirim!")
                st.balloons()
                st.rerun()
            else:
                st.error("Isi semua!")

    st.stop()

# ===================================
# DASHBOARD (login, operator, ustadz)
# ===================================
st.set_page_config(page_title="Dashboard", layout="wide")
st.title("KajianQNA")

# Login sementara
if st.sidebar.text_input("Password", type="password") != "admin123":
    st.sidebar.error("Password salah!")
    st.stop()
else:
    st.sidebar.success("Login berhasil")

aktif = get_kajian_aktif()
if aktif:
    st.success(f"AKTIF: {aktif[1]}")

# Moderasi
if aktif:
    c.execute("SELECT id, nama_penanya, isi FROM pertanyaan WHERE kajian_id = ? AND approved = 0", (aktif[0],))
    for row in c.fetchall():
        with st.expander(f"{row[1]}"):
            st.write(row[2])
            if st.button("Approve", key=row[0]):
                c.execute("UPDATE pertanyaan SET approved = 1 WHERE id = ?", (row[0],))
                conn.commit()
                st.rerun()
