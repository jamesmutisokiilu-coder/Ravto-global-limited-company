from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

# ==========================================
# FLASK APP
# ==========================================
app = Flask(__name__)

# ==========================================
# SECRET KEY
# ==========================================
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "ravto_super_secret_key_2026"
)

# ==========================================
# DATABASE CONFIGURATION
# ==========================================
database_url = os.environ.get("DATABASE_URL")

# FIX RENDER POSTGRESQL URL
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )

# USE POSTGRESQL ON RENDER
# FALLBACK TO SQLITE LOCALLY
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///ravto.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==========================================
# USER TABLE
# ==========================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# ==========================================
# ASSISTANT REQUEST TABLE
# ==========================================
class NeedAssistant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    assistant_area = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)

# ==========================================
# ORDERS TABLE
# ==========================================
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    category = db.Column(db.String(50), nullable=False)
    items = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    order_date = db.Column(db.String(20), nullable=False)

# ==========================================
# CREATE DATABASE
# ==========================================
with app.app_context():
    db.create_all()

# ==========================================
# HOME
# ==========================================
@app.route('/')
def home():
    return render_template('index.html')

# ==========================================
# ABOUT
# ==========================================
@app.route('/about')
def about():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('about.html')

# ==========================================
# SERVICES
# ==========================================
@app.route('/services')
def services():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('services.html')

# ==========================================
# BLOG
# ==========================================
@app.route('/blog')
def blog():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('blog.html')

# ==========================================
# CONTACT
# ==========================================
@app.route('/contact')
def contact():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('contact.html')

# ==========================================
# LOCATION
# ==========================================
@app.route('/location')
def location():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('location.html')

# ==========================================
# REGISTER
# ==========================================
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        fullname = request.form['fullname']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash('Email already exists')
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password)

        new_user = User(
            fullname=fullname,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Registration Successful')

        return redirect(url_for('login'))

    return render_template('register.html')

# ==========================================
# LOGIN
# ==========================================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            session['user_id'] = user.id
            session['user_name'] = user.fullname
            session['user_email'] = user.email

            flash('Login Successful')

            return redirect(url_for('dashboard'))

        flash('Invalid Email or Password')

        return redirect(url_for('login'))

    return render_template('login.html')

# ==========================================
# DASHBOARD
# ==========================================
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.html')

# ==========================================
# NEED ASSISTANT
# ==========================================
@app.route('/assistant', methods=['GET', 'POST'])
def assistant():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        new_request = NeedAssistant(
            fullname=request.form['fullname'],
            phone=request.form['phone'],
            email=session['user_email'],
            assistant_area=request.form['assistant_area'],
            location=request.form['location'],
            message=request.form['message']
        )

        db.session.add(new_request)
        db.session.commit()

        flash('Request Submitted Successfully')

        return redirect(url_for('assistant'))

    return render_template('assistant.html')

# ==========================================
# ORDERS
# ==========================================
@app.route('/orders', methods=['GET', 'POST'])
def orders():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        new_order = Order(
            name=request.form['name'],
            email=session['user_email'],
            phone=request.form['phone'],
            category=request.form['category'],
            items=request.form['items'],
            quantity=request.form['quantity'],
            order_date=request.form['order_date']
        )

        db.session.add(new_order)
        db.session.commit()

        flash('Order placed successfully')

        return redirect(url_for('orders'))

    user_orders = Order.query.filter_by(
        email=session['user_email']
    ).all()

    return render_template(
        'orders.html',
        orders=user_orders
    )

# ==========================================
# ADMIN LOGIN
# ==========================================
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        # ADMIN 1
        admin1_username = "kutosi"
        admin1_password = "extravaganza"

        # ADMIN 2
        admin2_username = "karanja"
        admin2_password = "extraordinary"

        # CHECK ADMINS
        if (
            (username == admin1_username and password == admin1_password)
            or
            (username == admin2_username and password == admin2_password)
        ):

            session['admin'] = True
            session['admin_name'] = username

            flash('Admin Login Successful')

            return redirect(url_for('admin_dashboard'))

        flash('Invalid Admin Credentials')

        return redirect(url_for('admin_login'))

    return render_template('admin-login.html')

# ==========================================
# ADMIN DASHBOARD
# ==========================================
@app.route('/admin-dashboard')
def admin_dashboard():

    if not session.get('admin'):

        flash('Admin Login Required')

        return redirect(url_for('admin_login'))

    users = User.query.all()
    requests = NeedAssistant.query.all()
    orders = Order.query.all()

    return render_template(
        'admin-dashboard.html',
        users=users,
        requests=requests,
        orders=orders
    )

# ==========================================
# DELETE REQUEST
# ==========================================
@app.route('/delete_request/<int:request_id>', methods=['POST'])
def delete_request(request_id):

    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    req = NeedAssistant.query.get_or_404(request_id)

    db.session.delete(req)
    db.session.commit()

    flash('Request deleted successfully')

    return redirect(url_for('admin_dashboard'))

# ==========================================
# DELETE ORDER
# ==========================================
@app.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):

    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    order = Order.query.get_or_404(order_id)

    db.session.delete(order)
    db.session.commit()

    flash('Order deleted successfully')

    return redirect(url_for('admin_dashboard'))

# ==========================================
# LOGOUT
# ==========================================
@app.route('/logout')
def logout():

    session.clear()

    flash('Logged Out Successfully')

    return redirect(url_for('home'))

# ==========================================
# RUN APP
# ==========================================
if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host='0.0.0.0',
        port=port
    )
