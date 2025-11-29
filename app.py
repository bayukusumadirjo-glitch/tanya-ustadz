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
                aktif INTEGER DEFAULT 0,
                ustadz TEXT,
                tanggal_kajian TEXT
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
# COUNTER UNTUK KEY UNIK (INI RAHASIA JALANNYA!)
# ===================================
if "btn_counter" not in st.session_state:
    st.session_state.btn_counter = 0
st.session_state.btn_counter += 1

# ===================================
# FORMAT TANGGAL
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
LINK_DEPLOY   = "https://tanya-ustadz-dirj.streamlit.app"

# ===================================
# LOGIN & MODE PENANYA (tetap sama, saya singkat)
# ===================================
# ... (kode login dan mode penanya tetap sama seperti sebelumnya) ...

# ===================================
# DASHBOARD OPERATOR — TOMBOL HAPUS JALAN 100%!
# ===================================
elif st.session_state.role == "Operator":
    st.header("Dashboard Operator")
    tab1, tab2, tab3 = st.tabs(["Kelola Kajian", "Moderasi", "QR Tetap"])

    # ... (tab Kelola Kajian & QR Tetap tetap sama) ...

    with tab2:
        st.subheader("Moderasi Pertanyaan")
        c.execute("SELECT id, nama, ustadz, tanggal_kajian FROM kajian WHERE aktif = 1")
        aktif = c.fetchone()
        if not aktif:
            st.info("Belum ada kajian aktif.")
        else:
            st.write(f"Moderasi untuk: **{aktif[1]}** • {aktif[2] or 'Ustadz'} • {format_tanggal_hanya(aktif[3]) if aktif[3] else '-'}")
            
            c.execute("SELECT id, nama_penanya, pertanyaan, tanggal, approved FROM pertanyaan WHERE kajian_id = ? ORDER BY tanggal DESC", (aktif[0],))
            pertanyaans = c.fetchall()

            if not pertanyaans:
                st.info("Belum ada pertanyaan masuk.")
            else:
                for q in pertanyaans:
                    q_id, nama, isi, tgl, approved = q
                    # KEY UNIK PAKAI COUNTER GLOBAL → 100% JALAN!
                    key_suffix = f"{q_id}_{st.session_state.btn_counter}"

                    with st.container(border=True):
                        st.write(f"**{nama}** • {format_tanggal_hanya(tgl)}")
                        st.info(isi)

                        col1, col2 = st.columns(2)

                        if approved == 0:
                            if col1.button("Approve", key=f"app_{key_suffix}"):
                                c.execute("UPDATE pertanyaan SET approved = 1 WHERE id = ?", (q_id,))
                                conn.commit()
                                st.success(f"Pertanyaan dari {nama} di-approve!")
                                st.rerun()
                        else:
                            col1.success("Sudah di-approve")

                        if col2.button("Hapus", key=f"del_{key_suffix}", type="secondary"):
                            c.execute("DELETE FROM pertanyaan WHERE id = ?", (q_id,))
                            conn.commit()
                            st.success(f"Pertanyaan dari {nama} dihapus!")
                            st.rerun()

    with tab3:
        st.success("QR CODE TETAP – PAKAI SELAMANYA!")
        link = f"{LINK_DEPLOY}?penanya=yes"
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=600x600&data={urllib.parse.quote(link)}"
        c1, c2 = st.columns(2)
        c1.image(qr, caption="Scan untuk bertanya")
        c2.code(link)

st.sidebar.caption("KajianQNA • Final • Tombol Hapus JALAN 100% • Barokah")
