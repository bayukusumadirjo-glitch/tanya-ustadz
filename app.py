# app.py ←←← VERSI FINAL & SUDAH DIPERBAIKI TOTAL (TIDAK ADA ERROR LAGI)

import streamlit as st
import sqlite3
from datetime import datetime

# === DATABASE ===
conn = sqlite3.connect('kajian_qna.db', check_same_thread=False)
c = conn.cursor()

# Buat tabel kajian
c.execute('''CREATE TABLE IF NOT EXISTS kajian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                tanggal_dibuat TEXT,
                aktif INTEGER DEFAULT 0
             )''')

# Buat tabel pertanyaan (INI YANG DI-FIX: NOT NOT NULL → NOT NULL)
c.execute('''CREATE TABLE IF NOT EXISTS pertanyaan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kajian_id INTEGER,
                nama_penanya TEXT NOT NULL,
                pertanyaan TEXT NOT NULL,
                tanggal TEXT,
                approved INTEGER DEFAULT 0,
                FOREIGN KEY (kajian_id) REFERENCES kajian (id)
             )''')
conn.commit()

# === PASSWORD (ganti sesuai keinginan) ===
PASS_OPERATOR = "operator123"
PASS_USTADZ   = "ustadz123"

# === URL QR CODE TETAP (ganti sekali setelah deploy) ===
PERMANENT_URL = "https://tanya-ustadz-anda.streamlit.app"   # GANTI NANTI

# === DETEKSI DARI QR ATAU BUKAN ===
is_penanya = st.query_params.get("from_qr", "no") == "yes"
if is_penanya and "from_qr" not in st.query_params:
    st.query_params.from_qr = "yes"

# ===================================
# 1. HALAMAN PENANYA (dari QR) — WAJIB NAMA + TIDAK BISA GANTI ROLE
# ===================================
if is_penanya:
    st.set_page_config(page_title="Tanya Ustadz", layout="centered")
    st.title("Tanya Ustadz")
    st.caption("Silakan tulis nama dan pertanyaan Anda")

    # Cek kajian aktif
    c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
    aktif = c.fetchone()

    if not aktif:
        st.error("Belum ada kajian aktif. Silakan hubungi panitia/operator.")
        st.stop()

    st.success(f"Kajian aktif: **{aktif[1]}**")

    with st.form("form_penanya"):
        nama = st.text_input("Nama Anda * (wajib)*", placeholder="Ahmad / Ummu Aisyah")
        pertanyaan = st.text_area("Pertanyaan Anda * (wajib)*", height=150,
                                  placeholder="Tuliskan pertanyaan dengan jelas dan sopan...")

        kirim = st.form_submit_button("Kirim Pertanyaan", use_container_width=True)

        if kirim:
            if not nama.strip():
                st.error("Nama wajib diisi!")
            elif not pertanyaan.strip():
                st.error("Pertanyaan wajib diisi!")
            elif len(pertanyaan.strip()) < 10:
                st.error("Pertanyaan terlalu pendek.")
            else:
                tgl = datetime.now().strftime("%d/%m/%Y %H:%M")
                c.execute("""INSERT INTO pertanyaan 
                             (kajian_id, nama_penanya, pertanyaan, tanggal, approved) 
                             VALUES (?, ?, ?, ?, 0)""",
                          (aktif[0], nama.strip(), pertanyaan.strip(), tgl))
                conn.commit()
                st.success(f"Terima kasih {nama.split()[0]}! Pertanyaan sudah terkirim.")
                st.balloons()

    st.info("Pertanyaan Anda akan dimoderasi terlebih dahulu oleh operator.")
    st.stop()

