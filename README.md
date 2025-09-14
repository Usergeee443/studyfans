# StudyFans - Universitet Qidiruv Platformasi

Bu platforma talabalar uchun dunyodagi universitetlarni qidirish va ularga ariza berish imkoniyatini beradi.

## Xususiyatlar

- 🌍 4 tilda qo'llab-quvvatlash (O'zbek, Ingliz, Rus, Turk)
- 🎓 Universitetlar ro'yxati va batafsil ma'lumotlar
- 🔍 Kuchli qidiruv tizimi
- 📱 Responsive dizayn
- 🔐 Admin paneli
- 📊 Universitet ma'lumotlarini boshqarish

## Texnologiyalar

- **Backend:** Flask (Python)
- **Database:** SQLite
- **Frontend:** HTML, CSS (Tailwind), JavaScript
- **Deployment:** Render.com

## O'rnatish

1. Repository ni klonlang:
```bash
git clone <repository-url>
cd studyfans
```

2. Virtual environment yarating:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate  # Windows
```

3. Kerakli paketlarni o'rnating:
```bash
pip install -r requirements.txt
```

4. Ilovani ishga tushiring:
```bash
python app.py
```

5. Brauzerda oching: `http://localhost:5000`

## Admin Panel

- URL: `/admin`
- Login: `admin`
- Parol: `admin123`

## Deployment (Render.com)

1. GitHub ga push qiling
2. Render.com da yangi Web Service yarating
3. Repository ni ulang
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app`

## Database

SQLite fayli avtomatik yaratiladi va `studyfans.db` nomi bilan saqlanadi.

## Litsenziya

MIT License



