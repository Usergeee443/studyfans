from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import or_

# Load environment variables
load_dotenv('config.env')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai_client = None
if OPENAI_API_KEY and OPENAI_API_KEY != 'your-openai-api-key-here' and len(OPENAI_API_KEY) > 20:
    env_backup = {}
    try:
        # Remove any proxy-related environment variables that might interfere
        import os as os_module
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        for var in proxy_vars:
            if var in os_module.environ:
                env_backup[var] = os_module.environ.pop(var)
        
        # Create OpenAI client with minimal configuration
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI client initialized")
        
        # Restore environment variables
        for var, value in env_backup.items():
            os_module.environ[var] = value
    except Exception as e:
        print(f"⚠️ OpenAI client initialization failed: {e}")
        openai_client = None
        # Restore environment variables even on error
        import os as os_module
        for var, value in env_backup.items():
            os_module.environ[var] = value
else:
    if not OPENAI_API_KEY or OPENAI_API_KEY == 'your-openai-api-key-here':
        print("⚠️ OpenAI API key not configured in config.env")
    else:
        print("⚠️ OpenAI API key appears to be invalid (too short)")

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
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder)
        # Create folder if it doesn't exist
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, filename)
        file.save(file_path)
        return f"uploads/{folder}/{filename}"
    return None

