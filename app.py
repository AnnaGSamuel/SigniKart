# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///signikart.db'
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    eco_score = db.Column(db.Integer, nullable=False)  # Score from 1-100
    certifications = db.Column(db.String(200))  # Comma-separated certification names
    co2_impact = db.Column(db.Float)  # CO2 saved per unit in kg
    water_impact = db.Column(db.Float)  # Water saved per unit in liters
    waste_impact = db.Column(db.Float)  # Waste reduced per unit in kg

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    purchase_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Calculate environmental impact
    def calculate_impact(self):
        product = Product.query.get(self.product_id)
        return {
            'co2_saved': product.co2_impact * self.quantity,
            'water_saved': product.water_impact * self.quantity,
            'waste_reduced': product.waste_impact * self.quantity
        }

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    likes = db.Column(db.Integer, default=0)

# Sample product data (in a real app, this would come from a database)
sample_products = [
    {
        'id': 1,
        'title': 'Organic Cotton T-Shirt',
        'image_url': '/static/images/tshirt.jpg',  # You'll need to add these images
        'price': 599.99,
        'eco_score': 95,
        'description': 'Made from 100% organic cotton, this t-shirt is both comfortable and sustainable.',
        'certifications': 'GOTS,Fair Trade',
        'co2_impact': 2.5,
        'water_impact': 300,
        'waste_impact': 0.5
    },
    {
        'id': 2,
        'title': 'Bamboo Water Bottle',
        'image_url': '/static/images/bottle.jpg',
        'price': 299.99,
        'eco_score': 90,
        'description': 'Reusable bamboo water bottle with stainless steel interior.',
        'certifications': 'Plastic Free,BPA Free',
        'co2_impact': 1.8,
        'water_impact': 250,
        'waste_impact': 0.8
    },
    {
        'id': 3,
        'title': 'Recycled Paper Notebook',
        'image_url': '/static/images/notebook.jpg',
        'price': 149.99,
        'eco_score': 85,
        'description': 'Handcrafted notebook made from 100% recycled paper.',
        'certifications': 'FSC,Recycled',
        'co2_impact': 1.2,
        'water_impact': 150,
        'waste_impact': 0.3
    }
]

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
            
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

'''@app.route('/products')
def products():
    return render_template('products.html', products=sample_products)'''

# Additional routes
@app.route('/products')
def products():
    #products = Product.query.all()
    return render_template('products.html', products=sample_products)

'''@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)'''

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if product is None:
        abort(404)
    return render_template('product_detail.html', product=product)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    purchases = Purchase.query.filter_by(user_id=user.id).all()
    
    # Calculate total impact
    total_impact = {
        'co2_saved': 0,
        'water_saved': 0,
        'waste_reduced': 0
    }
    
    for purchase in purchases:
        impact = purchase.calculate_impact()
        total_impact['co2_saved'] += impact['co2_saved']
        total_impact['water_saved'] += impact['water_saved']
        total_impact['waste_reduced'] += impact['waste_reduced']
    
    return render_template('profile.html', user=user, impact=total_impact, purchases=purchases)

@app.route('/community')
def community():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('community.html', posts=posts)

@app.route('/create_post', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    content = request.form.get('content')
    image_url = request.form.get('image_url')
    
    post = Post(
        user_id=session['user_id'],
        content=content,
        image_url=image_url
    )
    
    db.session.add(post)
    db.session.commit()
    
    return redirect(url_for('community'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)