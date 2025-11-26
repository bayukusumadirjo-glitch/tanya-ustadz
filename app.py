from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'rahasia123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kajian.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Kajian(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(200), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Pertanyaan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_penanya = db.Column(db.String(100), nullable=False)
    isi = db.Column(db.Text, nullable=False)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)
    kajian_id = db.Column(db.Integer, db.ForeignKey('kajian.id'), nullable=False)
    approved = db.Column(db.Boolean, default=False)

# Buat database pertama kali
with app.app_context():
    db.create_all()

# === HALAMAN PUBLIK (PENANYA) ===
@app.route('/')
def index():
    kajians = Kajian.query.all()
    return render_template('index.html', kajians=kajians)

@app.route('/submit/<int:kajian_id>', methods=['GET', 'POST'])
def submit(kajian_id):
    kajian = Kajian.query.get_or_404(kajian_id)
    if request.method == 'POST':
        nama = request.form['nama']
        isi = request.form['pertanyaan']

        if not nama.strip() or not isi.strip():
            flash('Nama dan pertanyaan harus diisi!', 'error')
            return redirect(url_for('submit', kajian_id=kajian_id))

        p = Pertanyaan(nama_penanya=nama, isi=isi, kajian_id=kajian_id)
        db.session.add(p)
        db.session.commit()
        flash('Pertanyaan berhasil dikirim! Menunggu moderasi operator.', 'success')
        return redirect(url_for('index'))

    return render_template('submit.html', kajian=kajian)

# === LOGIN ===
@app.route('/login/<role>', methods=['GET', 'POST'])
def login(role):
    if role not in ['operator', 'ustadz']:
        return "Role tidak valid"

    if request.method == 'POST':
        password = request.form['password']

        if role == 'operator' and password == 'operator123':  # ← ganti password di sini jika mau
            session['role'] = 'operator'
            return redirect(url_for('operator_dashboard'))
        elif role == 'ustadz' and password == 'ustadz123':      # ← ganti password di sini jika mau
            session['role'] = 'ustadz'
            return redirect(url_for('ustadz_dashboard'))
        else:
            flash('Password salah!', 'error')

    return render_template('login.html', role=role.capitalize())

@app.route('/logout')
def logout():
    session.pop('role', None)
    return redirect(url_for('index'))

# === OPERATOR ===
@app.route('/operator')
def operator_dashboard():
    if session.get('role') != 'operator':
        return redirect(url_for('login', role='operator'))

    kajians = Kajian.query.all()
    return render_template('operator_dashboard.html', kajians=kajians)

@app.route('/operator/create', methods=['GET', 'POST'])
def create_kajian():
    if session.get('role') != 'operator':
        return redirect(url_for('login', role='operator'))

    if request.method == 'POST':
        nama = request.form['nama'].strip()
        if Kajian.query.filter_by(nama=nama).first():
            flash('Nama kajian sudah ada!', 'error')
        else:
            k = Kajian(nama=nama)
            db.session.add(k)
            db.session.commit()
            flash('Kajian berhasil dibuat!', 'success')
        return redirect(url_for('operator_dashboard'))

    return render_template('create_kajian.html')

@app.route('/operator/manage/<int:kajian_id>')
def manage(kajian_id):
    if session.get('role') != 'operator':
        return redirect(url_for('login', role='operator'))

    kajian = Kajian.query.get_or_404(kajian_id)
    pertanyaans = Pertanyaan.query.filter_by(kajian_id=kajian_id).order_by(Pertanyaan.tanggal.desc()).all()
    return render_template('manage.html', kajian=kajian, pertanyaans=pertanyaans)

@app.route('/operator/approve/<int:p_id>')
def approve(p_id):
    if session.get('role') != 'operator':
        return redirect(url_for('login', role='operator'))
    p = Pertanyaan.query.get_or_404(p_id)
    p.approved = True
    db.session.commit()
    flash('Pertanyaan di-approve')
    return redirect(url_for('manage', kajian_id=p.kajian_id))

@app.route('/operator/delete/<int:p_id>')
def delete(p_id):
    if session.get('role') != 'operator':
        return redirect(url_for('login', role='operator'))
    p = Pertanyaan.query.get_or_404(p_id)
    db.session.delete(p)
    db.session.commit()
    flash('Pertanyaan dihapus')
    return redirect(url_for('manage', kajian_id=p.kajian_id))

# === USTADZ ===
@app.route('/ustadz')
def ustadz_dashboard():
    if session.get('role') != 'ustadz':
        return redirect(url_for('login', role='ustadz'))

    kajians = Kajian.query.all()
    return render_template('ustadz_dashboard.html', kajians=kajians)

@app.route('/ustadz/view/<int:kajian_id>')
def view_kajian(kajian_id):
    if session.get('role') != 'ustadz':
        return redirect(url_for('login', role='ustadz'))

    kajian = Kajian.query.get_or_404(kajian_id)
    pertanyaans = Pertanyaan.query.filter_by(kajian_id=kajian_id, approved=True).order_by(Pertanyaan.tanggal.desc()).all()
    return render_template('view_ustadz.html', kajian=kajian, pertanyaans=pertanyaans)

if __name__ == '__main__':
    app.run(debug=True)