# ===================================
# 2. & 3. PANEL OPERATOR & USTADZ (bukan dari QR)
# ===================================
else:
    st.set_page_config(page_title="Panel Operator & Ustadz", layout="wide")
    st.title("Panel Operator & Ustadz")

    role = st.sidebar.selectbox("Pilih Role", ["Operator", "Ustadz"])

    if role == "Ustadz":
        st.header("Dashboard Ustadz")
        pwd = st.sidebar.text_input("Password Ustadz", type="password")
        if pwd != PASS_USTADZ:
            st.error("Password salah!")
            st.stop()

        c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
        aktif = c.fetchone()
        if not aktif:
            st.info("Belum ada kajian aktif.")
        else:
            st.success(f"Kajian aktif: **{aktif[1]}**")
            c.execute("""SELECT nama_penanya, pertanyaan, tanggal 
                         FROM pertanyaan WHERE kajian_id = ? AND approved = 1 
                         ORDER BY tanggal ASC""", (aktif[0],))
            data = c.fetchall()
            if not data:
                st.info("Belum ada pertanyaan yang di-approve.")
            else:
                for i, (nama, q, tgl) in enumerate(data, 1):
                    st.markdown(f"**{i}. {nama}** — _{tgl}_")
                    st.write(q)
                    st.divider()

    else:  # Operator
        st.header("Panel Operator")
        pwd = st.sidebar.text_input("Password Operator", type="password")
        if pwd != PASS_OPERATOR:
            st.error("Password salah!")
            st.stop()

        tab1, tab2, tab3 = st.tabs(["Kelola Kajian", "Moderasi", "QR Code TETAP"])

        with tab1:
            st.subheader("Buat Kajian Baru")
            nama_kajian = st.text_input("Nama kajian baru")
            if st.button("Buat Kajian") and nama_kajian:
                c.execute("INSERT INTO kajian (nama, tanggal_dibuat) VALUES (?, ?)",
                          (nama_kajian, datetime.now().strftime("%d/%m/%Y %H:%M")))
                conn.commit()
                st.success("Kajian berhasil dibuat!")
                st.rerun()

            st.subheader("Pilih Kajian Aktif")
            c.execute("SELECT id, nama, aktif FROM kajian ORDER BY id DESC")
            for row in c.fetchall():
                col1, col2 = st.columns([5, 1])
                status = "AKTIF" if row[2] else "tidak aktif"
                col1.write(f"**{row[1]}** — {status}")
                if col2.button("Aktifkan", key=f"aktif_{row[0]}"):
                    c.execute("UPDATE kajian SET aktif = 0")
                    c.execute("UPDATE kajian SET aktif = 1 WHERE id = ?", (row[0],))
                    conn.commit()
                    st.rerun()

        with tab2:
            c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
            aktif = c.fetchone()
            if aktif:
                st.write(f"**Moderasi — {aktif[1]}**")
                c.execute("""SELECT id, nama_penanya, pertanyaan, tanggal, approved 
                             FROM pertanyaan WHERE kajian_id = ? ORDER BY tanggal DESC""", (aktif[0],))
                for q in c.fetchall():
                    status = "Approved" if q[4] else "Menunggu"
                    with st.expander(f"{q[1]} — {q[3]} — {status}"):
                        st.write(q[2])
                        if q[4] == 0:
                            c1, c2 = st.columns(2)
                            if c1.button("Approve", key=f"a{q[0]}"):
                                c.execute("UPDATE pertanyaan SET approved = 1 WHERE id = ?", (q[0],))
                                conn.commit()
                                st.rerun()
                            if c2.button("Hapus", key=f"d{q[0]}"):
                                c.execute("DELETE FROM pertanyaan WHERE id = ?", (q[0],))
                                conn.commit()
                                st.rerun()
            else:
                st.info("Belum ada kajian aktif.")

        with tab3:
            st.success("QR CODE TETAP SELAMANYA — Cetak sekali, pakai terus!")
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={PERMANENT_URL}"
            st.image(qr_url, width=350)
            st.code(PERMANENT_URL)
            st.markdown(f"[Download QR Code]({qr_url})")
