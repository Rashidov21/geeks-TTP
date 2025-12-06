# Development Tips

## HTTPS Error Fix

Agar siz quyidagi xatolikni ko'rsangiz:
```
ERROR You're accessing the development server over HTTPS, but it only supports HTTP.
```

### Yechimlar:

1. **HTTP orqali kirish:**
   - `http://127.0.0.1:8000` (HTTPS emas!)
   - `http://localhost:8000`

2. **Brauzer cache tozalash:**
   - Chrome/Edge: `Ctrl + Shift + Delete` → "Cached images and files" → Clear
   - Firefox: `Ctrl + Shift + Delete` → "Cache" → Clear

3. **HSTS sozlamalarini tozalash:**
   - Chrome/Edge: `chrome://net-internals/#hsts` → "Delete domain security policies" → `127.0.0.1` va `localhost` ni kiriting
   - Firefox: `about:preferences#privacy` → "Clear Data" → "Cookies and Site Data"

4. **Brauzer extension'larni tekshirish:**
   - HTTPS Everywhere kabi extension'lar development server'ni HTTPS'ga yo'naltirishi mumkin
   - Development vaqtida bu extension'larni o'chirib qo'ying

5. **Server'ni qayta ishga tushirish:**
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```

### Development Server ishga tushirish:

```bash
# Oddiy usul
python manage.py runserver

# Aniq IP va port
python manage.py runserver 127.0.0.1:8000

# Boshqa port
python manage.py runserver 8001
```

### Production uchun:

Production'da HTTPS kerak bo'lganda, `settings.py` da `DEBUG = False` qiling va security settings'lar avtomatik faollashadi.