def create_slug(text):
    """Create URL-friendly slug from text"""
    import re
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip()
    # Remove special characters except hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    # Replace spaces and multiple hyphens with single hyphen
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug

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

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title_uz = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)
    title_ru = db.Column(db.String(200), nullable=False)
    title_tr = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content_uz = db.Column(db.Text, nullable=False)
    content_en = db.Column(db.Text, nullable=False)
    content_ru = db.Column(db.Text, nullable=False)
    content_tr = db.Column(db.Text, nullable=False)
    excerpt_uz = db.Column(db.Text)
    excerpt_en = db.Column(db.Text)
    excerpt_ru = db.Column(db.Text)
    excerpt_tr = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    author = db.Column(db.String(100), default='Study Fans')
    published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, lang='en'):
        return {
            'id': self.id,
            'title': getattr(self, f'title_{lang}'),
            'content': getattr(self, f'content_{lang}'),
            'excerpt': getattr(self, f'excerpt_{lang}') or '',
            'slug': self.slug,
            'image_url': self.image_url,
            'author': self.author,
            'published': self.published,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

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
    
    # Search universities
    query = University.query
    
    # Filter by language requirements if specified
    if language:
        # Search in language_requirements field for the selected language
        language_filters = []
        if language == 'English':
            language_filters.append(University.language_requirements.contains('IELTS'))
            language_filters.append(University.language_requirements.contains('TOEFL'))
        elif language == 'Turkish':
            language_filters.append(University.language_requirements.contains('TÖMER'))
            language_filters.append(University.language_requirements.contains('Turkish'))
        elif language == 'Uzbek':
            language_filters.append(University.language_requirements.contains('Uzbek'))
        elif language == 'Russian':
            language_filters.append(University.language_requirements.contains('Russian'))
        
        if language_filters:
            from sqlalchemy import or_
            query = query.filter(or_(*language_filters))
    
    # For degree and major, we'll return all universities for now
    # since we don't have specific program data in the University model
    # In the future, we can create a separate Programs table
    
    universities = query.all()
    
    # If no filters are applied, return all universities
    if not language and not degree and not major:
        universities = University.query.all()
    
    return render_template('search_results.html', universities=universities, lang=lang, 
                         degree=degree, language=language, major=major)

@app.route('/services')
def services():
    lang = request.args.get('lang', 'uz')
    return render_template('services.html', lang=lang)

@app.route('/service/<service_id>')
def service_detail(service_id):
    lang = request.args.get('lang', 'uz')
    return render_template('service_detail.html', service_id=service_id, lang=lang)

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

@app.route('/success-stories')
def success_stories():
    lang = request.args.get('lang', 'uz')
    return render_template('success_stories.html', lang=lang)

@app.route('/faq')
def faq():
    lang = request.args.get('lang', 'uz')
    return render_template('faq.html', lang=lang)

@app.route('/partner')
def partner():
    lang = request.args.get('lang', 'uz')
    return render_template('partner.html', lang=lang)

@app.route('/chat')
def chat():
    lang = request.args.get('lang', 'uz')
    return render_template('chat.html', lang=lang)

@app.route('/blog')
def blog():
    lang = request.args.get('lang', 'uz')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Show only published posts for regular users
    posts = BlogPost.query.filter_by(published=True).order_by(BlogPost.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('blog.html', posts=posts, lang=lang)

@app.route('/blog/<slug>')
def blog_detail(slug):
    lang = request.args.get('lang', 'uz')
    post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()
    
    # Get related posts (same category or recent)
    related_posts = BlogPost.query.filter(
        BlogPost.id != post.id,
        BlogPost.published == True
    ).order_by(BlogPost.created_at.desc()).limit(3).all()
    
    return render_template('blog_detail.html', post=post, related_posts=related_posts, lang=lang)

@app.route('/calculator')
def calculator():
    lang = request.args.get('lang', 'uz')
    return render_template('calculator.html', lang=lang)

@app.route('/video-gallery')
def video_gallery():
    lang = request.args.get('lang', 'uz')
    return render_template('video_gallery.html', lang=lang)

@app.route('/certificates')
def certificates():
    lang = request.args.get('lang', 'uz')
    return render_template('certificates.html', lang=lang)
    
    return render_template('blog_detail.html', post=post, related_posts=related_posts, lang=lang)

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
    
    universities = University.query.order_by(University.id.desc()).all()
    blogs = BlogPost.query.all()
    return render_template('admin/dashboard.html', universities=universities, blogs=blogs)

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

# Admin Blog Routes
@app.route('/admin/blog')
def admin_blog():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/blog.html', posts=posts)

@app.route('/admin/blog/add', methods=['GET', 'POST'])
def admin_add_blog():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        title_uz = request.form.get('title_uz')
        title_en = request.form.get('title_en')
        title_ru = request.form.get('title_ru')
        title_tr = request.form.get('title_tr')
        slug = request.form.get('slug') or title_en.lower().replace(' ', '-')
        content_uz = request.form.get('content_uz')
        content_en = request.form.get('content_en')
        content_ru = request.form.get('content_ru')
        content_tr = request.form.get('content_tr')
        excerpt_uz = request.form.get('excerpt_uz')
        excerpt_en = request.form.get('excerpt_en')
        excerpt_ru = request.form.get('excerpt_ru')
        excerpt_tr = request.form.get('excerpt_tr')
        author = request.form.get('author', 'Study Fans')
        published = bool(request.form.get('published'))
        
        # Handle image upload
        image_url = None
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                image_url = save_uploaded_file(image_file, 'blog')
        
        # Create slug if not provided
        if not slug:
            slug = create_slug(title_en)
        
        # Ensure slug is unique
        existing_post = BlogPost.query.filter_by(slug=slug).first()
        if existing_post:
            slug = f"{slug}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        post = BlogPost(
            title_uz=title_uz,
            title_en=title_en,
            title_ru=title_ru,
            title_tr=title_tr,
            slug=slug,
            content_uz=content_uz,
            content_en=content_en,
            content_ru=content_ru,
            content_tr=content_tr,
            excerpt_uz=excerpt_uz,
            excerpt_en=excerpt_en,
            excerpt_ru=excerpt_ru,
            excerpt_tr=excerpt_tr,
            image_url=image_url,
            author=author,
            published=published
        )
        
        db.session.add(post)
        db.session.commit()
        flash('Blog post muvaffaqiyatli qo\'shildi!', 'success')
        return redirect(url_for('admin_blog'))
    
    return render_template('admin/add_blog.html')

@app.route('/admin/blog/edit/<int:post_id>', methods=['GET', 'POST'])
def admin_edit_blog(post_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    post = BlogPost.query.get_or_404(post_id)
    
    if request.method == 'POST':
        post.title_uz = request.form.get('title_uz')
        post.title_en = request.form.get('title_en')
        post.title_ru = request.form.get('title_ru')
        post.title_tr = request.form.get('title_tr')
        new_slug = request.form.get('slug')
        if new_slug and new_slug != post.slug:
            existing_post = BlogPost.query.filter_by(slug=new_slug).first()
            if not existing_post or existing_post.id == post.id:
                post.slug = new_slug
        post.content_uz = request.form.get('content_uz')
        post.content_en = request.form.get('content_en')
        post.content_ru = request.form.get('content_ru')
        post.content_tr = request.form.get('content_tr')
        post.excerpt_uz = request.form.get('excerpt_uz')
        post.excerpt_en = request.form.get('excerpt_en')
        post.excerpt_ru = request.form.get('excerpt_ru')
        post.excerpt_tr = request.form.get('excerpt_tr')
        post.author = request.form.get('author', 'Study Fans')
        post.published = bool(request.form.get('published'))
        post.updated_at = datetime.utcnow()
        
        # Handle image upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                image_url = save_uploaded_file(image_file, 'blog')
                if image_url:
                    post.image_url = image_url
        
        db.session.commit()
        flash('Blog post muvaffaqiyatli yangilandi!', 'success')
        return redirect(url_for('admin_blog'))
    
    return render_template('admin/edit_blog.html', post=post)

@app.route('/admin/blog/delete/<int:post_id>')
def admin_delete_blog(post_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Blog post muvaffaqiyatli o\'chirildi!', 'success')
    return redirect(url_for('admin_blog'))


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

@app.route('/api/ai-recommendation', methods=['POST'])
def ai_recommendation():
    """AI orqali universitet tavsiya qilish"""
    try:
        data = request.get_json()
        lang = data.get('lang', 'uz')
        degree = data.get('degree', '')
        major = data.get('major', '')
        budget = data.get('budget', '')
        language = data.get('language', '')
        country = data.get('country', '')
        city = data.get('city', '')
        
        # Universitetlar bazasidan qidirish
        query = University.query
        
        # Country filter
        if country:
            country_filters = []
            if country == 'Turkey':
                country_filters.append(University.country_en == 'Turkey')
                country_filters.append(University.country_uz == 'Turkiya')
            elif country == 'Cyprus':
                country_filters.append(University.country_en == 'Cyprus')
                country_filters.append(University.country_uz == 'Kipr')
            elif country == 'Georgia':
                country_filters.append(University.country_en == 'Georgia')
                country_filters.append(University.country_uz == 'Gruziya')
            elif country == 'Malaysia':
                country_filters.append(University.country_en == 'Malaysia')
                country_filters.append(University.country_uz == 'Malayziya')
            
            if country_filters:
                query = query.filter(or_(*country_filters))
        
        # City filter
        if city:
            city_filters = []
            if lang == 'uz':
                city_filters.append(University.city_uz.contains(city))
            elif lang == 'ru':
                city_filters.append(University.city_ru.contains(city))
            elif lang == 'tr':
                city_filters.append(University.city_tr.contains(city))
            else:
                city_filters.append(University.city_en.contains(city))
            
            if city_filters:
                query = query.filter(or_(*city_filters))
        
        # Language filter
        if language:
            if language == 'English':
                query = query.filter(
                    or_(
                        University.language_requirements.contains('IELTS'),
                        University.language_requirements.contains('TOEFL'),
                        University.language_requirements.contains('English')
                    )
                )
            elif language == 'Turkish':
                query = query.filter(
                    or_(
                        University.language_requirements.contains('TÖMER'),
                        University.language_requirements.contains('Turkish')
                    )
                )
        
        # Budget filter - bu filterni keyinroq qo'llaymiz, chunki u juda qattiq
        budget_filter_applied = False
        if budget:
            try:
                # Extract numbers from budget string
                if '1500' in budget and '3000' in budget:
                    # 1500-3000 range
                    min_budget = 1500
                    max_budget = 3000
                elif '3000' in budget and '5000' in budget:
                    # 3000-5000 range
                    min_budget = 3000
                    max_budget = 5000
                elif '5000' in budget:
                    # 5000+ range
                    min_budget = 5000
                    max_budget = 999999
                else:
                    min_budget = None
                    max_budget = None
                
                if min_budget is not None:
                    # Budget filterni keyinroq qo'llaymiz - avval boshqa filterlar bilan qidiramiz
                    budget_filter_applied = True
            except Exception as e:
                print(f"Budget filter error: {e}")
                budget_filter_applied = False
        
        # Bazadan topilgan universitetlar
        matched_universities = query.limit(10).all()
        
        # Agar hech narsa topilmasa, filterlarni bosqichma-bosqich kamaytiramiz
        if not matched_universities:
            print("⚠️ No universities found with strict filters, trying with relaxed filters...")
            # City filterni olib tashlaymiz
            if city:
                query = University.query
                if country:
                    country_filters = []
                    if country == 'Turkey':
                        country_filters.append(University.country_en == 'Turkey')
                        country_filters.append(University.country_uz == 'Turkiya')
                    elif country == 'Cyprus':
                        country_filters.append(University.country_en == 'Cyprus')
                        country_filters.append(University.country_uz == 'Kipr')
                    elif country == 'Georgia':
                        country_filters.append(University.country_en == 'Georgia')
                        country_filters.append(University.country_uz == 'Gruziya')
                    elif country == 'Malaysia':
                        country_filters.append(University.country_en == 'Malaysia')
                        country_filters.append(University.country_uz == 'Malayziya')
                    
                    if country_filters:
                        query = query.filter(or_(*country_filters))
                
                # Language filter
                if language:
                    if language == 'English':
                        query = query.filter(
                            or_(
                                University.language_requirements.contains('IELTS'),
                                University.language_requirements.contains('TOEFL'),
                                University.language_requirements.contains('English')
                            )
                        )
                    elif language == 'Turkish':
                        query = query.filter(
                            or_(
                                University.language_requirements.contains('TÖMER'),
                                University.language_requirements.contains('Turkish')
                            )
                        )
                
                matched_universities = query.limit(10).all()
        
        # Agar hali ham bo'sh bo'lsa, faqat country filter bilan qidiramiz
        if not matched_universities and country:
            print("⚠️ Still no results, trying with country filter only...")
            query = University.query
            country_filters = []
            if country == 'Turkey':
                country_filters.append(University.country_en == 'Turkey')
                country_filters.append(University.country_uz == 'Turkiya')
            elif country == 'Cyprus':
                country_filters.append(University.country_en == 'Cyprus')
                country_filters.append(University.country_uz == 'Kipr')
            elif country == 'Georgia':
                country_filters.append(University.country_en == 'Georgia')
                country_filters.append(University.country_uz == 'Gruziya')
            elif country == 'Malaysia':
                country_filters.append(University.country_en == 'Malaysia')
                country_filters.append(University.country_uz == 'Malayziya')
            
            if country_filters:
                query = query.filter(or_(*country_filters))
                matched_universities = query.limit(10).all()
        
        # Agar hali ham bo'sh bo'lsa, barcha universitetlarni ko'rsatamiz
        if not matched_universities:
            print("⚠️ No universities found with any filters, showing all universities...")
            matched_universities = University.query.limit(10).all()
        
        print(f"📊 Found {len(matched_universities)} universities")
        
        # OpenAI API orqali tavsiya
        recommendations = []
        ai_analysis = ""
        
        if openai_client and matched_universities:
            try:
                # Universitetlar ma'lumotlarini tayyorlash
                universities_info = []
                for uni in matched_universities:
                    uni_dict = uni.to_dict(lang)
                    fee_min = uni_dict.get('tuition_fee_min', 'N/A')
                    fee_max = uni_dict.get('tuition_fee_max', 'N/A')
                    universities_info.append({
                        'name': uni_dict['name'],
                        'city': uni_dict['city'],
                        'country': uni_dict['country'],
                        'tuition_fee_min': fee_min,
                        'tuition_fee_max': fee_max,
                        'description': (uni_dict.get('description', '') or '')[:200]
                    })
                
                # Language-specific prompt
                if lang == 'uz':
                    system_prompt = "Siz professional ta'lim maslahatchisisiz. Universitetlarni tavsiya qilasiz."
                    user_prompt = f"""Quyidagi talablarga mos universitetlarni tavsiya qiling:

Talabalar:
- Ta'lim darajasi: {degree}
- Yo'nalish: {major}
- Byudjet: {budget}
- Til: {language}
- Davlat: {country}
- Shahar: {city if city else 'Har qanday'}

Mavjud universitetlar:
{chr(10).join([f"- {u['name']} ({u['city']}, {u['country']}) - {u['tuition_fee_min']}-{u['tuition_fee_max']}$" for u in universities_info[:5]])}

Eng mos 3 ta universitetni tavsiya qiling va har birini qisqacha tushuntiring. Javobni o'zbek tilida bering."""
                elif lang == 'ru':
                    system_prompt = "Вы профессиональный консультант по образованию. Вы рекомендуете университеты."
                    user_prompt = f"""Рекомендуйте университеты, соответствующие следующим требованиям:

Требования:
- Уровень образования: {degree}
- Направление: {major}
- Бюджет: {budget}
- Язык: {language}
- Страна: {country}
- Город: {city if city else 'Любой'}

Доступные университеты:
{chr(10).join([f"- {u['name']} ({u['city']}, {u['country']}) - {u['tuition_fee_min']}-{u['tuition_fee_max']}$" for u in universities_info[:5]])}

Рекомендуйте 3 наиболее подходящих университета и кратко объясните каждый. Ответьте на русском языке."""
                elif lang == 'tr':
                    system_prompt = "Profesyonel bir eğitim danışmanısınız. Üniversiteleri öneriyorsunuz."
                    user_prompt = f"""Aşağıdaki gereksinimlere uygun üniversiteleri önerin:

Gereksinimler:
- Eğitim seviyesi: {degree}
- Bölüm: {major}
- Bütçe: {budget}
- Dil: {language}
- Ülke: {country}
- Şehir: {city if city else 'Herhangi bir'}

Mevcut üniversiteler:
{chr(10).join([f"- {u['name']} ({u['city']}, {u['country']}) - {u['tuition_fee_min']}-{u['tuition_fee_max']}$" for u in universities_info[:5]])}

En uygun 3 üniversiteyi önerin ve her birini kısaca açıklayın. Türkçe cevap verin."""
                else:
                    system_prompt = "You are a professional education consultant. You recommend universities."
                    user_prompt = f"""Recommend universities that match the following requirements:

Requirements:
- Education level: {degree}
- Major: {major}
- Budget: {budget}
- Language: {language}
- Country: {country}
- City: {city if city else 'Any'}

Available universities:
{chr(10).join([f"- {u['name']} ({u['city']}, {u['country']}) - {u['tuition_fee_min']}-{u['tuition_fee_max']}$" for u in universities_info[:5]])}

Recommend the top 3 most suitable universities and briefly explain each. Answer in English."""
                
                print(f"🔍 Sending request to OpenAI API...")
                print(f"📊 Universities found: {len(universities_info)}")
                
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=800
                )
                
                if response and response.choices and len(response.choices) > 0:
                    ai_analysis = response.choices[0].message.content
                    print(f"✅ OpenAI API response received: {len(ai_analysis)} characters")
                else:
                    raise Exception("Empty response from OpenAI API")
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"❌ OpenAI API error: {e}")
                print(f"📋 Error details: {error_details}")
                
                # Language-specific error messages
                if lang == 'uz':
                    ai_analysis = "AI tahlil qilishda xatolik yuz berdi, lekin bazadan topilgan universitetlar ko'rsatilmoqda."
                elif lang == 'ru':
                    ai_analysis = "Произошла ошибка при анализе ИИ, но найденные университеты из базы данных отображаются."
                elif lang == 'tr':
                    ai_analysis = "AI analizinde hata oluştu, ancak veritabanından bulunan üniversiteler gösteriliyor."
                else:
                    ai_analysis = "Error in AI analysis, but universities found in database are shown."
        
        # Natijalarni tayyorlash
        result = {
            'success': True,
            'universities': [uni.to_dict(lang) for uni in matched_universities],
            'ai_analysis': ai_analysis,
            'count': len(matched_universities)
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """AI Chat API endpoint"""
    try:
        if not openai_client:
            return jsonify({
                'success': False,
                'error': 'OpenAI API is not configured'
            }), 500
        
        data = request.get_json()
        message = data.get('message', '')
        lang = data.get('lang', 'uz')
        conversation_history = data.get('history', [])
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        # System prompt based on language
        system_prompts = {
            'uz': """Siz Study Fans kompaniyasining yordamchi AI asistentisiz. Siz Turkiya, Kipr, Gruziya va Malayziyadagi universitetlar haqida ma'lumot berasiz, talabalarga yordam berasiz va maslahat berasiz. 
Javoblar qisqa, aniq va foydali bo'lishi kerak. Agar savol universitetlar yoki ta'lim bilan bog'liq bo'lmasa, buni tushuntirib, ta'lim masalalariga qaytishingizni so'rang.""",
            'ru': """Вы AI-ассистент компании Study Fans. Вы предоставляете информацию об университетах в Турции, на Кипре, в Грузии и Малайзии, помогаете студентам и даете советы.
Ответы должны быть краткими, точными и полезными. Если вопрос не связан с университетами или образованием, объясните это и попросите вернуться к вопросам образования.""",
            'tr': """Study Fans şirketinin yardımcı AI asistanısınız. Türkiye, Kıbrıs, Gürcistan ve Malezya'daki üniversiteler hakkında bilgi veriyorsunuz, öğrencilere yardımcı oluyorsunuz ve tavsiyelerde bulunuyorsunuz.
Yanıtlar kısa, net ve yararlı olmalıdır. Soru üniversiteler veya eğitimle ilgili değilse, bunu açıklayın ve eğitim konularına dönmelerini isteyin.""",
            'en': """You are an AI assistant for Study Fans company. You provide information about universities in Turkey, Cyprus, Georgia, and Malaysia, help students, and give advice.
Responses should be brief, accurate, and helpful. If the question is not related to universities or education, explain this and ask to return to education topics."""
        }
        
        system_prompt = system_prompts.get(lang, system_prompts['en'])
        
        # Build messages array
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Keep last 10 messages for context
            if msg.get('role') and msg.get('content'):
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'response': ai_response
        })
        
    except Exception as e:
        print(f"Error in chat API: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
                    language_requirements="IELTS 5.0+ yoki TOEFL 60+ yoki English",
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
                    language_requirements="IELTS 5.5+ yoki TOEFL 70+ yoki English, Russian",
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
                    language_requirements="IELTS 7.0+ yoki TOEFL 100+ yoki English",
                    admission_requirements="Diplom, transkript, til sertifikati, pasport, SAT/ACT",
                    application_deadline="1-yanvar",
                    scholarship_available=True,
                    accommodation_available=True
                ),
                University(
                    name_uz="Istanbul Texnik Universiteti",
                    name_en="Istanbul Technical University",
                    name_ru="Стамбульский технический университет",
                    name_tr="İstanbul Teknik Üniversitesi",
                    country_uz="Turkiya",
                    country_en="Turkey",
                    country_ru="Турция",
                    country_tr="Türkiye",
                    city_uz="Istanbul",
                    city_en="Istanbul",
                    city_ru="Стамбул",
                    city_tr="İstanbul",
                    description_uz="Turkiyaning eng nufuzli texnik universiteti. Muhandislik va texnologiya sohasida yetakchi.",
                    description_en="Turkey's most prestigious technical university. Leading in engineering and technology.",
                    description_ru="Самый престижный технический университет Турции. Лидер в области инженерии и технологий.",
                    description_tr="Türkiye'nin en prestijli teknik üniversitesi. Mühendislik ve teknoloji alanında öncü.",
                    website="https://itu.edu.tr",
                    ranking=3,
                    founded_year=1773,
                    university_type="Public",
                    student_count="35000+",
                    tuition_fee_min="1000",
                    tuition_fee_max="3000",
                    language_requirements="TÖMER B2+ yoki Turkish, English",
                    admission_requirements="Diplom, transkript, til sertifikati, pasport",
                    application_deadline="15-avgust",
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
