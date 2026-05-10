from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'traveloop-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///traveloop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ============ MODELS ============

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    trips = db.relationship('Trip', backref='user', lazy=True, cascade='all, delete-orphan')

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_public = db.Column(db.Boolean, default=False)
    total_budget = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stops = db.relationship('Stop', backref='trip', lazy=True, cascade='all, delete-orphan', order_by='Stop.order')
    notes = db.relationship('Note', backref='trip', lazy=True, cascade='all, delete-orphan')
    checklist = db.relationship('ChecklistItem', backref='trip', lazy=True, cascade='all, delete-orphan')

class Stop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    order = db.Column(db.Integer, default=0)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    activities = db.relationship('Activity', backref='stop', lazy=True, cascade='all, delete-orphan')

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default='Sightseeing')
    cost = db.Column(db.Float, default=0.0)
    duration = db.Column(db.String(50))
    description = db.Column(db.Text)
    stop_id = db.Column(db.Integer, db.ForeignKey('stop.id'), nullable=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)

class ChecklistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default='General')
    is_packed = db.Column(db.Boolean, default=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============ CITIES DATA ============
CITIES = [
    {"name": "Mumbai", "country": "India", "cost_index": "Medium", "popularity": 95, "description": "City of Dreams"},
    {"name": "Delhi", "country": "India", "cost_index": "Low", "popularity": 90, "description": "Capital of India"},
    {"name": "Goa", "country": "India", "cost_index": "Medium", "popularity": 98, "description": "Beach Paradise"},
    {"name": "Jaipur", "country": "India", "cost_index": "Low", "popularity": 88, "description": "Pink City"},
    {"name": "Paris", "country": "France", "cost_index": "High", "popularity": 99, "description": "City of Love"},
    {"name": "Tokyo", "country": "Japan", "cost_index": "High", "popularity": 97, "description": "Land of Rising Sun"},
    {"name": "Bangkok", "country": "Thailand", "cost_index": "Low", "popularity": 94, "description": "Temple City"},
    {"name": "Dubai", "country": "UAE", "cost_index": "High", "popularity": 96, "description": "City of Gold"},
    {"name": "Singapore", "country": "Singapore", "cost_index": "High", "popularity": 93, "description": "Lion City"},
    {"name": "London", "country": "UK", "cost_index": "High", "popularity": 98, "description": "Historic Capital"},
    {"name": "New York", "country": "USA", "cost_index": "High", "popularity": 99, "description": "The Big Apple"},
    {"name": "Bali", "country": "Indonesia", "cost_index": "Low", "popularity": 96, "description": "Island of Gods"},
    {"name": "Rome", "country": "Italy", "cost_index": "Medium", "popularity": 95, "description": "Eternal City"},
    {"name": "Barcelona", "country": "Spain", "cost_index": "Medium", "popularity": 94, "description": "City of Gaudi"},
    {"name": "Sydney", "country": "Australia", "cost_index": "High", "popularity": 92, "description": "Harbour City"},
]

ACTIVITIES_DB = [
    {"name": "City Walking Tour", "category": "Sightseeing", "cost": 500, "duration": "3 hours"},
    {"name": "Local Food Tour", "category": "Food", "cost": 800, "duration": "2 hours"},
    {"name": "Museum Visit", "category": "Culture", "cost": 300, "duration": "2 hours"},
    {"name": "Beach Day", "category": "Adventure", "cost": 200, "duration": "Full day"},
    {"name": "Adventure Sports", "category": "Adventure", "cost": 2000, "duration": "4 hours"},
    {"name": "Shopping Tour", "category": "Shopping", "cost": 1000, "duration": "3 hours"},
    {"name": "Night Safari", "category": "Adventure", "cost": 1500, "duration": "3 hours"},
    {"name": "Cooking Class", "category": "Food", "cost": 1200, "duration": "3 hours"},
    {"name": "Temple Tour", "category": "Culture", "cost": 400, "duration": "2 hours"},
    {"name": "Boat Cruise", "category": "Sightseeing", "cost": 1800, "duration": "2 hours"},
    {"name": "Photography Walk", "category": "Sightseeing", "cost": 600, "duration": "2 hours"},
    {"name": "Yoga Session", "category": "Wellness", "cost": 500, "duration": "1.5 hours"},
]

# ============ AUTH ROUTES ============

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('signup'))
        user = User(name=name, email=email, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Welcome to Traveloop!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ============ DASHBOARD ============

@app.route('/dashboard')
@login_required
def dashboard():
    trips = Trip.query.filter_by(user_id=current_user.id).order_by(Trip.created_at.desc()).all()
    public_trips = Trip.query.filter_by(is_public=True).filter(Trip.user_id != current_user.id).limit(3).all()
    return render_template('dashboard.html', trips=trips, public_trips=public_trips, cities=CITIES[:6])

# ============ TRIP ROUTES ============

@app.route('/trips')
@login_required
def my_trips():
    trips = Trip.query.filter_by(user_id=current_user.id).order_by(Trip.created_at.desc()).all()
    return render_template('trips.html', trips=trips)

@app.route('/trip/create', methods=['GET', 'POST'])
@login_required
def create_trip():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date() if request.form.get('start_date') else None
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date() if request.form.get('end_date') else None
        is_public = True if request.form.get('is_public') else False
        trip = Trip(name=name, description=description, start_date=start_date, end_date=end_date, is_public=is_public, user_id=current_user.id)
        db.session.add(trip)
        db.session.commit()
        flash('Trip created!', 'success')
        return redirect(url_for('trip_detail', trip_id=trip.id))
    return render_template('create_trip.html')

@app.route('/trip/<int:trip_id>')
@login_required
def trip_detail(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    total_cost = sum(a.cost for s in trip.stops for a in s.activities)
    trip.total_budget = total_cost
    db.session.commit()
    cost_by_category = {}
    for stop in trip.stops:
        for act in stop.activities:
            cost_by_category[act.category] = cost_by_category.get(act.category, 0) + act.cost
    return render_template('trip_detail.html', trip=trip, total_cost=total_cost, cost_by_category=cost_by_category)

@app.route('/trip/<int:trip_id>/delete', methods=['POST'])
@login_required
def delete_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_trips'))
    db.session.delete(trip)
    db.session.commit()
    flash('Trip deleted!', 'success')
    return redirect(url_for('my_trips'))

# ============ STOP ROUTES ============

@app.route('/trip/<int:trip_id>/stop/add', methods=['POST'])
@login_required
def add_stop(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    city = request.form.get('city')
    country = request.form.get('country')
    start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date() if request.form.get('start_date') else None
    end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date() if request.form.get('end_date') else None
    order = len(trip.stops) + 1
    stop = Stop(city=city, country=country, start_date=start_date, end_date=end_date, order=order, trip_id=trip_id)
    db.session.add(stop)
    db.session.commit()
    flash(f'{city} added!', 'success')
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/stop/<int:stop_id>/delete', methods=['POST'])
@login_required
def delete_stop(stop_id):
    stop = Stop.query.get_or_404(stop_id)
    trip_id = stop.trip_id
    db.session.delete(stop)
    db.session.commit()
    return redirect(url_for('trip_detail', trip_id=trip_id))

# ============ ACTIVITY ROUTES ============

@app.route('/stop/<int:stop_id>/activity/add', methods=['POST'])
@login_required
def add_activity(stop_id):
    stop = Stop.query.get_or_404(stop_id)
    name = request.form.get('name')
    category = request.form.get('category', 'Sightseeing')
    cost = float(request.form.get('cost', 0))
    duration = request.form.get('duration', '')
    description = request.form.get('description', '')
    activity = Activity(name=name, category=category, cost=cost, duration=duration, description=description, stop_id=stop_id)
    db.session.add(activity)
    db.session.commit()
    return redirect(url_for('trip_detail', trip_id=stop.trip_id))

@app.route('/activity/<int:activity_id>/delete', methods=['POST'])
@login_required
def delete_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    trip_id = activity.stop.trip_id
    db.session.delete(activity)
    db.session.commit()
    return redirect(url_for('trip_detail', trip_id=trip_id))

# ============ NOTES ============

@app.route('/trip/<int:trip_id>/note/add', methods=['POST'])
@login_required
def add_note(trip_id):
    content = request.form.get('content')
    note = Note(content=content, trip_id=trip_id)
    db.session.add(note)
    db.session.commit()
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/note/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    trip_id = note.trip_id
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('trip_detail', trip_id=trip_id))

# ============ CHECKLIST ============

@app.route('/trip/<int:trip_id>/checklist/add', methods=['POST'])
@login_required
def add_checklist(trip_id):
    item = request.form.get('item')
    category = request.form.get('category', 'General')
    checklist_item = ChecklistItem(item=item, category=category, trip_id=trip_id)
    db.session.add(checklist_item)
    db.session.commit()
    return redirect(url_for('trip_detail', trip_id=trip_id))

@app.route('/checklist/<int:item_id>/toggle', methods=['POST'])
@login_required
def toggle_checklist(item_id):
    item = ChecklistItem.query.get_or_404(item_id)
    item.is_packed = not item.is_packed
    db.session.commit()
    return redirect(url_for('trip_detail', trip_id=item.trip_id))

@app.route('/checklist/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_checklist(item_id):
    item = ChecklistItem.query.get_or_404(item_id)
    trip_id = item.trip_id
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('trip_detail', trip_id=trip_id))

# ============ SEARCH ============

@app.route('/search/cities')
@login_required
def search_cities():
    query = request.args.get('q', '').lower()
    results = [c for c in CITIES if query in c['name'].lower() or query in c['country'].lower()] if query else CITIES
    return render_template('city_search.html', cities=results, query=query)

@app.route('/search/activities')
@login_required
def search_activities():
    query = request.args.get('q', '').lower()
    category = request.args.get('category', '')
    results = ACTIVITIES_DB
    if query:
        results = [a for a in results if query in a['name'].lower()]
    if category:
        results = [a for a in results if a['category'] == category]
    return render_template('activity_search.html', activities=results, query=query, category=category)

# ============ PUBLIC ITINERARY ============

@app.route('/public/<int:trip_id>')
def public_itinerary(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if not trip.is_public:
        flash('This trip is private', 'error')
        return redirect(url_for('index'))
    total_cost = sum(a.cost for s in trip.stops for a in s.activities)
    return render_template('public_itinerary.html', trip=trip, total_cost=total_cost)

# ============ PROFILE ============

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        db.session.commit()
        flash('Profile updated!', 'success')
    return render_template('profile.html')

# ============ BUDGET ============

@app.route('/trip/<int:trip_id>/budget')
@login_required
def budget(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    cost_by_category = {}
    cost_by_city = {}
    total = 0
    for stop in trip.stops:
        city_cost = 0
        for act in stop.activities:
            cost_by_category[act.category] = cost_by_category.get(act.category, 0) + act.cost
            city_cost += act.cost
            total += act.cost
        cost_by_city[stop.city] = city_cost
    days = (trip.end_date - trip.start_date).days if trip.start_date and trip.end_date else 1
    avg_per_day = total / max(days, 1)
    return render_template('budget.html', trip=trip, cost_by_category=cost_by_category, cost_by_city=cost_by_city, total=total, avg_per_day=avg_per_day)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
