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
                approved INTEGER DEFAULT 0,
                FOREIGN KEY (kajian_id) REFERENCES kajian (id)
             )''')
conn.commit()

# ===================================
# KONFIGURASI
# ===================================
PASS_OPERATOR = "operator123"   # GANTI SESUAI KEINGINAN
PASS_USTADZ = "ustadz123"       # GANTI SESUAI KEINGINAN

# GANTI SETELAH DEPLOY!
LINK_DEPLOY = "https://tanya-ustadz-dirj.streamlit.app"  # UBAH INI NANTI

# ===================================
# CEK MODE PENANYA (dari QR)
# ===================================
if st.query_params.get("penanya") == "yes":
    st.set_page_config(page_title="Tanya Ustadz", layout="centered")
    st.title("Tanya Ustadz")

    c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
    aktif = c.fetchone()

    if not aktif:
        st.error("Belum ada kajian aktif.")
        st.info("Hubungi operator untuk mengaktifkan kajian.")
        st.stop()

    st.success(f"KAJIAN AKTIF: **{aktif[1]}**")

    with st.form("form_tanya"):
        nama = st.text_input("Nama Anda *", placeholder="Contoh: Ahmad / Ibu Fatimah")
        pertanyaan = st.text_area("Pertanyaan Anda *", height=150, placeholder="Tuliskan dengan sopan dan jelas...")
        kirim = st.form_submit_button("Kirim Pertanyaan", type="primary")

        if kirim:
            if not nama.strip() or not pertanyaan.strip():
                st.error("Nama dan pertanyaan wajib diisi!")
            else:
                c.execute("INSERT INTO pertanyaan (kajian_id, nama_penanya, pertanyaan) VALUES (?, ?, ?)",
                          (aktif[0], nama.strip(), pertanyaan.strip()))
                conn.commit()
                st.success("Pertanyaan terkirim! Menunggu moderasi.")
                st.balloons()

    st.caption("KajianQNA • Aman • Terfilter • Rahasia Terjaga")
    st.stop()

# ===================================
# DASHBOARD UTAMA (Operator & Ustadz)
# ===================================
st.set_page_config(page_title="KajianQNA - Panel", layout="wide")
st.title("KajianQNA – Panel Ustadz & Operator")

# Session state untuk login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None

# ===================================
# LOGIN DENGAN TOMBOL (RAPI!)
# ===================================
if not st.session_state.logged_in:
    st.sidebar.header("Login Panel")
    role = st.sidebar.radio("Pilih Role", ["Operator", "Ustadz"])
    pwd = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Masuk sebagai " + role, type="primary", use_container_width=True):
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
# TAMPILKAN STATUS LOGIN
# ===================================
st.sidebar.success(f"Login sebagai: **{st.session_state.role}**")
if st.sidebar.button("Logout", type="secondary"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

# ===================================
# DASHBOARD USTADZ
# ===================================
if st.session_state.role == "Ustadz":
    st.header("Dashboard Ustadz")

    c.execute("SELECT nama FROM kajian WHERE aktif = 1")
    kajian_aktif = c.fetchone()
    if kajian_aktif:
        st.success(f"KAJIAN AKTIF: **{kajian_aktif[0]}**")
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
        for nama, isi, tgl in rows:
            with st.expander(f"{nama} • {tgl.split('.')[0] if '.' in tgl else tgl}"):
                st.write(isi)

# ===================================
# DASHBOARD OPERATOR
# ===================================
elif st.session_state.role == "Operator":
    st.header("Dashboard Operator")
    tab1, tab2, tab3 = st.tabs(["Kelola Kajian", "Moderasi Pertanyaan", "QR Tetap"])

    with tab1:
        st.subheader("Buat Kajian Baru")
        with st.form("buat_kajian"):
            nama_kajian = st.text_input("Nama Kajian *")
            submit = st.form_submit_button("Buat Kajian Baru")
            if submit and nama_kajian.strip():
                c.execute("INSERT INTO kajian (nama) VALUES (?)", (nama_kajian.strip(),))
                conn.commit()
                st.success(f"Kajian **{nama_kajian}** berhasil dibuat!")
                st.rerun()

        st.markdown("---")
        st.subheader("Daftar Kajian")

        c.execute("SELECT id, nama, aktif FROM kajian ORDER BY id DESC")
        kajians = c.fetchall()

        for kaj in kajians:
            col1, col2, col3 = st.columns([4, 2, 2])
            status = "AKTIF" if kaj[2] else "Non-Aktif"
            warna = "success" if kaj[2] else "normal"
            col1.write(f"**{kaj[1]}**")
            col2.write(status)

            if kaj[2]:
                if col3.button("Nonaktifkan", key=f"off_{kaj[0]}"):
                    c.execute("UPDATE kajian SET aktif = 0 WHERE id = ?", (kaj[0],))
                    conn.commit()
                    st.rerun()
            else:
                if col3.button("Aktifkan", key=f"on_{kaj[0]}", type="primary"):
                    c.execute("UPDATE kajian SET aktif = 0")  # Matikan semua
                    c.execute("UPDATE kajian SET aktif = 1 WHERE id = ?", (kaj[0],))
                    conn.commit()
                    st.rerun()

    with tab2:
        st.subheader("Moderasi Pertanyaan")
        c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
        aktif = c.fetchone()

        if not aktif:
            st.info("Belum ada kajian aktif.")
        else:
            st.write(f"Moderasi untuk: **{aktif[1]}**")
            c.execute("SELECT id, nama_penanya, pertanyaan, tanggal FROM pertanyaan WHERE kajian_id = ? AND approved = 0 ORDER BY tanggal DESC", (aktif[0],))
            waiting = c.fetchall()

            if not waiting:
                st.success("Semua pertanyaan sudah dimoderasi!")
            else:
                for p in waiting:
                    with st.container(border=True):
                        st.write(f"**{p[1]}** • {p[3].split('.')[0]}")
                        st.info(p[2])
                        c1, c2 = st.columns(2)
                        if c1.button("Approve", key=f"ok_{p[0]}"):
                            c.execute("UPDATE pertanyaan SET approved = 1 WHERE id = ?", (p[0],))
                            conn.commit()
                            st.rerun()
                        if c2.button("Tolak", key=f"no_{p[0]}", type="secondary"):
                            c.execute("DELETE FROM pertanyaan WHERE id = ?", (p[0],))
                            conn.commit()
                            st.rerun()

    with tab3:
        st.success("QR CODE TETAP – PAKAI SELAMANYA!")
        qr_link = f"{LINK_DEPLOY}?penanya=yes"
        qr_img = f"https://api.qrserver.com/v1/create-qr-code/?size=600x600&data={urllib.parse.quote(qr_link)}"
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(qr_img, caption="Scan untuk bertanya")
        with col2:
            st.code(qr_link, language="text")
        
        st.info("QR ini otomatis mengikuti kajian yang aktif!")

# Footer
st.sidebar.caption("KajianQNA vFinal • Stabil • Tanpa Auto Refresh")
