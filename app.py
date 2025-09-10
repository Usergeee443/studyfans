from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = "7900459082:AAHKlcfwfRPSmCJwZk5dJ3hr1NHXQ5xOJew"
TELEGRAM_CHAT_ID = "6429299277"

def send_telegram_message(message):
    """Send message to Telegram bot"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

app = Flask(__name__)

# Database configuration - using SQLite for simplicity and deployment
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///studyfans.db'
print("✅ Using SQLite database: studyfans.db")

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db = SQLAlchemy(app)

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, folder='universities'):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to make filename unique
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)
        file.save(file_path)
        return f"uploads/{folder}/{filename}"
    return None

# Database Models
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title_uz = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)
    title_ru = db.Column(db.String(200), nullable=False)
    description_uz = db.Column(db.Text, nullable=False)
    description_en = db.Column(db.Text, nullable=False)
    description_ru = db.Column(db.Text, nullable=False)
    university_uz = db.Column(db.String(200), nullable=False)
    university_en = db.Column(db.String(200), nullable=False)
    university_ru = db.Column(db.String(200), nullable=False)
    degree = db.Column(db.String(50), nullable=False)  # Bachelor, Master, PhD
    language = db.Column(db.String(50), nullable=False)  # English, Uzbek, Russian
    major = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    tuition_fee = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self, lang='en'):
        return {
            'id': self.id,
            'title': getattr(self, f'title_{lang}'),
            'description': getattr(self, f'description_{lang}'),
            'university': getattr(self, f'university_{lang}'),
            'degree': self.degree,
            'language': self.language,
            'major': self.major,
            'duration': self.duration,
            'tuition_fee': self.tuition_fee
        }

class University(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_uz = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200), nullable=False)
    name_ru = db.Column(db.String(200), nullable=False)
    name_tr = db.Column(db.String(200), nullable=False)
    country_uz = db.Column(db.String(100), nullable=False)
    country_en = db.Column(db.String(100), nullable=False)
    country_ru = db.Column(db.String(100), nullable=False)
    country_tr = db.Column(db.String(100), nullable=False)
    city_uz = db.Column(db.String(100), nullable=False)
    city_en = db.Column(db.String(100), nullable=False)
    city_ru = db.Column(db.String(100), nullable=False)
    city_tr = db.Column(db.String(100), nullable=False)
    description_uz = db.Column(db.Text, nullable=False)
    description_en = db.Column(db.Text, nullable=False)
    description_ru = db.Column(db.Text, nullable=False)
    description_tr = db.Column(db.Text, nullable=False)
    website = db.Column(db.String(200))
    logo_url = db.Column(db.String(200))
    ranking = db.Column(db.Integer)
    founded_year = db.Column(db.Integer)
    university_type = db.Column(db.String(50))  # Public, Private
    student_count = db.Column(db.String(50))
    tuition_fee_min = db.Column(db.String(50))
    tuition_fee_max = db.Column(db.String(50))
    language_requirements = db.Column(db.Text)
    admission_requirements = db.Column(db.Text)
    application_deadline = db.Column(db.String(100))
    scholarship_available = db.Column(db.Boolean, default=False)
    accommodation_available = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self, lang='en'):
        return {
            'id': self.id,
            'name': getattr(self, f'name_{lang}'),
            'country': getattr(self, f'country_{lang}'),
            'city': getattr(self, f'city_{lang}'),
            'description': getattr(self, f'description_{lang}'),
            'website': self.website,
            'logo_url': self.logo_url,
            'ranking': self.ranking,
            'founded_year': self.founded_year,
            'university_type': self.university_type,
            'student_count': self.student_count,
            'tuition_fee_min': self.tuition_fee_min,
            'tuition_fee_max': self.tuition_fee_max,
            'language_requirements': self.language_requirements,
            'admission_requirements': self.admission_requirements,
            'application_deadline': self.application_deadline,
            'scholarship_available': self.scholarship_available,
            'accommodation_available': self.accommodation_available
        }

class UniversityApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    university_id = db.Column(db.Integer, db.ForeignKey('university.id'), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(20), nullable=False)  # Male, Female
    country = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    university = db.relationship('University', backref=db.backref('applications', lazy=True))

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    return render_template('index.html', lang=lang)

@app.route('/universities')
def universities():
    lang = request.args.get('lang', 'en')
    universities = University.query.all()
    return render_template('universities.html', universities=universities, lang=lang)

@app.route('/university/<int:university_id>')
def university_detail(university_id):
    lang = request.args.get('lang', 'en')
    university = University.query.get_or_404(university_id)
    # Get courses for this university
    courses = Course.query.filter(
        (Course.university_uz == university.name_uz) |
        (Course.university_en == university.name_en) |
        (Course.university_ru == university.name_ru)
    ).all()
    return render_template('university_detail.html', university=university, courses=courses, lang=lang)

@app.route('/search')
def search():
    lang = request.args.get('lang', 'en')
    degree = request.args.get('degree', '')
    language = request.args.get('language', '')
    major = request.args.get('major', '')
    
    # Search universities instead of courses
    query = University.query
    
    # Filter by language requirements if specified
    if language:
        query = query.filter(University.language_requirements.contains(language))
    
    universities = query.all()
    return render_template('search_results.html', universities=universities, lang=lang, 
                         degree=degree, language=language, major=major)

@app.route('/services')
def services():
    lang = request.args.get('lang', 'uz')
    return render_template('services.html', lang=lang)

@app.route('/about')
def about():
    lang = request.args.get('lang', 'uz')
    return render_template('about.html', lang=lang)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    lang = request.args.get('lang', 'uz')
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Send to Telegram
        telegram_message = f"""
