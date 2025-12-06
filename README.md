# Typing Trainer Platform

Geeks Andijan o'quvchilari uchun typing tezligi va code typing malakasini oshirishga mo'ljallangan o'quv platforma.

## Texnologiyalar

- **Backend**: Django 6.0
- **Frontend**: HTML + TailwindCSS (CDN)
- **Database**: SQLite
- **Syntax Highlighting**: highlight.js

## Funksiyalar

### Foydalanuvchi rollari

1. **Oddiy User**
   - Ro'yxatdan o'tish / Kirish
   - Oddiy va murakkab matnlar bilan mashq qilish
   - Code mode orqali kod yozish mashqlari
   - Musobaqalarga qo'shilish
   - Shaxsiy statistikani ko'rish
   - Reytingda o'z o'rnini ko'rish

2. **Manager (O'qituvchi/Admin)**
   - Musobaqa yaratish
   - Musobaqaga userlarni qo'shish
   - Musobaqa davomida natijalarni real vaqtda ko'rish
   - Musobaqani yopish
   - Reytinglarni nazorat qilish

### Platforma bo'limlari

1. **Dashboard**
   - WPM (Words Per Minute)
   - Accuracy %
   - Mashq o'tgan vaqtlar
   - Oxirgi 10 ta natija
   - Musobaqalarga takliflar

2. **Typing Modes**
   - Oddiy matn (Easy/Hard)
   - Kod yozish (Python, JavaScript, C++, Java)
   - Syntax highlight
   - Real-time statistikalar

3. **Musobaqalar**
   - 1v1 duel
   - Guruh musobaqalari (3-20 user)
   - Real-time progress
   - Leaderboard

4. **Reytinglar**
   - Umumiy WPM reytingi
   - Kod bo'yicha WPM reytingi
   - Accuracy reytingi
   - Haftalik / oylik / barcha vaqt

## O'rnatish

1. Virtual environment yaratish:
```bash
python -m venv venv
```

2. Virtual environmentni faollashtirish:
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Kerakli paketlarni o'rnatish:
```bash
pip install -r requirements.txt
```

4. Migrationslarni ishga tushirish:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Superuser yaratish:
```bash
python manage.py createsuperuser
```

6. Seed data yuklash:
```bash
python manage.py seed_data
```

7. Development serverni ishga tushirish:
```bash
python manage.py runserver
```

8. Brauzerda ochish:
```
http://127.0.0.1:8000
```

## Manager rolini berish

Admin panelda user profile'ga kirib, `is_manager` checkbox'ni belgilang.

## Matn va Kodlar kolleksiyasi

- **Easy Texts**: 50 ta
- **Hard Texts**: 50 ta
- **Python Codes**: 20 ta
- **JavaScript Codes**: 20 ta
- **C++ Codes**: 20 ta
- **Java Codes**: 20 ta

Barcha ma'lumotlar `seed_data` command orqali yuklanadi.

## Admin Panel

Admin panelga kirish:
```
http://127.0.0.1:8000/admin
```

Superuser credentials bilan kirish mumkin.

## API

Platforma faqat Django views va templates ishlatadi. API yo'q.

## Qo'shimcha funksiyalar (optional)

- WebSocket orqali real-time musobaqa
- Dark mode
- Mobile App (Flutter)
- Custom text sharhlash
- Friend system

