from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from sqlalchemy import values
from werkzeug.security import generate_password_hash, check_password_hash
import json

app = Flask(__name__)

app.config["SECRET_KEY"] = "finance_tracker_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            flash("Username already exists!")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful!")

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid username or password")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).all()

    income = sum(
        t.amount for t in transactions
        if t.transaction_type == "Income"
    )

    expense = sum(
        t.amount for t in transactions
        if t.transaction_type == "Expense"
    )

    balance = income - expense

    category_totals = {}

    for transaction in transactions:

        if transaction.transaction_type == "Expense":

            category_totals[
                transaction.category
            ] = category_totals.get(
                transaction.category,
                0
            ) + transaction.amount

    labels = list(category_totals.keys())
    values = list(category_totals.values())

    return render_template(
        "dashboard.html",
        transactions=transactions,
        income=income,
        expense=expense,
        balance=balance,
        labels=labels,
        values=values
    )
     
   


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_transaction():

    if request.method == "POST":

        amount = float(
            request.form["amount"]
        )

        category = request.form["category"]

        transaction_type = request.form["type"]

        transaction = Transaction(
            amount=amount,
            category=category,
            transaction_type=transaction_type,
            user_id=current_user.id
        )

        db.session.add(transaction)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template(
        "add_transaction.html"
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000)