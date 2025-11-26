import streamlit as st
import sqlite3
from datetime import datetime
import urllib.parse

# ===================================
# KONFIGURASI
# ===================================
DB_NAME = "kajian_qna.db"
PASS_OPERATOR = "operator123"   # GANTI SESUAI KEINGINAN
PASS_USTADZ = "ustadz123"       # GANTI SESUAI KEINGINAN

# GANTI INI SETELAH DEPLOY!
LINK_DEPLOY = "https://tanya-ustadz-dirj.streamlit.app"  # UBAH SETELAH DAPAT LINK PERMANEN

# ===================================
# DATABASE SETUP
# ===================================
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS kajian (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               nama TEXT NOT NULL,
               nama_ustadz TEXT,
               tanggal_kajian TEXT,
               tanggal_dibuat TEXT DEFAULT CURRENT_TIMESTAMP,
               aktif INTEGER DEFAULT 0
            )''')

try: c.execute("ALTER TABLE kajian ADD COLUMN nama_ustadz TEXT")
except: pass
try: c.execute("ALTER TABLE kajian ADD COLUMN tanggal_kajian TEXT")
except: pass

c.execute('''CREATE TABLE IF NOT EXISTS pertanyaan (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               kajian_id INTEGER,
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
    c.execute("SELECT nama, nama_ustadz, tanggal_kajian FROM kajian WHERE aktif = 1")
    return c.fetchone()

def set_kajian_aktif(kajian_id):
    c.execute("UPDATE kajian SET aktif = 0")
    c.execute("UPDATE kajian SET aktif = 1 WHERE id = ?", (kajian_id,))
    conn.commit()

# ===================================
# MODE PENANYA (dari QR)
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
    col1.success(f"KAJIAN: {aktif[0]}")
    col2.info(f"{aktif[1] or 'Ustadz'} • {aktif[2] or ''}")

    with st.form("form_tanya"):
        nama = st.text_input("Nama Anda *", placeholder="Wajib diisi")
        pertanyaan = st.text_area("Pertanyaan Anda *", height=150, placeholder="Tulis pertanyaan Anda di sini...")
        kirim = st.form_submit_button("Kirim Pertanyaan", type="primary")

        if kirim:
            if not nama.strip() or not pertanyaan.strip():
                st.error("Nama dan pertanyaan wajib diisi!")
            else:
                c.execute("SELECT id FROM kajian WHERE aktif = 1")
                kajian_id = c.fetchone()[0]
                c.execute("INSERT INTO pertanyaan (kajian_id, nama_penanya, isi) VALUES (?, ?, ?)",
                          (kajian_id, nama.strip(), pertanyaan.strip()))
                conn.commit()
                st.success("Pertanyaan terkirim! Menunggu moderasi operator.")
                st.balloons()

    st.caption("KajianQNA – Pertanyaan terfilter, rahasia terjaga")
    st.stop()

# ===================================
# HALAMAN UTAMA (Operator & Ustadz)
# ===================================
st.set_page_config(page_title="KajianQNA Dashboard", layout="wide")
st.title("KajianQNA – Sistem Tanya Jawab Ustadz")

# Session state untuk login (tahan refresh!)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None

# ===================================
# LOGIN
# ===================================
if not st.session_state.logged_in:
    st.markdown("### Silakan login terlebih dahulu")
    col1, col2 = st.columns([1, 2])
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
    st.success(f"KAJIAN AKTIF: {aktif[0]}")
    st.info(f"Ustadz: {aktif[1] or '-'} | Tanggal: {aktif[2] or '-'}")
else:
    st.warning("Belum ada kajian aktif")

# ===================================
# DASHBOARD USTADZ
# ===================================
if st.session_state.role == "Ustadz":
    st.header("Dashboard Ustadz")

    c.execute("SELECT id, nama FROM kajian WHERE aktif = 1")
    aktif_row = c.fetchone()
    
    if not aktif_row:
        st.info("Belum ada kajian aktif.")
    else:
        st.subheader(f"Pertanyaan untuk: {aktif_row[1]}")
        c.execute("""SELECT nama_penanya, isi, tanggal FROM pertanyaan 
                     WHERE kajian_id = ? AND approved = 1 
                     ORDER BY tanggal DESC""", (aktif_row[0],))
        rows = c.fetchall()
        
        if not rows:
            st.info("Belum ada pertanyaan yang di-approve.")
        else:
            for nama, isi, tgl in rows:
                with st.expander(f"{nama} • {tgl.split('.')[0]}"):
                    st.write(isi)

# ===================================
# DASHBOARD OPERATOR
# ===================================
elif st.session_state.role == "Operator":
    st.header("Dashboard Operator")
    tab1, tab2, tab3 = st.tabs(["Kelola Kajian", "Moderasi Pertanyaan", "QR Code Tetap"])

    with tab1:
        st.subheader("Buat Kajian Baru")
        with st.form("buat_kajian"):
            nama = st.text_input("Nama Kajian *")
            ustadz = st.text_input("Nama Ustadz")
            tgl = st.date_input("Tanggal Kajian", datetime.now())
            buat = st.form_submit_button("Buat Kajian", type="primary")
            if buat:
                if not nama.strip():
                    st.error("Nama kajian wajib diisi!")
                else:
                    c.execute("INSERT INTO kajian (nama, nama_ustadz, tanggal_kajian) VALUES (?, ?, ?)",
                              (nama, ustadz or None, str(tgl)))
                    conn.commit()
                    st.success("Kajian berhasil dibuat!")
                    st.rerun()

        st.markdown("---")
        st.subheader("Daftar Kajian")
        c.execute("SELECT id, nama, nama_ustadz, tanggal_kajian, aktif FROM kajian ORDER BY tanggal_dibuat DESC")
        for row in c.fetchall():
            cols = st.columns([4, 2, 2, 2, 1])
            cols[0].write(f"**{row[1]}**")
            cols[1].write(row[2] or "-")
            cols[2].write(row[3] or "-")
            if row[4] == 1:
                cols[3].success("AKTIF")
            else:
                if cols[3].button("Aktifkan", key=f"aktif_{row[0]}"):
                    set_kajian_aktif(row[0])
                    st.rerun()
            if cols[4].button("Hapus", key=f"hps_{row[0]}", type="secondary"):
                c.execute("DELETE FROM pertanyaan WHERE kajian_id = ?", (row[0],))
                c.execute("DELETE FROM kajian WHERE id = ?", (row[0],))
                conn.commit()
                st.success("Kajian dihapus!")
                st.rerun()

    with tab2:
        st.subheader("Moderasi Pertanyaan")
        c.execute("SELECT id FROM kajian WHERE aktif = 1")
        aktif_id = c.fetchone()
        if not aktif_id:
            st.info("Belum ada kajian aktif.")
        else:
            c.execute("""SELECT id, nama_penanya, isi, tanggal FROM pertanyaan 
                         WHERE kajian_id = ? AND approved = 0 
                         ORDER BY tanggal DESC""", (aktif_id[0],))
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
                            st.success("Di-approve!")
                            st.rerun()
                        if c2.button("Tolak/Hapus", key=f"no_{p[0]}", type="secondary"):
                            c.execute("DELETE FROM pertanyaan WHERE id = ?", (p[0],))
                            conn.commit()
                            st.error("Ditolak & dihapus")
                            st.rerun()
                    st.markdown("---")

    with tab3:
        st.success("QR CODE TETAP – CETAK SEKALI, PAKAI SELAMANYA!")
        qr_link = f"{LINK_DEPLOY}?penanya=yes"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=600x600&data={urllib.parse.quote(qr_link)}"
        col1, col2 = st.columns(2)
        col1.image(qr_url, caption="Scan = langsung ke form tanya", width=300)
        col2.code(qr_link, language="text")
        st.info("QR ini otomatis mengikuti kajian yang sedang aktif!")

# ===================================
# LOGOUT
# ===================================
if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

st.sidebar.info(f"Login sebagai: **{st.session_state.role}**")
