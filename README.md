# Study Fans - Educational Consulting Platform

Bu loyiha Python Flask, HTML va Tailwind CSS yordamida yaratilgan professional ta'lim maslahati platformasi.

## Xususiyatlar

### 🌐 Ko'p tilli qo'llab-quvvatlash
- **O'zbek tili** - Asosiy til
- **Ingliz tili** - Xalqaro til
- **Rus tili** - Mintaqaviy til

### 🎓 Asosiy funksiyalar
- **Kurslar qidiruv** - Daraja, til va mutaxassislik bo'yicha qidiruv
- **Universitetlar katalogi** - Hamkor universitetlar ro'yxati
- **Admin paneli** - Kurslar boshqaruvi
- **Responsive dizayn** - Barcha qurilmalarda ishlaydi

### 🔧 Admin funksiyalari
- **Login/Logout** - Xavfsiz kirish
- **Kurslar CRUD** - Qo'shish, tahrirlash, o'chirish
- **3 tilda ma'lumot** - Har bir kurs uchun 3 tilda tavsif
- **Dashboard** - Statistika va boshqaruv

## O'rnatish

### 1. Loyihani klonlash
```bash
git clone <repository-url>
cd studyfans
```

### 2. Virtual environment yaratish
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate     # Windows
```

### 3. Kerakli paketlarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4. Loyihani ishga tushirish
```bash
python app.py
```

Loyiha `http://localhost:5000` manzilida ishga tushadi.

## Foydalanish

### Admin kirish
- **URL**: `http://localhost:5000/admin`
- **Login**: `admin`
- **Parol**: `admin123`

### Asosiy sahifalar
- **Bosh sahifa**: `/`
- **Universitetlar**: `/universities`
- **Qidiruv natijalari**: `/search`
- **Admin paneli**: `/admin`

## Loyiha struktura

```
studyfans/
├── app.py                 # Asosiy Flask ilovasi
├── requirements.txt       # Python paketlari
├── README.md             # Loyiha hujjati
├── templates/            # HTML shablonlar
│   ├── base.html         # Asosiy shablon
│   ├── index.html        # Bosh sahifa
│   ├── universities.html # Universitetlar sahifasi
│   ├── search_results.html # Qidiruv natijalari
│   └── admin/            # Admin sahifalari
│       ├── login.html    # Admin kirish
│       ├── dashboard.html # Admin dashboard
│       ├── courses.html  # Kurslar ro'yxati
│       ├── add_course.html # Yangi kurs qo'shish
│       └── edit_course.html # Kursni tahrirlash
└── studyfans.db          # SQLite ma'lumotlar bazasi
```

## Texnologiyalar

- **Backend**: Python Flask
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Ma'lumotlar bazasi**: SQLite
- **Ikonlar**: Font Awesome
- **Animatsiyalar**: AOS (Animate On Scroll)

## API Endpoints

### Umumiy sahifalar
- `GET /` - Bosh sahifa
- `GET /universities` - Universitetlar sahifasi
- `GET /search` - Qidiruv natijalari

### Admin sahifalari
- `GET /admin` - Admin kirish sahifasi
- `POST /admin/login` - Admin kirish
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/courses` - Kurslar ro'yxati
- `GET /admin/courses/add` - Yangi kurs qo'shish
- `POST /admin/courses/add` - Yangi kurs saqlash
- `GET /admin/courses/edit/<id>` - Kursni tahrirlash
- `POST /admin/courses/edit/<id>` - Kurs o'zgarishlarini saqlash
- `GET /admin/courses/delete/<id>` - Kursni o'chirish
- `GET /admin/logout` - Admin chiqish

### API endpoints
- `GET /api/search` - Kurslar qidiruv API
- `GET /api/universities` - Universitetlar API

## Ma'lumotlar bazasi

### Kurslar (Course)
- `id` - Unikal identifikator
- `title_uz/en/ru` - Kurs nomi (3 tilda)
- `description_uz/en/ru` - Kurs tavsifi (3 tilda)
- `university_uz/en/ru` - Universitet nomi (3 tilda)
- `degree` - Daraja (Bachelor, Master, PhD)
- `language` - O'qish tili (English, Uzbek, Russian)
- `major` - Mutaxassislik
- `duration` - Davomiyligi
- `tuition_fee` - Tuition fee
- `created_at` - Yaratilgan vaqt

### Universitetlar (University)
- `id` - Unikal identifikator
- `name_uz/en/ru` - Universitet nomi (3 tilda)
- `country_uz/en/ru` - Mamlakat (3 tilda)
- `description_uz/en/ru` - Tavsif (3 tilda)
- `website` - Veb-sayt
- `logo_url` - Logo URL
- `ranking` - Reyting
- `created_at` - Yaratilgan vaqt

### Admin (Admin)
- `id` - Unikal identifikator
- `username` - Foydalanuvchi nomi
- `password_hash` - Parol hash
- `created_at` - Yaratilgan vaqt

## Rivojlantirish

### Yangi funksiya qo'shish
1. `app.py` faylida yangi route yarating
2. Kerakli template yarating
3. Ma'lumotlar bazasi modelini yangilang (agar kerak bo'lsa)

### Stil o'zgartirish
- Tailwind CSS klasslaridan foydalaning
- `base.html` faylida global stillarni o'zgartiring

## Xavfsizlik

- Admin parollari hash qilingan
- Session boshqaruvi
- CSRF himoyasi (kelajakda qo'shiladi)

## Yordam

Agar savollar bo'lsa, loyiha muallifiga murojaat qiling.

## Litsenziya

Bu loyiha MIT litsenziyasi ostida tarqatiladi.
