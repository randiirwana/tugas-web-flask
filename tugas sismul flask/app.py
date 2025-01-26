import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from sqlalchemy.exc import OperationalError, SQLAlchemyError

app = Flask(__name__)

# Konfigurasi
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:randi123@localhost/tugas_sismul'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'your_secret_key'

# Inisialisasi database dan modul tambahan
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Pesanan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100))
    email = db.Column(db.String(100))
    tanggal = db.Column(db.String(100))
    jumlah = db.Column(db.Integer)
    produk = db.Column(db.String(100))
    harga = db.Column(db.Float)
    total_harga = db.Column(db.Float)
    pesan = db.Column(db.String(200))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    try:
        if current_user.is_authenticated:
            if current_user.role == "admin":
                message = "Selamat datang di Dashboard Admin!"
            else:
                message = "Selamat datang di Halaman Pembeli!"
            return render_template("index.html", message=message)
        return redirect(url_for('login'))
    except Exception as e:
        flash(f"Terjadi kesalahan: {str(e)}", "danger")
        return redirect(url_for('login'))

@app.route('/detail')
def detail():
    return render_template('detail.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/shop')
def shop():
    return render_template('shop.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == "POST":
        try:
            email = request.form.get("email")
            password = request.form.get("password")
            
            if not email or not password:
                flash('Email dan password harus diisi', 'danger')
                return redirect(url_for('login'))
            
            user = User.query.filter_by(email=email).first()
            
            if user and bcrypt.check_password_hash(user.password, password):
                login_user(user, remember=True)
                flash(f"Selamat datang, {user.username}!", "success")
                return redirect(url_for('home'))
            else:
                flash("Email atau password salah", "danger")
                return redirect(url_for('login'))
                
        except Exception as e:
            flash(f"Terjadi kesalahan saat login: {str(e)}", "danger")
            return redirect(url_for('login'))
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    try:
        if request.method == "POST":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")
            
            if not all([username, email, password, confirm_password]):
                flash("Semua field harus diisi", "danger")
                return redirect(url_for("register"))
            
            if password != confirm_password:
                flash("Password tidak cocok", "danger")
                return redirect(url_for("register"))
                
            if User.query.filter_by(username=username).first():
                flash("Username sudah digunakan", "danger")
                return redirect(url_for("register"))
                
            if User.query.filter_by(email=email).first():
                flash("Email sudah digunakan", "danger")
                return redirect(url_for("register"))
                
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            new_user = User(username=username, email=email, password=hashed_password, role="user")
            
            try:
                db.session.add(new_user)
                db.session.commit()
                flash("Registrasi berhasil! Silakan login.", "success")
                return redirect(url_for("login"))
            except SQLAlchemyError as e:
                db.session.rollback()
                flash("Terjadi kesalahan saat mendaftar. Silakan coba lagi.", "danger")
                return redirect(url_for("register"))
            
        return render_template("register.html")
    except Exception as e:
        flash(f"Terjadi kesalahan: {str(e)}", "danger")
        return redirect(url_for('register'))

@app.route("/logout")
@login_required
def logout():
    try:
        logout_user()
        flash("Anda telah keluar", "success")
        return redirect(url_for("login"))
    except Exception as e:
        flash(f"Terjadi kesalahan saat logout: {str(e)}", "danger")
        return redirect(url_for('home'))

if __name__ == "__main__":
    with app.app_context():
        try:
            db.create_all()
            
            # Tambahkan admin jika belum ada
            admin = User.query.filter_by(email="admin@admin.com").first()
            if not admin:
                hashed_password = bcrypt.generate_password_hash("admin123").decode("utf-8")
                admin_user = User(username="admin", email="admin@admin.com", password=hashed_password, role="admin")
                db.session.add(admin_user)

            # Tambahkan pembeli (user) jika belum ada
            pembeli = User.query.filter_by(email="pembeli@pembeli.com").first()
            if not pembeli:
                hashed_password = bcrypt.generate_password_hash("pembeli123").decode("utf-8")
                buyer_user = User(username="pembeli", email="pembeli@pembeli.com", password=hashed_password, role="user")
                db.session.add(buyer_user)

            db.session.commit()
            print("Database berhasil diinisialisasi")
            
        except OperationalError as e:
            print(f"Error database operasional: {e}")
            db.session.rollback()
        except SQLAlchemyError as e:
            print(f"Error SQLAlchemy: {e}")
            db.session.rollback()
        except Exception as e:
            print(f"Error lainnya: {e}")
            db.session.rollback()

    app.run(debug=True)