# Flask app entry point
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_migrate import Migrate
from config import Config
from models import db, User, SwapRequest, Feedback
from forms import RegisterForm, LoginForm, ProfileForm
from utils import generate_token, confirm_token

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
mail = Mail(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.')
            return redirect(url_for('register'))
        user = User(email=form.email.data, name=form.name.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        token = generate_token(user.email)
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = f'Click to confirm your email: <a href="{confirm_url}">{confirm_url}</a>'
        msg = Message('Confirm Your Email', recipients=[user.email], html=html)
        mail.send(msg)

        flash('Check your email to confirm registration.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/confirm/<token>')
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash('Confirmation link is invalid or expired.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=email).first_or_404()
    if user.is_verified:
        flash('Account already confirmed.')
    else:
        user.is_verified = True
        db.session.commit()
        flash('Email confirmed. You can now login.')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_verified:
                flash('Please verify your email.')
                return redirect(url_for('login'))
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials.')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        form.populate_obj(current_user)
        db.session.commit()
        flash('Profile updated.')
        return redirect(url_for('profile'))
    return render_template('profile.html', form=form)

@app.route('/browse')
def browse():
    skill = request.args.get('skill')
    users = []
    if skill:
        users = User.query.filter(
            User.is_public == True,
            User.is_banned == False,
            User.skills_offered.ilike(f'%{skill}%')
        ).all()
    return render_template('browse.html', users=users)

@app.route('/swap/<int:user_id>')
@login_required
def swap_request(user_id):
    receiver = User.query.get_or_404(user_id)
    if receiver.id == current_user.id:
        flash('You cannot swap with yourself.')
        return redirect(url_for('browse'))
    existing = SwapRequest.query.filter_by(sender_id=current_user.id, receiver_id=receiver.id).first()
    if existing:
        flash('Swap already requested.')
        return redirect(url_for('browse'))
    swap = SwapRequest(sender=current_user, receiver=receiver)
    db.session.add(swap)
    db.session.commit()
    flash('Swap request sent.')
    return redirect(url_for('browse'))

@app.route('/swaps')
@login_required
def my_swaps():
    sent = SwapRequest.query.filter_by(sender_id=current_user.id).all()
    received = SwapRequest.query.filter_by(receiver_id=current_user.id).all()
    return render_template('swaps.html', sent=sent, received=received)

@app.route('/swap/<int:swap_id>/accept')
@login_required
def accept_swap(swap_id):
    swap = SwapRequest.query.get_or_404(swap_id)
    if swap.receiver_id != current_user.id:
        flash('Unauthorized.')
        return redirect(url_for('my_swaps'))
    swap.status = 'accepted'
    db.session.commit()
    flash('Swap accepted.')
    return redirect(url_for('my_swaps'))

@app.route('/swap/<int:swap_id>/delete')
@login_required
def delete_swap(swap_id):
    swap = SwapRequest.query.get_or_404(swap_id)
    if swap.sender_id != current_user.id:
        flash('Unauthorized.')
        return redirect(url_for('my_swaps'))
    db.session.delete(swap)
    db.session.commit()
    flash('Swap request deleted.')
    return redirect(url_for('my_swaps'))

if __name__ == "__main__":
    app.run(debug=True)
