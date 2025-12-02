from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "icloudhomes_secret_key"

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "tickets.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ---------------- Database ----------------
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    mobile = db.Column(db.String(20))
    location = db.Column(db.String(200)) # <--- NEW LOCATION FIELD
    issue = db.Column(db.String(500))
    priority = db.Column(db.String(10), default="Medium")
    status = db.Column(db.String(20), default="Open")
    created_at = db.Column(db.DateTime, default=datetime.now)

with app.app_context():
    db.create_all()

# ---------------- SECURITY GATEKEEPER ----------------
@app.before_request
def require_login():
    allowed_routes = ['site_login', 'admin_login', 'admin_dashboard', 'admin_logout', 'static']
    if request.endpoint not in allowed_routes and 'staff_logged_in' not in session and 'admin' not in session:
        return redirect(url_for('site_login'))

# ---------------- Routes ----------------
@app.route("/login", methods=["GET", "POST"])
def site_login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "staff" and password == "1234":
            session["staff_logged_in"] = True
            return redirect(url_for("index"))
        else:
            error = "Invalid Staff Credentials"
    return render_template("site_login.html", error=error)

@app.route("/logout")
def site_logout():
    session.pop("staff_logged_in", None)
    return redirect(url_for("site_login"))

@app.route("/")
def index():
    return render_template("index.html", company="iCloudhomes")

@app.route("/new", methods=["GET", "POST"])
def new_ticket():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        location = request.form["location"] # <--- GET LOCATION
        issue = request.form["issue"]
        priority = request.form["priority"]
        
        ticket = Ticket(name=name, email=email, mobile=mobile, location=location, issue=issue, priority=priority)
        db.session.add(ticket)
        db.session.commit()
        return redirect(url_for("user_tickets", email=email))
    return render_template("new.html")

@app.route("/tickets/<email>")
def user_tickets(email):
    tickets = Ticket.query.filter_by(email=email).all()
    return render_template("ticket.html", tickets=tickets, email=email)

# ---------------- Admin ----------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Invalid credentials"
    return render_template("login.html", error=error)

@app.route("/admin/dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    
    search_query = request.args.get('search')
    if search_query:
        # Added Location to Search Logic
        tickets = Ticket.query.filter(
            or_(
                Ticket.name.contains(search_query),
                Ticket.email.contains(search_query),
                Ticket.mobile.contains(search_query),
                Ticket.location.contains(search_query), # <--- Search Location
                Ticket.issue.contains(search_query)
            )
        ).order_by(Ticket.created_at.desc()).all()
    else:
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    
    if request.method == "POST":
        ticket_id = int(request.form["ticket_id"])
        ticket = Ticket.query.get(ticket_id)
        ticket.status = request.form["status"]
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
        
    return render_template("admin_dashboard.html", tickets=tickets)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(debug=True)