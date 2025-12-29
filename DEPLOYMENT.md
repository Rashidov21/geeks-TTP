# Deployment Guide

## Production Settings

### 1. Environment Variables

Create a `.env` file in the project root with the following variables:

```env
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

**Important:** Never commit the `.env` file to version control!

### 2. Generate Secret Key

You can generate a secure secret key using:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### 3. Database Migration

Run migrations before deployment:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### 6. Create Logs Directory

```bash
mkdir -p logs
chmod 755 logs
```

### 7. Production Checklist

- [ ] Set `DEBUG=False` in environment variables
- [ ] Set secure `SECRET_KEY` in environment variables
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set up proper database (PostgreSQL recommended for production)
- [ ] Configure static files serving (nginx/Apache)
- [ ] Set up SSL/HTTPS
- [ ] Configure logging
- [ ] Set up backup strategy
- [ ] Configure email settings (if needed)
- [ ] Set up monitoring and error tracking

### 8. WSGI Configuration

For production, use a proper WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn typing_platform.wsgi:application --bind 0.0.0.0:8000
```

### 9. Nginx Configuration Example

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL certificates (Let's Encrypt yoki boshqa)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL optimization
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Static files
    location /static/ {
        alias /path/to/geeks-TTP/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /path/to/geeks-TTP/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Django application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 10. Security Headers

The application includes security headers in `settings.py`:
- XSS Protection
- Content Type NoSniff
- X-Frame-Options
- HSTS (in production)

### 11. Performance Optimization

- Database indexes are configured
- Caching is enabled (in-memory cache by default)
- Query optimization with `select_related` and `prefetch_related`
- Static files optimization

### 12. Monitoring

Check logs in the `logs/` directory:
- `logs/django.log` - Application logs

### 13. Database Backup

Regular backups are recommended:

```bash
python manage.py dumpdata > backup.json
```

### 14. Systemd Service (Tavsiya qilinadi)

Production uchun systemd service yaratish:

1. **Service faylini yaratish:**
```bash
sudo cp systemd/typing-platform.service /etc/systemd/system/
sudo nano /etc/systemd/system/typing-platform.service
# WorkingDirectory va PATH ni o'zgartiring
```

2. **Service ishga tushirish:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable typing-platform
sudo systemctl start typing-platform
sudo systemctl status typing-platform
```

3. **Service boshqarish:**
```bash
sudo systemctl restart typing-platform  # Qayta ishga tushirish
sudo systemctl stop typing-platform     # To'xtatish
sudo systemctl start typing-platform    # Ishga tushirish
sudo journalctl -u typing-platform -f  # Loglarni ko'rish
```

### 15. Updates

When updating the application:

1. Pull latest code: `git pull origin main`
2. Activate virtual environment: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Run migrations: `python manage.py migrate`
5. Collect static files: `python manage.py collectstatic --noinput`
6. Restart the application server:
   ```bash
   sudo systemctl restart typing-platform
   # yoki
   # pkill -f gunicorn
   # gunicorn typing_platform.wsgi:application --bind 0.0.0.0:8000 --workers 4 &
   ```

### 16. Database Backup

Regular backups are recommended:

```bash
# SQLite uchun
cp db.sqlite3 backups/db_$(date +%Y%m%d_%H%M%S).sqlite3

# PostgreSQL uchun
pg_dump -U your_user your_db_name > backups/db_$(date +%Y%m%d_%H%M%S).sql

# Django dumpdata
python manage.py dumpdata > backups/data_$(date +%Y%m%d_%H%M%S).json
```

### 17. Monitoring

- **Logs:** `logs/django.log` va `logs/error.log`
- **System logs:** `journalctl -u typing-platform -f`
- **Nginx logs:** `/var/log/nginx/access.log` va `/var/log/nginx/error.log`

