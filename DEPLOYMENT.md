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
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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

### 14. Updates

When updating the application:

1. Pull latest code
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Collect static files: `python manage.py collectstatic --noinput`
5. Restart the application server