<b>📞 Yangi Aloqa Xabari</b>

👤 <b>Ism:</b> {name}
📧 <b>Email:</b> {email}
📱 <b>Telefon:</b> {phone}
📝 <b>Mavzu:</b> {subject}

💬 <b>Xabar:</b>
{message}

⏰ <b>Vaqt:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        if send_telegram_message(telegram_message):
            return redirect(url_for('contact', lang=lang, success='true'))
        else:
            return redirect(url_for('contact', lang=lang, error='true'))
    
    return render_template('contact.html', lang=lang)

@app.route('/university/<int:university_id>/apply', methods=['POST'])
def apply_university(university_id):
    lang = request.form.get('lang', request.args.get('lang', 'uz'))
    university = University.query.get_or_404(university_id)
    
    full_name = request.form.get('full_name')
    gender = request.form.get('gender')
    country = request.form.get('country')
    region = request.form.get('region')
    phone_number = request.form.get('phone_number')
    
    if not all([full_name, gender, country, region, phone_number]):
        flash('Barcha maydonlarni to\'ldiring', 'error')
        return redirect(url_for('university_detail', university_id=university_id, lang=lang))
    
    # Create application
    application = UniversityApplication(
        university_id=university_id,
        full_name=full_name,
        gender=gender,
        country=country,
        region=region,
        phone_number=phone_number
    )
    
    db.session.add(application)
    db.session.commit()
    
    # Send to Telegram bot
    university_name = getattr(university, f'name_{lang}', university.name_en)
    telegram_message = f"""
<b>🎓 Yangi Universitet Arizasi</b>

🏫 <b>Universitet:</b> {university_name}
👤 <b>Ism:</b> {full_name}
⚧ <b>Jins:</b> {gender}
🌍 <b>Mamlakat:</b> {country}
📍 <b>Viloyat:</b> {region}
📱 <b>Telefon:</b> {phone_number}

⏰ <b>Vaqt:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    if send_telegram_message(telegram_message):
        return redirect(url_for('university_detail', university_id=university_id, lang=lang, success='true'))
    else:
        return redirect(url_for('university_detail', university_id=university_id, lang=lang, error='true'))

@app.route('/admin')
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    
    admin = Admin.query.filter_by(username=username).first()
    
    if admin and check_password_hash(admin.password_hash, password):
        session['admin_logged_in'] = True
        session['admin_username'] = username
        flash('Muvaffaqiyatli kirildi!', 'success')
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Noto\'g\'ri login yoki parol!', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    courses = Course.query.all()
    universities = University.query.all()
    return render_template('admin/dashboard.html', courses=courses, universities=universities)

@app.route('/admin/universities')
def admin_universities():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    universities = University.query.all()
    return render_template('admin/universities.html', universities=universities)

@app.route('/admin/universities/add', methods=['GET', 'POST'])
def admin_add_university():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        # Handle logo upload
        logo_url = None
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename:
                logo_url = save_uploaded_file(logo_file, 'universities')
        
        university = University(
            name_uz=request.form.get('name_uz'),
            name_en=request.form.get('name_en'),
            name_ru=request.form.get('name_ru'),
            name_tr=request.form.get('name_tr'),
            country_uz=request.form.get('country_uz'),
            country_en=request.form.get('country_en'),
            country_ru=request.form.get('country_ru'),
            country_tr=request.form.get('country_tr'),
            city_uz=request.form.get('city_uz'),
            city_en=request.form.get('city_en'),
            city_ru=request.form.get('city_ru'),
            city_tr=request.form.get('city_tr'),
            description_uz=request.form.get('description_uz'),
            description_en=request.form.get('description_en'),
            description_ru=request.form.get('description_ru'),
            description_tr=request.form.get('description_tr'),
            website=request.form.get('website'),
            ranking=request.form.get('ranking'),
            logo_url=logo_url,
            founded_year=request.form.get('founded_year'),
            university_type=request.form.get('university_type'),
            student_count=request.form.get('student_count'),
            tuition_fee_min=request.form.get('tuition_fee_min'),
            tuition_fee_max=request.form.get('tuition_fee_max'),
            language_requirements=request.form.get('language_requirements'),
            admission_requirements=request.form.get('admission_requirements'),
            application_deadline=request.form.get('application_deadline'),
            scholarship_available=bool(request.form.get('scholarship_available')),
            accommodation_available=bool(request.form.get('accommodation_available'))
        )
        
        db.session.add(university)
        db.session.commit()
        flash('Universitet muvaffaqiyatli qo\'shildi!', 'success')
        return redirect(url_for('admin_universities'))
    
    return render_template('admin/add_university.html')

@app.route('/admin/universities/edit/<int:university_id>', methods=['GET', 'POST'])
def admin_edit_university(university_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    university = University.query.get_or_404(university_id)
    
    if request.method == 'POST':
        # Handle logo upload
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename:
                logo_url = save_uploaded_file(logo_file, 'universities')
                if logo_url:
                    university.logo_url = logo_url
        
        university.name_uz = request.form.get('name_uz')
        university.name_en = request.form.get('name_en')
        university.name_ru = request.form.get('name_ru')
        university.name_tr = request.form.get('name_tr')
        university.country_uz = request.form.get('country_uz')
        university.country_en = request.form.get('country_en')
        university.country_ru = request.form.get('country_ru')
        university.country_tr = request.form.get('country_tr')
        university.city_uz = request.form.get('city_uz')
        university.city_en = request.form.get('city_en')
        university.city_ru = request.form.get('city_ru')
        university.city_tr = request.form.get('city_tr')
        university.description_uz = request.form.get('description_uz')
        university.description_en = request.form.get('description_en')
        university.description_ru = request.form.get('description_ru')
        university.description_tr = request.form.get('description_tr')
        university.website = request.form.get('website')
        university.ranking = request.form.get('ranking')
        university.founded_year = request.form.get('founded_year')
        university.university_type = request.form.get('university_type')
        university.student_count = request.form.get('student_count')
        university.tuition_fee_min = request.form.get('tuition_fee_min')
        university.tuition_fee_max = request.form.get('tuition_fee_max')
        university.language_requirements = request.form.get('language_requirements')
        university.admission_requirements = request.form.get('admission_requirements')
        university.application_deadline = request.form.get('application_deadline')
        university.scholarship_available = bool(request.form.get('scholarship_available'))
        university.accommodation_available = bool(request.form.get('accommodation_available'))
        
        db.session.commit()
        flash('Universitet muvaffaqiyatli yangilandi!', 'success')
        return redirect(url_for('admin_universities'))
    
    return render_template('admin/edit_university.html', university=university)

@app.route('/admin/universities/delete/<int:university_id>')
def admin_delete_university(university_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    university = University.query.get_or_404(university_id)
    db.session.delete(university)
    db.session.commit()
    flash('Universitet muvaffaqiyatli o\'chirildi!', 'success')
    return redirect(url_for('admin_universities'))


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Muvaffaqiyatli chiqildi!', 'success')
    return redirect(url_for('admin_login'))

# API Routes for AJAX
@app.route('/api/search')
def api_search():
    lang = request.args.get('lang', 'en')
    degree = request.args.get('degree', '')
    language = request.args.get('language', '')
    major = request.args.get('major', '')
    
    query = Course.query
    
    if degree:
        query = query.filter(Course.degree == degree)
    if language:
        query = query.filter(Course.language == language)
    if major:
        query = query.filter(Course.major.contains(major))
    
    courses = query.all()
    return jsonify([course.to_dict(lang) for course in courses])

@app.route('/api/universities')
def api_universities():
    lang = request.args.get('lang', 'en')
    universities = University.query.all()
    return jsonify([university.to_dict(lang) for university in universities])

@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Template filter for URL query parameters
@app.template_filter('replace_query_param')
def replace_query_param(url, param, value):
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    query_params[param] = [value]
    new_query = urlencode(query_params, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

# Initialize database and create admin user
def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default admin user if not exists
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: username=admin, password=admin123")
        
        # Add sample data if database is empty
        if Course.query.count() == 0:
            sample_courses = [
                Course(
                    title_uz="Kompyuter Fanlari Bakalavri",
                    title_en="Bachelor of Computer Science",
                    title_ru="Бакалавр компьютерных наук",
                    description_uz="Zamonaviy dasturlash tillari va texnologiyalari bo'yicha to'liq ta'lim",
                    description_en="Complete education in modern programming languages and technologies",
                    description_ru="Полное образование в области современных языков программирования и технологий",
                    university_uz="Toshkent Axborot Texnologiyalari Universiteti",
                    university_en="Tashkent University of Information Technologies",
                    university_ru="Ташкентский университет информационных технологий",
                    degree="Bachelor",
                    language="Uzbek",
                    major="Computer Science",
                    duration="4 yil",
                    tuition_fee="5,000,000 so'm/yil"
                ),
                Course(
                    title_uz="Biznes Boshqaruvi Magistri",
                    title_en="Master of Business Administration",
                    title_ru="Магистр делового администрирования",
                    description_uz="Zamonaviy biznes strategiyalari va boshqaruv usullari",
                    description_en="Modern business strategies and management methods",
                    description_ru="Современные бизнес-стратегии и методы управления",
                    university_uz="O'zbekiston Milliy Universiteti",
                    university_en="National University of Uzbekistan",
                    university_ru="Национальный университет Узбекистана",
                    degree="Master",
                    language="English",
                    major="Business Administration",
                    duration="2 yil",
                    tuition_fee="$3,000/yil"
                )
            ]
            
            for course in sample_courses:
                db.session.add(course)
            
            db.session.commit()
            print("Sample courses added to database")
        
        # Add sample universities if database is empty
        if University.query.count() == 0:
            sample_universities = [
                University(
                    name_uz="Toshkent Axborot Texnologiyalari Universiteti",
                    name_en="Tashkent University of Information Technologies",
                    name_ru="Ташкентский университет информационных технологий",
                    name_tr="Taşkent Bilgi Teknolojileri Üniversitesi",
                    country_uz="O'zbekiston",
                    country_en="Uzbekistan",
                    country_ru="Узбекистан",
                    country_tr="Özbekistan",
                    city_uz="Toshkent",
                    city_en="Tashkent",
                    city_ru="Ташкент",
                    city_tr="Taşkent",
                    description_uz="IT sohasida yetakchi universitet. Zamonaviy dasturlash va texnologiyalar bo'yicha ta'lim beradi.",
                    description_en="Leading university in IT field. Provides education in modern programming and technologies.",
                    description_ru="Ведущий университет в области ИТ. Обеспечивает образование в области современного программирования и технологий.",
                    description_tr="BT alanında önde gelen üniversite. Modern programlama ve teknolojiler konusunda eğitim verir.",
                    website="https://tuit.uz",
                    ranking=1,
                    founded_year=1955,
                    university_type="Public",
                    student_count="15000+",
                    tuition_fee_min="2000",
                    tuition_fee_max="5000",
                    language_requirements="IELTS 5.0+ yoki TOEFL 60+",
                    admission_requirements="Diplom, transkript, til sertifikati, pasport",
                    application_deadline="1-avgust",
                    scholarship_available=True,
                    accommodation_available=True
                ),
                University(
                    name_uz="O'zbekiston Milliy Universiteti",
                    name_en="National University of Uzbekistan",
                    name_ru="Национальный университет Узбекистана",
                    name_tr="Özbekistan Milli Üniversitesi",
                    country_uz="O'zbekiston",
                    country_en="Uzbekistan",
                    country_ru="Узбекистан",
                    country_tr="Özbekistan",
                    city_uz="Toshkent",
                    city_en="Tashkent",
                    city_ru="Ташкент",
                    city_tr="Taşkent",
                    description_uz="O'zbekistonning eng nufuzli universiteti. Barcha sohalarda yuqori sifatli ta'lim beradi.",
                    description_en="Most prestigious university in Uzbekistan. Provides high-quality education in all fields.",
                    description_ru="Самый престижный университет Узбекистана. Обеспечивает качественное образование во всех областях.",
                    description_tr="Özbekistan'ın en prestijli üniversitesi. Tüm alanlarda yüksek kaliteli eğitim verir.",
                    website="https://nuu.uz",
                    ranking=2,
                    founded_year=1918,
                    university_type="Public",
                    student_count="50000+",
                    tuition_fee_min="500",
                    tuition_fee_max="2000",
                    language_requirements="IELTS 5.5+ yoki TOEFL 70+",
                    admission_requirements="Diplom, transkript, til sertifikati, pasport",
                    application_deadline="15-iyul",
                    scholarship_available=True,
                    accommodation_available=True
                ),
                University(
                    name_uz="Harvard Universiteti",
                    name_en="Harvard University",
                    name_ru="Гарвардский университет",
                    name_tr="Harvard Üniversitesi",
                    country_uz="AQSH",
                    country_en="United States",
                    country_ru="США",
                    country_tr="Amerika Birleşik Devletleri",
                    city_uz="Kembrij",
                    city_en="Cambridge",
                    city_ru="Кембридж",
                    city_tr="Cambridge",
                    description_uz="Dunyoning eng nufuzli universitetlaridan biri. 1636-yilda tashkil etilgan.",
                    description_en="One of the world's most prestigious universities. Founded in 1636.",
                    description_ru="Один из самых престижных университетов мира. Основан в 1636 году.",
                    description_tr="Dünyanın en prestijli üniversitelerinden biri. 1636 yılında kurulmuştur.",
                    website="https://harvard.edu",
                    ranking=1,
                    founded_year=1636,
                    university_type="Private",
                    student_count="23000+",
                    tuition_fee_min="50000",
                    tuition_fee_max="60000",
                    language_requirements="IELTS 7.0+ yoki TOEFL 100+",
                    admission_requirements="Diplom, transkript, til sertifikati, pasport, SAT/ACT",
                    application_deadline="1-yanvar",
                    scholarship_available=True,
                    accommodation_available=True
                )
            ]
            
            for university in sample_universities:
                db.session.add(university)
            
            db.session.commit()
            print("Sample universities added to database")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
