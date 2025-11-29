import streamlit as st
import sqlite3
from datetime import datetime
import urllib.parse

# ===================================
# DATABASE + UPGRADE OTOMATIS
# ===================================
conn = sqlite3.connect('kajian_qna.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS kajian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                tanggal_dibuat TEXT DEFAULT (datetime('now')),
                aktif INTEGER DEFAULT 0
             )''')

try:
    c.execute("ALTER TABLE kajian ADD COLUMN ustadz TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass

try:
    c.execute("ALTER TABLE kajian ADD COLUMN tanggal_kajian TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass

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
# FUNGSI FORMAT TANGGAL (HANYA TANGGAL)
# ===================================
def format_tanggal_hanya(tanggal_str):
    if not tanggal_str:
        return "Tanggal tidak diketahui"
    try:
        dt = datetime.strptime(tanggal_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
        bulan = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Ags", "Sep", "Okt", "Nov", "Des"]
        return f"{dt.day} {bulan[dt.month-1]} {dt.year}"
    except:
        try:
            dt = datetime.strptime(tanggal_str, "%Y-%m-%d")
            bulan = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Ags", "Sep", "Okt", "Nov", "Des"]
            return f"{dt.day} {bulan[dt.month-1]} {dt.year}"
        except:
            return tanggal_str.split(' ')[0]

# ===================================
# KONFIGURASI
# ===================================
PASS_OPERATOR = "operator123"
PASS_USTADZ   = "ustadz123"
LINK_DEPLOY   = "https://tanya-ustadz-dirj.streamlit.app"  # GANTI SETELAH DEPLOY

# ===================================
# MODE PENANYA
# ===================================
if st.query_params.get("penanya") == "yes":
    st.set_page_config(page_title="Tanya Ustadz", layout="centered")
    st.title("Tanya Ustadz")

    c.execute("SELECT id, nama, ustadz, tanggal_kajian FROM kajian WHERE aktif = 1")
    aktif = c.fetchone()

    if not aktif:
        st.error("Belum ada kajian aktif.")
        st.info("Silakan hubungi operator masjid.")
        st.stop()

    ustadz_nama = aktif[2] if aktif[2] else "Ustadz"
    tgl_kajian = format_tanggal_hanya(aktif[3]) if aktif[3] else "Tanggal belum ditentukan"

    st.success(f"KAJIAN: **{aktif[1]}**")
    st.info(f"**{ustadz_nama}** • {tgl_kajian}")

    with st.form("form_tanya"):
        nama = st.text_input("Nama Anda *", placeholder="Ahmad / Ibu Fatimah")
        pertanyaan = st.text_area("Pertanyaan Anda *", height=150, placeholder="Tuliskan dengan ikhlas dan sopan...")
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

    st.caption("KajianQNA • Aman • Terfilter • Rahasia Terjaga")
    st.stop()

# ===================================
# DASHBOARD UTAMA
# ===================================
st.set_page_config(page_title="KajianQNA - Panel", layout="wide")
st.title("KajianQNA – Panel Ustadz & Operator")
st.caption(f"Hari ini: **{datetime.now().strftime('%A, %d %B %Y')}**")

# Login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None

if not st.session_state.logged_in:
    st.sidebar.header("Login Panel")
    role = st.sidebar.radio("Pilih Role", ["Operator", "Ustadz"])
    pwd = st.sidebar.text_input("Password", type="password")
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
if st.sidebar.button("Refresh Data Sekarang", type="primary", use_container_width=True):
    st.rerun()
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

# ===================================
# DASHBOARD USTADZ — TANPA JAM
# ===================================
if st.session_state.role == "Ustadz":
    st.header("Dashboard Ustadz")

    c.execute("SELECT nama, ustadz, tanggal_kajian FROM kajian WHERE aktif = 1")
    aktif = c.fetchone()
    if aktif:
        st.success(f"KAJIAN AKTIF: **{aktif[0]}**")
        st.info(f"**{aktif[1] or 'Ustadz'}** • {format_tanggal_hanya(aktif[2]) if aktif[2] else 'Tanggal belum ditentukan'}")
    else:
        st.warning("Belum ada kajian aktif")
        st.stop()

    st.markdown("---")
    st.subheader("Pertanyaan yang Sudah Di-Approve")

    c.execute("""SELECT nama_penanya, pertanyaan, tanggal 
                 FROM pertanyaan 
                 WHERE kajian_id IN (SELECT id FROM kajian WHERE aktif = 1) 
                 AND approved = 1 
                 ORDER BY tanggal DESC""")
    for nama, pertanyaan, tgl in c.fetchall():
        with st.container(border=True):
            st.write(f"**{nama}**")
            st.caption(format_tanggal_hanya(tgl))
            st.markdown(pertanyaan)

# ===================================
# DASHBOARD OPERATOR — KEY UNIK 100%!
# ===================================
elif st.session_state.role == "Operator":
    st.header("Dashboard Operator")
    tab1, tab2, tab3 = st.tabs(["Kelola Kajian", "Moderasi", "QR Tetap"])

    with tab1:
        st.subheader("Buat Kajian Baru")
        with st.form("new_kajian"):
            nama_k = st.text_input("Nama Kajian *")
            ustadz = st.text_input("Nama Ustadz *")
            tgl_kajian = st.date_input("Tanggal Kajian *", datetime.now())
            if st.form_submit_button("Buat Kajian", type="primary"):
                if nama_k.strip() and ustadz.strip():
                    c.execute("INSERT INTO kajian (nama, ustadz, tanggal_kajian) VALUES (?, ?, ?)",
                              (nama_k.strip(), ustadz.strip(), str(tgl_kajian)))
                    conn.commit()
                    st.success("Kajian berhasil dibuat!")
                    st.rerun()

        st.markdown("---")
        st.subheader("Daftar Kajian")
        c.execute("SELECT id, nama, ustadz, tanggal_kajian, aktif FROM kajian ORDER BY id DESC")
        for k in c.fetchall():
            kajian_id, nama, ustadz_n, tgl, aktif = k
            with st.expander(f"**{nama}** • {ustadz_n or 'Ustadz'} • {format_tanggal_hanya(tgl) if tgl else '-'}"):
                col1, col2, col3, col4 = st.columns(4)
                if col1.button("Edit", key=f"edit_{kajian_id}_{datetime.now().timestamp()}"):
                    st.session_state.edit_id = kajian_id
                    st.session_state.edit_nama = nama
                    st.session_state.edit_ustadz = ustadz_n
                    st.session_state.edit_tanggal = tgl or datetime.now().date()
                    st.rerun()
                col2.write(f"**{'AKTIF' if aktif else 'Non-Aktif'}**")
                if aktif:
                    if col3.button("Nonaktifkan", key=f"off_{kajian_id}_{datetime.now().timestamp()}"):
                        c.execute("UPDATE kajian SET aktif = 0 WHERE id = ?", (kajian_id,))
                        conn.commit()
                        st.rerun()
                else:
                    if col3.button("Jadikan Aktif", key=f"on_{kajian_id}_{datetime.now().timestamp()}", type="primary"):
                        c.execute("UPDATE kajian SET aktif = 0")
                        c.execute("UPDATE kajian SET aktif = 1 WHERE id = ?", (kajian_id,))
                        conn.commit()
                        st.rerun()
                if col4.button("Hapus Kajian", key=f"delkaj_{kajian_id}_{datetime.now().timestamp()}", type="secondary"):
                    st.session_state.hapus_id = kajian_id
                    st.session_state.hapus_nama = nama
                    st.rerun()

        # Konfirmasi Hapus
        if "hapus_id" in st.session_state:
            st.error(f"Yakin HAPUS kajian **{st.session_state.hapus_nama}**?")
            c1, c2 = st.columns(2)
            if c1.button("YA, HAPUS", type="primary"):
                c.execute("DELETE FROM pertanyaan WHERE kajian_id = ?", (st.session_state.hapus_id,))
                c.execute("DELETE FROM kajian WHERE id = ?", (st.session_state.hapus_id,))
                conn.commit()
                del st.session_state.hapus_id
                del st.session_state.hapus_nama
                st.success("Kajian dihapus permanen!")
                st.rerun()
            if c2.button("Batal"):
                del st.session_state.hapus_id
                del st.session_state.hapus_nama
                st.rerun()

        # Form Edit
        if "edit_id" in st.session_state:
            st.markdown("---")
            st.subheader("Edit Kajian")
            with st.form("edit_form"):
                e_nama = st.text_input("Nama Kajian", value=st.session_state.edit_nama)
                e_ustadz = st.text_input("Nama Ustadz", value=st.session_state.edit_ustadz or "")
                e_tanggal = st.date_input("Tanggal Kajian", value=datetime.strptime(st.session_state.edit_tanggal, "%Y-%m-%d") if isinstance(st.session_state.edit_tanggal, str) else st.session_state.edit_tanggal)
                c1, c2 = st.columns(2)
                if c1.form_submit_button("Simpan", type="primary"):
                    c.execute("UPDATE kajian SET nama=?, ustadz=?, tanggal_kajian=? WHERE id=?",
                              (e_nama.strip(), e_ustadz.strip() or None, str(e_tanggal), st.session_state.edit_id))
                    conn.commit()
                    for key in ["edit_id", "edit_nama", "edit_ustadz", "edit_tanggal"]:
                        if key in st.session_state: del st.session_state[key]
                    st.success("Berhasil diupdate!")
                    st.rerun()
                if c2.form_submit_button("Batal"):
                    for key in ["edit_id", "edit_nama", "edit_ustadz", "edit_tanggal"]:
                        if key in st.session_state: del st.session_state[key]
                    st.rerun()

    with tab2:
        st.subheader("Moderasi Pertanyaan")
        c.execute("SELECT id, nama, ustadz, tanggal_kajian FROM kajian WHERE aktif = 1")
        aktif = c.fetchone()
        if not aktif:
            st.info("Belum ada kajian aktif.")
        else:
            st.write(f"Moderasi untuk: **{aktif[1]}** • {aktif[2] or 'Ustadz'} • {format_tanggal_hanya(aktif[3]) if aktif[3] else '-'}")
            c.execute("SELECT id, nama_penanya, pertanyaan, tanggal, approved FROM pertanyaan WHERE kajian_id = ? ORDER BY tanggal DESC", (aktif[0],))
            for q in c.fetchall():
                q_id = q[0]
                unique_key = f"{datetime.now().timestamp()}_{q_id}"
                with st.container(border=True):
                    st.write(f"**{q[1]}** • {format_tanggal_hanya(q[3])}")
                    st.info(q[2])
                    c1, c2 = st.columns(2)
                    if q[4] == 0:
                        if c1.button("Approve", key=f"approve_{unique_key}"):
                            c.execute("UPDATE pertanyaan SET approved = 1 WHERE id = ?", (q_id,))
                            conn.commit()
                            st.rerun()
                    else:
                        c1.success("Sudah di-approve")
                    if c2.button("Hapus", key=f"hapus_{unique_key}", type="secondary"):
                        c.execute("DELETE FROM pertanyaan WHERE id = ?", (q_id,))
                        conn.commit()
                        st.rerun()

    with tab3:
        st.success("QR CODE TETAP – PAKAI SELAMANYA!")
        link = f"{LINK_DEPLOY}?penanya=yes"
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=600x600&data={urllib.parse.quote(link)}"
        c1, c2 = st.columns(2)
        c1.image(qr, caption="Scan untuk bertanya")
        c2.code(link)

st.sidebar.caption("KajianQNA • Final • Tombol Hapus Jalan • Barokah")
