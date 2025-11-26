import streamlit as st
import sqlite3
from datetime import datetime
import urllib.parse

# ===================================
# DATABASE
# ===================================
conn = sqlite3.connect('kajian_qna.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS kajian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                tanggal_dibuat TEXT DEFAULT (datetime('now')),
                aktif INTEGER DEFAULT 0
             )''')

c.execute('''CREATE TABLE IF NOT EXISTS pertanyaan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kajian_id INTEGER,
                nama_penanya TEXT NOT NULL,
                pertanyaan TEXT NOT NULL,
                tanggal TEXT DEFAULT (datetime('now')),
                approved INTEGER DEFAULT 0
             )''')
conn.commit()

# ===================================
# KONFIGURASI
# ===================================
PASS_OPERATOR = "operator123"
PASS_USTADZ   = "ustadz123"
LINK_DEPLOY   = "https://tanya-ustadz-dirj.streamlit.app"  # GANTI SETELAH DEPLOY

# ===================================
# MODE PENANYA (QR)
# ===================================
if st.query_params.get("penanya") == "yes":
    st.set_page_config(page_title="Tanya Ustadz", layout="centered")
    st.title("Tanya Ustadz")

    c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
    aktif = c.fetchone()

    if not aktif:
        st.error("Belum ada kajian aktif.")
        st.info("Hubungi operator.")
        st.stop()

    st.success(f"KAJIAN: **{aktif[1]}**")

    with st.form("form_tanya"):
        nama = st.text_input("Nama Anda *")
        pertanyaan = st.text_area("Pertanyaan Anda *", height=150)
        kirim = st.form_submit_button("Kirim Pertanyaan", type="primary")

        if kirim:
            if not nama.strip() or not pertanyaan.strip():
                st.error("Nama dan pertanyaan wajib diisi!")
            else:
                c.execute("INSERT INTO pertanyaan (kajian_id, nama_penanya, pertanyaan) VALUES (?, ?, ?)",
                          (aktif[0], nama.strip(), pertanyaan.strip()))
                conn.commit()
                st.success("Pertanyaan berhasil dikirim! Menunggu moderasi.")
                st.toast("Terima kasih sudah bertanya — Jazakumullah khoiron katsiro")

    st.caption("KajianQNA • Aman • Real-time")
    st.stop()

# ===================================
# DASHBOARD UTAMA + AUTO REFRESH SETIAP 5 DETIK
# ===================================
st.set_page_config(page_title="KajianQNA - Panel", layout="wide")
st.title("KajianQNA – Panel Ustadz & Operator")

# Auto refresh halaman setiap 5 detik (pertanyaan langsung muncul!)
st.rerun_every(5)

# Session login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None

# ===================================
# LOGIN
# ===================================
if not st.session_state.logged_in:
    st.sidebar.header("Login")
    role = st.sidebar.radio("Role", ["Operator", "Ustadz"])
    pwd  = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button(f"Masuk sebagai {role}", type="primary", use_container_width=True):
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

st.sidebar.success(f"**{st.session_state.role}**")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

# ===================================
# DASHBOARD USTADZ — REAL-TIME
# ===================================
if st.session_state.role == "Ustadz":
    st.header("Dashboard Ustadz")
    
    c.execute("SELECT nama FROM kajian WHERE aktif = 1")
    aktif_nama = c.fetchone()
    if aktif_nama:
        st.success(f"KAJIAN AKTIF: **{aktif_nama[0]}**")
    else:
        st.warning("Belum ada kajian aktif")

    c.execute("""SELECT nama_penanya, pertanyaan, tanggal 
                 FROM pertanyaan 
                 WHERE kajian_id IN (SELECT id FROM kajian WHERE aktif = 1) 
                 AND approved = 1 
                 ORDER BY tanggal DESC""")
    rows = c.fetchall()

    if not rows:
        st.info("Belum ada pertanyaan yang di-approve.")
    else:
        for n, q, t in rows:
            tgl = t.split('.')[0] if t and '.' in t else t
            with st.expander(f"{n} • {tgl}"):
                st.markdown(q)

# ===================================
# DASHBOARD OPERATOR — REAL-TIME
# ===================================
elif st.session_state.role == "Operator":
    st.header("Dashboard Operator")
    tab1, tab2, tab3 = st.tabs(["Kelola Kajian", "Moderasi (Real-time)", "QR Tetap"])

    with tab1:
        st.subheader("Buat Kajian Baru")
        with st.form("new"):
            nama_k = st.text_input("Nama Kajian *")
            if st.form_submit_button("Buat"):
                if nama_k.strip():
                    c.execute("INSERT INTO kajian (nama) VALUES (?)", (nama_k.strip(),))
                    conn.commit()
                    st.success("Kajian dibuat!")
                    # st.rerun() tidak perlu lagi karena auto refresh

        st.markdown("---")
        st.subheader("Daftar Kajian")
        c.execute("SELECT id, nama, aktif FROM kajian ORDER BY id DESC")
        for k in c.fetchall():
            c1, c2, c3 = st.columns([4, 2, 2])
            c1.write(f"**{k[1]}**")
            if k[2]:
                c2.success("AKTIF")
                if c3.button("Nonaktifkan", key=f"off_{k[0]}"):
                    c.execute("UPDATE kajian SET aktif = 0 WHERE id = ?", (k[0],))
                    conn.commit()
            else:
                c2.write("Non-Aktif")
                if c3.button("Aktifkan", key=f"on_{k[0]}", type="primary"):
                    c.execute("UPDATE kajian SET aktif = 0")
                    c.execute("UPDATE kajian SET aktif = 1 WHERE id = ?", (k[0],))
                    conn.commit()

    with tab2:
        st.subheader("Moderasi Pertanyaan — Update Otomatis")
        c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
        aktif = c.fetchone()
        if not aktif:
            st.info("Belum ada kajian aktif.")
        else:
            st.write(f"Moderasi untuk: **{aktif[1]}**")
            c.execute("SELECT id, nama_penanya, pertanyaan, tanggal, approved FROM pertanyaan WHERE kajian_id = ? ORDER BY tanggal DESC", (aktif[0],))
            all_q = c.fetchall()
            if not all_q:
                st.info("Belum ada pertanyaan.")
            else:
                for q in all_q:
                    status = "Approved" if q[4] else "Menunggu"
                    tgl = q[3].split('.')[0] if q[3] and '.' in q[3] else (q[3] or "-")
                    with st.container(border=True):
                        st.write(f"**{q[1]}** • {tgl} • **{status}**")
                        st.info(q[2])
                        col1, col2 = st.columns(2)
                        if q[4] == 0:
                            if col1.button("Approve", key=f"app_{q[0]}"):
                                c.execute("UPDATE pertanyaan SET approved = 1 WHERE id = ?", (q[0],))
                                conn.commit()
                        else:
                            col1.write("Sudah di-approve")
                        if col2.button("Hapus", key=f"del_{q[0]}", type="secondary"):
                            c.execute("DELETE FROM pertanyaan WHERE id = ?", (q[0],))
                            conn.commit()

    with tab3:
        st.success("QR CODE TETAP – PAKAI SELAMANYA!")
        link = f"{LINK_DEPLOY}?penanya=yes"
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=600x600&data={urllib.parse.quote(link)}"
        col1, col2 = st.columns(2)
        col1.image(qr, caption="Scan untuk bertanya")
        col2.code(link)
        st.info("QR ini otomatis ikut kajian aktif — cetak sekali, pakai selamanya!")

# Footer
st.sidebar.caption("KajianQNA • Real-time • Tanpa Refresh Manual • Jazakumullah khoiron")
