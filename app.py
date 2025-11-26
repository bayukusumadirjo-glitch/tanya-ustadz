import streamlit as st
import sqlite3
from datetime import datetime
import urllib.parse

# ===================================
# KONEKSI + UPGRADE DATABASE OTOMATIS
# ===================================
conn = sqlite3.connect('kajian_qna.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS kajian (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                tanggal_dibuat TEXT DEFAULT (datetime('now')),
                aktif INTEGER DEFAULT 0
             )''')

# Tambah kolom ustadz & tanggal_kajian kalau belum ada
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
# FUNGSI FORMAT TANGGAL INDONESIA
# ===================================
def format_tanggal(tanggal_str):
    if not tanggal_str:
        return "Tidak ada tanggal"
    try:
        dt = datetime.strptime(tanggal_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
        bulan = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Ags", "Sep", "Okt", "Nov", "Des"]
        return f"{dt.day} {bulan[dt.month-1]} {dt.year}, {dt.strftime('%H:%M')}"
    except:
        try:
            dt = datetime.strptime(tanggal_str, "%Y-%m-%d")
            bulan = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Ags", "Sep", "Okt", "Nov", "Des"]
            return f"{dt.day} {bulan[dt.month-1]} {dt.year}"
        except:
            return tanggal_str

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

    c.execute("SELECT id, nama, ustadz, tanggal_kajian FROM kajian WHERE aktif = 1")
    aktif = c.fetchone()

    if not aktif:
        st.error("Belum ada kajian aktif.")
        st.info("Silakan hubungi operator masjid.")
        st.stop()

    ustadz_nama = aktif[2] if aktif[2] else "Ustadz"
    tgl_kajian = format_tanggal(aktif[3]) if aktif[3] else "Tanggal belum ditentukan"

    st.success(f"KAJIAN: **{aktif[1]}**")
    st.info(f"**{ustadz_nama}** • {tgl_kajian}")

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
                st.success("Pertanyaan berhasil dikirim!")
                st.toast("Terima kasih sudah bertanya — Jazakumullah khoiron katsiro")

    st.caption("KajianQNA • Aman • Terfilter")
    st.stop()

# ===================================
# DASHBOARD UTAMA
# ===================================
st.set_page_config(page_title="KajianQNA - Panel", layout="wide")
st.title("KajianQNA – Panel Ustadz & Operator")
st.caption(f"Hari ini: **{datetime.now().strftime('%A, %d %B %Y | %H:%M')}**")

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
# DASHBOARD USTADZ
# ===================================
if st.session_state.role == "Ustadz":
    st.header("Dashboard Ustadz")
    c.execute("SELECT nama, ustadz, tanggal_kajian FROM kajian WHERE aktif = 1")
    aktif = c.fetchone()
    if aktif:
        ustadz_nama = aktif[1] if aktif[1] else "Ustadz"
        tgl = format_tanggal(aktif[2]) if aktif[2] else "Tanggal belum ditentukan"
        st.success(f"KAJIAN AKTIF: **{aktif[0]}**")
        st.info(f"**{ustadz_nama}** • {tgl}")
    else:
        st.warning("Belum ada kajian aktif")

    c.execute("""SELECT nama_penanya, pertanyaan, tanggal FROM pertanyaan 
                 WHERE kajian_id IN (SELECT id FROM kajian WHERE aktif = 1) AND approved = 1 
                 ORDER BY tanggal DESC""")
    rows = c.fetchall()
    if not rows:
        st.info("Belum ada pertanyaan yang di-approve.")
    else:
        for n, q, t in rows:
            with st.expander(f"{n} • {format_tanggal(t)}"):
                st.markdown(q)

# ===================================
# DASHBOARD OPERATOR — DENGAN FITUR EDIT KAJIAN!
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
            submit = st.form_submit_button("Buat Kajian Baru", type="primary")
            if submit:
                if nama_k.strip() and ustadz.strip():
                    c.execute("INSERT INTO kajian (nama, ustadz, tanggal_kajian) VALUES (?, ?, ?)",
                              (nama_k.strip(), ustadz.strip(), str(tgl_kajian)))
                    conn.commit()
                    st.success("Kajian berhasil dibuat!")
                    st.rerun()
                else:
                    st.error("Semua field wajib diisi!")

        st.markdown("---")
        st.subheader("Daftar Kajian")

        c.execute("SELECT id, nama, ustadz, tanggal_kajian, aktif FROM kajian ORDER BY id DESC")
        kajians = c.fetchall()

        for k in kajians:
            with st.expander(f"**{k[1]}** • {k[2] or 'Ustadz'} • {format_tanggal(k[3]) if k[3] else '-'}", expanded=False):
                col_a, col_b, col_c = st.columns([2, 2, 3])

                # Tombol Edit
                if col_a.button("Edit", key=f"edit_{k[0]}"):
                    st.session_state.edit_id = k[0]
                    st.session_state.edit_nama = k[1]
                    st.session_state.edit_ustadz = k[2]
                    st.session_state.edit_tanggal = k[3] or datetime.now().date()
                    st.rerun()

                # Status Aktif
                status = "AKTIF" if k[4] else "Non-Aktif"
                warna = "success" if k[4] else "secondary"
                col_b.write(f"**Status:** :{warna}[{status}]")

                # Tombol Ganti Status
                if k[4]:
                    if col_c.button("Nonaktifkan", key=f"off_{k[0]}"):
                        c.execute("UPDATE kajian SET aktif = 0 WHERE id = ?", (k[0],))
                        conn.commit()
                        st.rerun()
                else:
                    if col_c.button("Jadikan Aktif", key=f"on_{k[0]}", type="primary"):
                        c.execute("UPDATE kajian SET aktif = 0")  # Matikan semua
                        c.execute("UPDATE kajian SET aktif = 1 WHERE id = ?", (k[0],))
                        conn.commit()
                        st.rerun()

        # === FORM EDIT KAJIAN (Modal Style) ===
        if "edit_id" in st.session_state:
            st.markdown("---")
            st.subheader("Edit Kajian")
            with st.form("edit_form", clear_on_submit=True):
                edit_nama = st.text_input("Nama Kajian", value=st.session_state.edit_nama)
                edit_ustadz = st.text_input("Nama Ustadz", value=st.session_state.edit_ustadz or "")
                edit_tanggal = st.date_input("Tanggal Kajian", value=datetime.strptime(st.session_state.edit_tanggal, "%Y-%m-%d") if isinstance(st.session_state.edit_tanggal, str) else st.session_state.edit_tanggal)

                col1, col2 = st.columns(2)
                if col1.form_submit_button("Simpan Perubahan", type="primary"):
                    c.execute("""UPDATE kajian SET nama=?, ustadz=?, tanggal_kajian=? WHERE id=?""",
                              (edit_nama.strip(), edit_ustadz.strip() or None, str(edit_tanggal), st.session_state.edit_id))
                    conn.commit()
                    st.success("Kajian berhasil diupdate!")
                    del st.session_state.edit_id
                    st.rerun()

                if col2.form_submit_button("Batal"):
                    del st.session_state.edit_id
                    st.rerun()

    # Tab Moderasi & QR tetap sama seperti sebelumnya
    with tab2:
        st.subheader("Moderasi Pertanyaan")
        c.execute("SELECT id, nama, ustadz, tanggal_kajian FROM kajian WHERE aktif = 1")
        aktif = c.fetchone()
        if not aktif:
            st.info("Belum ada kajian aktif.")
        else:
            st.write(f"Moderasi untuk: **{aktif[1]}** • {aktif[2] or 'Ustadz'} • {format_tanggal(aktif[3]) if aktif[3] else '-'}")
            c.execute("SELECT id, nama_penanya, pertanyaan, tanggal, approved FROM pertanyaan WHERE kajian_id = ? ORDER BY tanggal DESC", (aktif[0],))
            for q in c.fetchall():
                status = "Approved" if q[4] else "Menunggu"
                with st.container(border=True):
                    st.write(f"**{q[1]}** • {format_tanggal(q[3])} • **{status}**")
                    st.info(q[2])
                    c1, c2 = st.columns(2)
                    if q[4] == 0 and c1.button("Approve", key=f"a{q[0]}"):
                        c.execute("UPDATE pertanyaan SET approved = 1 WHERE id = ?", (q[0],))
                        conn.commit()
                        st.rerun()
                    elif q[4] == 1:
                        c1.write("Sudah di-approve")
                    if c2.button("Hapus", key=f"d{q[0]}", type="secondary"):
                        c.execute("DELETE FROM pertanyaan WHERE id = ?", (q[0],))
                        conn.commit()
                        st.rerun()

    with tab3:
        st.success("QR CODE TETAP – PAKAI SELAMANYA!")
        link = f"{LINK_DEPLOY}?penanya=yes"
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=600x600&data={urllib.parse.quote(link)}"
        c1, c2 = st.columns(2)
        c1.image(qr, caption="Scan untuk bertanya")
        c2.code(link)

st.sidebar.caption("KajianQNA • Final + Edit Kajian • Barokah • Jazakumullah khoiron")
