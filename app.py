import os
import json
import uuid
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import inspect, text

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# ============================================================
# APPLICATION
# ============================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "ravto_super_secret_key_2026"
)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

database_url = os.environ.get("DATABASE_URL")

if database_url:

    # Render may provide postgres://
    if database_url.startswith("postgres://"):

        database_url = database_url.replace(
            "postgres://",
            "postgresql+psycopg2://",
            1
        )

    # Convert standard PostgreSQL URL to psycopg2
    elif database_url.startswith("postgresql://"):

        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg2://",
            1
        )


app.config["SQLALCHEMY_DATABASE_URI"] = (
    database_url
    or "sqlite:///ravto.db"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

app.config["UPLOAD_FOLDER"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "static",
    "uploads"
)


db = SQLAlchemy(app)


# ============================================================
# CREATE UPLOAD DIRECTORY
# ============================================================

os.makedirs(
    app.config["UPLOAD_FOLDER"],
    exist_ok=True
)


# ============================================================
# USER MODEL
# ============================================================

class User(db.Model):

    __tablename__ = "user"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    fullname = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# NEED ASSISTANT MODEL
# ============================================================

class NeedAssistant(db.Model):

    __tablename__ = "need_assistant"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    fullname = db.Column(
        db.String(100),
        nullable=False
    )

    phone = db.Column(
        db.String(30),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        nullable=False
    )

    assistant_area = db.Column(
        db.String(150),
        nullable=False
    )

    location = db.Column(
        db.String(200),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    request_type = db.Column(
        db.String(100),
        default="Technical Assistance"
    )

    priority = db.Column(
        db.String(50),
        default="Normal"
    )

    budget = db.Column(
        db.String(100),
        nullable=True
    )

    project_type = db.Column(
        db.String(100),
        nullable=True
    )

    preferred_date = db.Column(
        db.String(30),
        nullable=True
    )

    preferred_time = db.Column(
        db.String(50),
        nullable=True
    )

    contact_method = db.Column(
        db.String(50),
        default="Phone"
    )

    additional_details = db.Column(
        db.Text,
        nullable=True
    )

    attachment = db.Column(
        db.String(255),
        nullable=True
    )

    status = db.Column(
        db.String(50),
        default="Pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# PRODUCT MODEL
# ============================================================

class Product(db.Model):

    __tablename__ = "product"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    price = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    stock = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    image = db.Column(
        db.String(255),
        nullable=True
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# ORDER MODEL
# ============================================================

class Order(db.Model):

    __tablename__ = "order"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    order_number = db.Column(
        db.String(50),
        unique=True,
        nullable=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        nullable=False
    )

    phone = db.Column(
        db.String(30),
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=True
    )

    items = db.Column(
        db.Text,
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    subtotal = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    total = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    order_date = db.Column(
        db.String(30),
        nullable=False
    )

    status = db.Column(
        db.String(50),
        default="Pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ============================================================
# DATABASE SCHEMA MIGRATION
# ============================================================
#
# IMPORTANT:
#
# db.create_all() creates missing tables but does NOT add
# columns to tables that already exist.
#
# This function checks the existing database and adds missing
# columns without deleting existing information.
#
# This specifically fixes:
#
# psycopg2.errors.UndefinedColumn:
# column order.order_number does not exist
#
# ============================================================

def migrate_database():

    try:

        inspector = inspect(db.engine)

        existing_tables = inspector.get_table_names()

        print(
            "DATABASE TABLES:",
            existing_tables
        )

        # ----------------------------------------------------
        # TABLE DEFINITIONS
        # ----------------------------------------------------

        required_columns = {

            "user": {

                "created_at":
                    "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"

            },

            "need_assistant": {

                "request_type":
                    "VARCHAR(100)",

                "priority":
                    "VARCHAR(50) DEFAULT 'Normal'",

                "budget":
                    "VARCHAR(100)",

                "project_type":
                    "VARCHAR(100)",

                "preferred_date":
                    "VARCHAR(30)",

                "preferred_time":
                    "VARCHAR(50)",

                "contact_method":
                    "VARCHAR(50) DEFAULT 'Phone'",

                "additional_details":
                    "TEXT",

                "attachment":
                    "VARCHAR(255)",

                "status":
                    "VARCHAR(50) DEFAULT 'Pending'",

                "created_at":
                    "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"

            },

            "product": {

                "description":
                    "TEXT",

                "price":
                    "FLOAT DEFAULT 0",

                "stock":
                    "INTEGER DEFAULT 0",

                "image":
                    "VARCHAR(255)",

                "active":
                    "BOOLEAN DEFAULT TRUE",

                "created_at":
                    "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"

            },

            "order": {

                "order_number":
                    "VARCHAR(50)",

                "category":
                    "VARCHAR(100)",

                "items":
                    "TEXT",

                "quantity":
                    "INTEGER DEFAULT 1",

                "subtotal":
                    "FLOAT DEFAULT 0",

                "total":
                    "FLOAT DEFAULT 0",

                "order_date":
                    "VARCHAR(30)",

                "status":
                    "VARCHAR(50) DEFAULT 'Pending'",

                "created_at":
                    "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"

            }

        }

        # ----------------------------------------------------
        # ADD MISSING COLUMNS
        # ----------------------------------------------------

        for table_name, columns in required_columns.items():

            if table_name not in existing_tables:

                print(
                    f"DATABASE: table '{table_name}' "
                    f"does not exist yet. db.create_all() will create it."
                )

                continue

            inspector = inspect(db.engine)

            existing_columns = {
                column["name"]
                for column in inspector.get_columns(
                    table_name
                )
            }

            for column_name, column_definition in columns.items():

                if column_name in existing_columns:

                    continue

                print(
                    f"DATABASE: adding missing column "
                    f"{table_name}.{column_name}"
                )

                # ------------------------------------------------
                # PostgreSQL
                # ------------------------------------------------

                if db.engine.dialect.name == "postgresql":

                    if table_name in [
                        "user",
                        "order"
                    ]:

                        quoted_table = (
                            f'"{table_name}"'
                        )

                    else:

                        quoted_table = table_name

                    sql = (
                        f"ALTER TABLE {quoted_table} "
                        f"ADD COLUMN IF NOT EXISTS "
                        f'"{column_name}" '
                        f"{column_definition}"
                    )

                    db.session.execute(
                        text(sql)
                    )

                # ------------------------------------------------
                # SQLite
                # ------------------------------------------------

                elif db.engine.dialect.name == "sqlite":

                    sql = (
                        f'ALTER TABLE "{table_name}" '
                        f'ADD COLUMN "{column_name}" '
                        f'{column_definition}'
                    )

                    try:

                        db.session.execute(
                            text(sql)
                        )

                    except Exception as error:

                        print(
                            "SQLITE COLUMN WARNING:",
                            error
                        )

            db.session.commit()

        # ----------------------------------------------------
        # REFRESH INSPECTOR
        # ----------------------------------------------------

        inspector = inspect(db.engine)

        # ----------------------------------------------------
        # MAKE SURE EXISTING ORDERS HAVE ORDER NUMBERS
        # ----------------------------------------------------

        if "order" in inspector.get_table_names():

            orders_without_numbers = Order.query.filter(
                db.or_(
                    Order.order_number.is_(None),
                    Order.order_number == ""
                )
            ).all()

            if orders_without_numbers:

                print(
                    f"DATABASE: assigning numbers to "
                    f"{len(orders_without_numbers)} existing orders."
                )

                for old_order in orders_without_numbers:

                    old_order.order_number = (
                        f"RAVTO-{old_order.id:06d}"
                    )

                db.session.commit()

        # ----------------------------------------------------
        # CREATE UNIQUE INDEX FOR ORDER NUMBERS
        # ----------------------------------------------------
        #
        # The model says unique=True. Existing databases may
        # not automatically receive the constraint when the
        # column is added manually.
        #
        # ----------------------------------------------------

        if db.engine.dialect.name == "postgresql":

            try:

                db.session.execute(
                    text(
                        'CREATE UNIQUE INDEX IF NOT EXISTS '
                        'ix_order_order_number_unique '
                        'ON "order" (order_number)'
                    )
                )

                db.session.commit()

            except Exception as error:

                db.session.rollback()

                print(
                    "ORDER NUMBER INDEX WARNING:",
                    error
                )

        print(
            "DATABASE SCHEMA: migration completed successfully."
        )

    except Exception as error:

        db.session.rollback()

        print(
            "DATABASE MIGRATION ERROR:",
            error
        )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

with app.app_context():

    try:

        # Create missing tables
        db.create_all()

        print(
            "DATABASE: tables verified/created."
        )

        # Add missing columns
        migrate_database()

    except Exception as error:

        print(
            "DATABASE INITIALIZATION ERROR:",
            error
        )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def login_required():

    return "user_id" in session


def admin_required():

    return session.get("admin") is True


def generate_order_number():

    # Use UUID so two customers placing orders at the same
    # second do not receive the same order number.

    unique_part = uuid.uuid4().hex[:8].upper()

    return f"RAVTO-{unique_part}"


def get_current_user():

    user_id = session.get("user_id")

    if not user_id:

        return None

    return db.session.get(
        User,
        user_id
    )


def clean(value):

    if value is None:

        return ""

    return str(value).strip()


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# ABOUT
# ============================================================

@app.route("/about")
def about():

    if not login_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "about.html"
    )


# ============================================================
# SERVICES
# ============================================================

@app.route("/services")
def services():

    if not login_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "services.html"
    )


# ============================================================
# BLOG
# ============================================================

@app.route("/blog")
def blog():

    if not login_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "blog.html"
    )


# ============================================================
# CONTACT
# ============================================================

@app.route("/contact")
def contact():

    if not login_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "contact.html"
    )


# ============================================================
# LOCATION
# ============================================================

@app.route("/location")
def location():

    if not login_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "location.html"
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        fullname = clean(
            request.form.get(
                "fullname"
            )
        )

        email = clean(
            request.form.get(
                "email"
            )
        ).lower()

        password = request.form.get(
            "password",
            ""
        )

        if not fullname or not email or not password:

            flash(
                "Please complete all registration fields."
            )

            return redirect(
                url_for("register")
            )

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "Email already exists. Please login."
            )

            return redirect(
                url_for("login")
            )

        hashed_password = generate_password_hash(
            password
        )

        new_user = User(
            fullname=fullname,
            email=email,
            password=hashed_password
        )

        try:

            db.session.add(
                new_user
            )

            db.session.commit()

            flash(
                "Registration successful. You can now login."
            )

            return redirect(
                url_for("login")
            )

        except Exception as error:

            db.session.rollback()

            print(
                "REGISTRATION ERROR:",
                error
            )

            flash(
                "Registration failed. Please try again."
            )

            return redirect(
                url_for("register")
            )

    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = clean(
            request.form.get(
                "email"
            )
        ).lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session["user_id"] = user.id

            session["user_name"] = (
                user.fullname
            )

            session["user_email"] = (
                user.email
            )

            flash(
                "Login successful."
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid email or password."
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "login.html"
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    if not login_required():

        return redirect(
            url_for("login")
        )

    current_email = session.get(
        "user_email"
    )

    user_orders = Order.query.filter_by(
        email=current_email
    ).order_by(
        Order.created_at.desc()
    ).all()

    user_requests = NeedAssistant.query.filter_by(
        email=current_email
    ).order_by(
        NeedAssistant.created_at.desc()
    ).all()

    total_orders = len(
        user_orders
    )

    total_requests = len(
        user_requests
    )

    pending_orders = Order.query.filter_by(
        email=current_email,
        status="Pending"
    ).count()

    pending_requests = NeedAssistant.query.filter_by(
        email=current_email,
        status="Pending"
    ).count()

    return render_template(
        "dashboard.html",
        orders=user_orders,
        requests=user_requests,
        total_orders=total_orders,
        total_requests=total_requests,
        pending_orders=pending_orders,
        pending_requests=pending_requests
    )


# ============================================================
# NEED ASSISTANT
# ============================================================

@app.route(
    "/assistant",
    methods=["GET", "POST"]
)
def assistant():

    if not login_required():

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        fullname = clean(
            request.form.get(
                "fullname"
            )
        )

        phone = clean(
            request.form.get(
                "phone"
            )
        )

        email = session.get(
            "user_email"
        )

        assistant_area = clean(
            request.form.get(
                "assistant_area"
            )
        )

        location = clean(
            request.form.get(
                "location"
            )
        )

        message = clean(
            request.form.get(
                "message"
            )
        )

        request_type = clean(
            request.form.get(
                "request_type"
            )
        )

        priority = clean(
            request.form.get(
                "priority"
            )
        ) or "Normal"

        budget = clean(
            request.form.get(
                "budget"
            )
        )

        project_type = clean(
            request.form.get(
                "project_type"
            )
        )

        preferred_date = clean(
            request.form.get(
                "preferred_date"
            )
        )

        preferred_time = clean(
            request.form.get(
                "preferred_time"
            )
        )

        contact_method = clean(
            request.form.get(
                "contact_method"
            )
        ) or "Phone"

        additional_details = clean(
            request.form.get(
                "additional_details"
            )
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not fullname:

            flash(
                "Please enter your full name."
            )

            return redirect(
                url_for("assistant")
            )

        if not phone:

            flash(
                "Please enter your phone number."
            )

            return redirect(
                url_for("assistant")
            )

        if not assistant_area:

            flash(
                "Please select the service you need."
            )

            return redirect(
                url_for("assistant")
            )

        if not location:

            flash(
                "Please enter your location."
            )

            return redirect(
                url_for("assistant")
            )

        if not message:

            flash(
                "Please describe the assistance you need."
            )

            return redirect(
                url_for("assistant")
            )

        # ----------------------------------------------------
        # ATTACHMENT
        # ----------------------------------------------------

        attachment_name = None

        uploaded_file = request.files.get(
            "attachment"
        )

        if uploaded_file and uploaded_file.filename:

            original_name = uploaded_file.filename

            safe_name = (
                original_name
                .replace(" ", "_")
                .replace("/", "_")
                .replace("\\", "_")
            )

            timestamp = datetime.utcnow().strftime(
                "%Y%m%d%H%M%S"
            )

            attachment_name = (
                f"{timestamp}_{safe_name}"
            )

            file_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                attachment_name
            )

            uploaded_file.save(
                file_path
            )

        # ----------------------------------------------------
        # CREATE REQUEST
        # ----------------------------------------------------

        new_request = NeedAssistant(

            fullname=fullname,

            phone=phone,

            email=email,

            assistant_area=assistant_area,

            location=location,

            message=message,

            request_type=(
                request_type
                or "Technical Assistance"
            ),

            priority=priority,

            budget=budget,

            project_type=project_type,

            preferred_date=preferred_date,

            preferred_time=preferred_time,

            contact_method=contact_method,

            additional_details=additional_details,

            attachment=attachment_name,

            status="Pending"

        )

        try:

            db.session.add(
                new_request
            )

            db.session.commit()

            flash(
                "Your assistance request has been submitted successfully. Our team will contact you."
            )

        except Exception as error:

            db.session.rollback()

            print(
                "ASSISTANT REQUEST ERROR:",
                error
            )

            flash(
                "Unable to submit your request. Please try again."
            )

        return redirect(
            url_for("assistant")
        )

    return render_template(
        "assistant.html"
    )


# ============================================================
# PRODUCTS API
# ============================================================

@app.route("/api/products")
def api_products():

    products = Product.query.filter_by(
        active=True
    ).order_by(
        Product.name.asc()
    ).all()

    data = []

    for product in products:

        data.append({

            "id": product.id,

            "name": product.name,

            "category": product.category,

            "description": product.description or "",

            "price": float(
                product.price or 0
            ),

            "stock": product.stock,

            "image": (
                url_for(
                    "static",
                    filename=product.image
                )
                if product.image
                else None
            )

        })

    return jsonify(data)


# ============================================================
# ORDERS
# ============================================================

@app.route(
    "/orders",
    methods=["GET", "POST"]
)
def orders():

    if not login_required():

        return redirect(
            url_for("login")
        )

    # ========================================================
    # POST ORDER
    # ========================================================

    if request.method == "POST":

        name = clean(
            request.form.get(
                "name"
            )
        )

        phone = clean(
            request.form.get(
                "phone"
            )
        )

        email = session.get(
            "user_email"
        )

        category = clean(
            request.form.get(
                "category"
            )
        )

        order_date = clean(
            request.form.get(
                "order_date"
            )
        )

        # ----------------------------------------------------
        # CART DATA
        # ----------------------------------------------------

        cart_data = request.form.get(
            "cart_data",
            ""
        )

        # ----------------------------------------------------
        # BACKWARD COMPATIBILITY
        # ----------------------------------------------------

        if not cart_data:

            old_items = clean(
                request.form.get(
                    "items"
                )
            )

            old_quantity = request.form.get(
                "quantity",
                "1"
            )

            try:

                old_quantity = int(
                    old_quantity
                )

            except (
                ValueError,
                TypeError
            ):

                old_quantity = 1

            if old_items:

                cart = [

                    {
                        "id": None,

                        "name": old_items,

                        "price": 0,

                        "quantity": old_quantity,

                        "subtotal": 0

                    }

                ]

            else:

                cart = []

        else:

            try:

                cart = json.loads(
                    cart_data
                )

            except Exception:

                cart = []

        # ----------------------------------------------------
        # VALIDATE CUSTOMER
        # ----------------------------------------------------

        if not name:

            flash(
                "Please enter your name."
            )

            return redirect(
                url_for("orders")
            )

        if not phone:

            flash(
                "Please enter your phone number."
            )

            return redirect(
                url_for("orders")
            )

        # ----------------------------------------------------
        # VALIDATE CART
        # ----------------------------------------------------

        if not cart or not isinstance(
            cart,
            list
        ):

            flash(
                "Your cart is empty. Please add at least one item."
            )

            return redirect(
                url_for("orders")
            )

        # ----------------------------------------------------
        # SERVER-SIDE TOTAL CALCULATION
        # ----------------------------------------------------

        validated_items = []

        total_quantity = 0

        subtotal = 0.0

        for cart_item in cart:

            if not isinstance(
                cart_item,
                dict
            ):

                continue

            try:

                product_id = int(
                    cart_item.get("id")
                )

            except (
                ValueError,
                TypeError
            ):

                continue

            try:

                requested_quantity = int(
                    cart_item.get(
                        "quantity",
                        1
                    )
                )

            except (
                ValueError,
                TypeError
            ):

                requested_quantity = 1

            if requested_quantity < 1:

                continue

            product = db.session.get(
                Product,
                product_id
            )

            if not product:

                continue

            if not product.active:

                continue

            # ------------------------------------------------
            # STOCK CHECK
            # ------------------------------------------------

            if product.stock < requested_quantity:

                flash(
                    f"Insufficient stock for {product.name}. "
                    f"Available stock: {product.stock}."
                )

                return redirect(
                    url_for("orders")
                )

            unit_price = float(
                product.price or 0
            )

            item_subtotal = (
                unit_price
                * requested_quantity
            )

            validated_items.append({

                "id": product.id,

                "name": product.name,

                "category": product.category,

                "price": unit_price,

                "quantity": requested_quantity,

                "subtotal": round(
                    item_subtotal,
                    2
                )

            })

            total_quantity += (
                requested_quantity
            )

            subtotal += (
                item_subtotal
            )

        # ----------------------------------------------------
        # VALID ITEMS
        # ----------------------------------------------------

        if not validated_items:

            flash(
                "No valid products were found in your cart."
            )

            return redirect(
                url_for("orders")
            )

        # ----------------------------------------------------
        # TOTAL
        # ----------------------------------------------------

        total = subtotal

        # ----------------------------------------------------
        # ORDER DATE
        # ----------------------------------------------------

        if not order_date:

            order_date = datetime.now().strftime(
                "%Y-%m-%d"
            )

        # ----------------------------------------------------
        # ORDER CATEGORY
        # ----------------------------------------------------

        if not category:

            categories = list(
                {
                    item["category"]
                    for item in validated_items
                    if item.get("category")
                }
            )

            category = ", ".join(
                categories
            )

        # ----------------------------------------------------
        # CREATE ORDER
        # ----------------------------------------------------

        new_order = Order(

            order_number=generate_order_number(),

            name=name,

            email=email,

            phone=phone,

            category=category,

            items=json.dumps(
                validated_items
            ),

            quantity=total_quantity,

            subtotal=round(
                subtotal,
                2
            ),

            total=round(
                total,
                2
            ),

            order_date=order_date,

            status="Pending"

        )

        try:

            db.session.add(
                new_order
            )

            # ------------------------------------------------
            # REDUCE STOCK
            # ------------------------------------------------

            for item in validated_items:

                product = db.session.get(
                    Product,
                    item["id"]
                )

                if product:

                    product.stock -= (
                        item["quantity"]
                    )

            db.session.commit()

            flash(
                f"Order {new_order.order_number} placed successfully."
            )

            return redirect(
                url_for("orders")
            )

        except Exception as error:

            db.session.rollback()

            print(
                "ORDER ERROR:",
                error
            )

            flash(
                "Unable to place your order. Please try again."
            )

            return redirect(
                url_for("orders")
            )

    # ========================================================
    # GET ORDERS
    # ========================================================

    user_orders = Order.query.filter_by(
        email=session.get(
            "user_email"
        )
    ).order_by(
        Order.created_at.desc()
    ).all()

    # ========================================================
    # AVAILABLE PRODUCTS
    # ========================================================

    products = Product.query.filter_by(
        active=True
    ).order_by(
        Product.category.asc(),
        Product.name.asc()
    ).all()

    return render_template(

        "orders.html",

        orders=user_orders,

        products=products

    )


# ============================================================
# ADMIN PRODUCTS
# ============================================================

@app.route(
    "/admin/products",
    methods=["GET", "POST"]
)
def admin_products():

    if not admin_required():

        return redirect(
            url_for("admin_login")
        )

    if request.method == "POST":

        name = clean(
            request.form.get(
                "name"
            )
        )

        category = clean(
            request.form.get(
                "category"
            )
        )

        description = clean(
            request.form.get(
                "description"
            )
        )

        try:

            price = float(
                request.form.get(
                    "price",
                    0
                )
            )

        except (
            ValueError,
            TypeError
        ):

            price = 0

        try:

            stock = int(
                request.form.get(
                    "stock",
                    0
                )
            )

        except (
            ValueError,
            TypeError
        ):

            stock = 0

        if price < 0:

            price = 0

        if stock < 0:

            stock = 0

        if not name or not category:

            flash(
                "Product name and category are required."
            )

            return redirect(
                url_for("admin_products")
            )

        product = Product(

            name=name,

            category=category,

            description=description,

            price=price,

            stock=stock,

            active=True

        )

        try:

            db.session.add(
                product
            )

            db.session.commit()

            flash(
                "Product added successfully."
            )

        except Exception as error:

            db.session.rollback()

            print(
                "PRODUCT ERROR:",
                error
            )

            flash(
                "Unable to add product."
            )

        return redirect(
            url_for("admin_products")
        )

    products = Product.query.order_by(
        Product.created_at.desc()
    ).all()

    return render_template(
        "admin-products.html",
        products=products
    )


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route(
    "/admin-login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        username = clean(
            request.form.get(
                "username"
            )
        )

        password = request.form.get(
            "password",
            ""
        )

        # ----------------------------------------------------
        # ADMIN 1
        # ----------------------------------------------------

        admin1_username = "kutosi"

        admin1_password = "extravaganza"

        # ----------------------------------------------------
        # ADMIN 2
        # ----------------------------------------------------

        admin2_username = "karanja"

        admin2_password = "extraordinary"

        if (

            (
                username == admin1_username
                and
                password == admin1_password
            )

            or

            (
                username == admin2_username
                and
                password == admin2_password
            )

        ):

            session["admin"] = True

            session["admin_name"] = (
                username
            )

            flash(
                "Admin login successful."
            )

            return redirect(
                url_for(
                    "admin_dashboard"
                )
            )

        flash(
            "Invalid admin credentials."
        )

        return redirect(
            url_for(
                "admin_login"
            )
        )

    return render_template(
        "admin-login.html"
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route(
    "/admin-dashboard"
)
def admin_dashboard():

    if not admin_required():

        flash(
            "Admin login required."
        )

        return redirect(
            url_for(
                "admin_login"
            )
        )

    users = User.query.order_by(
        User.created_at.desc()
    ).all()

    requests = NeedAssistant.query.order_by(
        NeedAssistant.created_at.desc()
    ).all()

    orders = Order.query.order_by(
        Order.created_at.desc()
    ).all()

    products = Product.query.order_by(
        Product.created_at.desc()
    ).all()

    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    total_users = User.query.count()

    total_requests = NeedAssistant.query.count()

    total_orders = Order.query.count()

    total_products = Product.query.count()

    pending_requests = NeedAssistant.query.filter_by(
        status="Pending"
    ).count()

    pending_orders = Order.query.filter_by(
        status="Pending"
    ).count()

    completed_orders = Order.query.filter_by(
        status="Completed"
    ).count()

    total_order_value = sum(

        float(
            order.total or 0
        )

        for order in orders

    )

    return render_template(

        "admin-dashboard.html",

        users=users,

        requests=requests,

        orders=orders,

        products=products,

        total_users=total_users,

        total_requests=total_requests,

        total_orders=total_orders,

        total_products=total_products,

        pending_requests=pending_requests,

        pending_orders=pending_orders,

        completed_orders=completed_orders,

        total_order_value=total_order_value

    )


# ============================================================
# DELETE ASSISTANT REQUEST
# ============================================================

@app.route(
    "/delete_request/<int:request_id>",
    methods=["POST"]
)
def delete_request(
    request_id
):

    if not admin_required():

        return redirect(
            url_for(
                "admin_login"
            )
        )

    req = NeedAssistant.query.get_or_404(
        request_id
    )

    if req.attachment:

        file_path = os.path.join(

            app.config[
                "UPLOAD_FOLDER"
            ],

            req.attachment

        )

        if os.path.exists(
            file_path
        ):

            try:

                os.remove(
                    file_path
                )

            except Exception:

                pass

    try:

        db.session.delete(
            req
        )

        db.session.commit()

        flash(
            "Assistant request deleted successfully."
        )

    except Exception as error:

        db.session.rollback()

        print(
            "DELETE REQUEST ERROR:",
            error
        )

        flash(
            "Unable to delete request."
        )

    return redirect(
        url_for(
            "admin_dashboard"
        )
    )


# ============================================================
# DELETE ORDER
# ============================================================

@app.route(
    "/delete_order/<int:order_id>",
    methods=["POST"]
)
def delete_order(
    order_id
):

    if not admin_required():

        return redirect(
            url_for(
                "admin_login"
            )
        )

    order = Order.query.get_or_404(
        order_id
    )

    try:

        db.session.delete(
            order
        )

        db.session.commit()

        flash(
            "Order deleted successfully."
        )

    except Exception as error:

        db.session.rollback()

        print(
            "DELETE ORDER ERROR:",
            error
        )

        flash(
            "Unable to delete order."
        )

    return redirect(
        url_for(
            "admin_dashboard"
        )
    )


# ============================================================
# UPDATE ORDER STATUS
# ============================================================

@app.route(
    "/update_order_status/<int:order_id>",
    methods=["POST"]
)
def update_order_status(
    order_id
):

    if not admin_required():

        return redirect(
            url_for(
                "admin_login"
            )
        )

    order = Order.query.get_or_404(
        order_id
    )

    new_status = clean(
        request.form.get(
            "status"
        )
    )

    allowed_statuses = [

        "Pending",

        "Confirmed",

        "Processing",

        "Ready",

        "Completed",

        "Cancelled"

    ]

    if new_status not in allowed_statuses:

        flash(
            "Invalid order status."
        )

        return redirect(
            url_for(
                "admin_dashboard"
            )
        )

    try:

        order.status = new_status

        db.session.commit()

        flash(
            f"Order {order.order_number or order.id} "
            f"updated to {new_status}."
        )

    except Exception as error:

        db.session.rollback()

        print(
            "ORDER STATUS ERROR:",
            error
        )

        flash(
            "Unable to update order status."
        )

    return redirect(
        url_for(
            "admin_dashboard"
        )
    )


# ============================================================
# UPDATE ASSISTANT REQUEST STATUS
# ============================================================

@app.route(
    "/update_request_status/<int:request_id>",
    methods=["POST"]
)
def update_request_status(
    request_id
):

    if not admin_required():

        return redirect(
            url_for(
                "admin_login"
            )
        )

    req = NeedAssistant.query.get_or_404(
        request_id
    )

    new_status = clean(
        request.form.get(
            "status"
        )
    )

    allowed_statuses = [

        "Pending",

        "Contacted",

        "In Progress",

        "Completed",

        "Cancelled"

    ]

    if new_status not in allowed_statuses:

        flash(
            "Invalid request status."
        )

        return redirect(
            url_for(
                "admin_dashboard"
            )
        )

    try:

        req.status = new_status

        db.session.commit()

        flash(
            "Assistant request status updated."
        )

    except Exception as error:

        db.session.rollback()

        print(
            "REQUEST STATUS ERROR:",
            error
        )

        flash(
            "Unable to update request status."
        )

    return redirect(
        url_for(
            "admin_dashboard"
        )
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route(
    "/logout"
)
def logout():

    session.clear()

    flash(
        "Logged out successfully."
    )

    return redirect(
        url_for("home")
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/health"
)
def health():

    try:

        db.session.execute(
            text("SELECT 1")
        )

        database_status = "connected"

    except Exception as error:

        database_status = "error"

        print(
            "HEALTH DATABASE ERROR:",
            error
        )

    return jsonify({

        "status": "ok",

        "application":
            "RAVTO GLOBAL LTD",

        "database":
            database_status,

        "time":
            datetime.utcnow().isoformat()

    })


# ============================================================
# DATABASE STATUS
# ============================================================
#
# This route is useful for checking the actual columns on
# Render while troubleshooting.
#
# It is protected by admin login.
#
# ============================================================

@app.route(
    "/admin/database-status"
)
def database_status():

    if not admin_required():

        return redirect(
            url_for(
                "admin_login"
            )
        )

    try:

        inspector = inspect(
            db.engine
        )

        result = {}

        for table_name in [
            "user",
            "need_assistant",
            "product",
            "order"
        ]:

            if table_name in inspector.get_table_names():

                result[table_name] = [

                    column["name"]

                    for column in inspector.get_columns(
                        table_name
                    )

                ]

            else:

                result[table_name] = []

        return jsonify({

            "status": "success",

            "database":
                db.engine.dialect.name,

            "tables":
                result

        })

    except Exception as error:

        return jsonify({

            "status": "error",

            "message":
                str(error)

        }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )
