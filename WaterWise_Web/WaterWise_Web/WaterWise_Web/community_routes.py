from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Post 
import datetime

# --- Blueprint tanımı ---
community = Blueprint("community", __name__, template_folder="templates")

# === Topluluk ana sayfası (feed) ===
@community.route('/feed')
@login_required
def feed():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('feed.html', posts=posts)

# === Gönderi oluşturma (feed içinde standart gönderi formu için) ===
@community.route('/post', methods=['POST'])
@login_required
def create_post():
    # feed.html içinde <input name="content"> kullandıysanız bu endpoint ile uyumlu olur
    content = request.form.get('content', '')
    if not content or not content.strip():
        flash("Gönderi boş olamaz.", "danger")
        return redirect(url_for('community.feed'))
    
    new_post = Post(
        content=content.strip(),
        user_id=current_user.id,
        timestamp=datetime.datetime.utcnow()
    )
    db.session.add(new_post)
    db.session.commit()
    flash("Gönderi paylaşıldı!", "success")
    return redirect(url_for('community.feed'))

# === İpucu formu (feed.html içindeki ipucu formu 'tip_content' gönderiyorsa) ===
@community.route('/post_tip', methods=['POST'])
@login_required
def post_tip():
    # feed.html içinde <input name="tip_content"> veya <textarea name="tip_content"> varsa kullanın
    tip_content = request.form.get('tip_content', '')
    if not tip_content or not tip_content.strip():
        flash("İpucu boş olamaz!", "danger")
        return redirect(url_for('community.feed'))

    new_post = Post(
        content=tip_content.strip(),
        user_id=current_user.id,
        timestamp=datetime.datetime.utcnow()
    )
    db.session.add(new_post)
    db.session.commit()
    flash("İpucu paylaşıldı!", "success")
    return redirect(url_for('community.feed'))

# === Gönderi beğenme ===
@community.route('/like/<int:post_id>', methods=['POST', 'GET'])
@login_required
def like_post(post_id):
    post = Post.query.get(post_id)
    if post:
        post.likes = (post.likes or 0) + 1
        db.session.commit()
    return redirect(url_for('community.feed'))

# === Profil sayfası ===
@community.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()

        # Basit Validasyon
        if not username or not email:
            flash("Kullanıcı adı ve e-posta boş olamaz.", "danger")
            return redirect(url_for('community.profile'))

        # E-posta kontrolü (başkası kullanıyor mu?)
        existing_user = User.query.filter(User.email == email).first()
        if existing_user and existing_user.id != current_user.id:
            flash("Bu e-posta adresi başka bir kullanıcı tarafından kullanılıyor.", "danger")
            return redirect(url_for('community.profile'))

        # Güncelleme
        current_user.username = username
        current_user.email = email

        if password:
            current_user.password = generate_password_hash(password)
            flash("Profil bilgileri ve şifre güncellendi!", "success")
        else:
            flash("Profil bilgileri güncellendi!", "success")

        db.session.commit()
        return redirect(url_for('community.profile'))

    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.timestamp.desc()).all()
    return render_template('profile.html', user=current_user, posts=posts)

# === Kayıt olma ===
@community.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash("Lütfen tüm alanları doldurun.", "danger")
            return redirect(url_for('community.register'))

        if User.query.filter_by(email=email).first():
            flash("Bu e-posta zaten kayıtlı.", "danger")
            return redirect(url_for('community.register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash("Kayıt başarılı! Giriş yapabilirsin.", "success")
        return redirect(url_for('community.login'))

    return render_template('register.html')

# === Giriş ===
@community.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash("E-posta ve şifre girin.", "danger")
            return redirect(url_for('community.login'))

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash("Hatalı e-posta veya şifre.", "danger")
            return redirect(url_for('community.login'))

        login_user(user)
        return redirect(url_for('community.feed'))
    return render_template('login.html')

# === Çıkış ===
@community.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('community.login'))
