# VPS Server Deployment Guide

## Quick Start

### 1. Server tayyorlash

```bash
# System yangilash
sudo apt update && sudo apt upgrade -y

# Python va pip o'rnatish
sudo apt install python3 python3-pip python3-venv -y

# PostgreSQL (ixtiyoriy, lekin tavsiya qilinadi)
sudo apt install postgresql postgresql-contrib -y

# Nginx o'rnatish
sudo apt install nginx -y

# Git o'rnatish
sudo apt install git -y
```

### 2. Loyihani klonlash

```bash
cd /var/www  # yoki boshqa papka
git clone <repository-url> geeks-TTP
cd geeks-TTP
```

### 3. Environment variables sozlash

```bash
cp env.example .env
nano .env
```

`.env` faylida quyidagilarni sozlang:
```env
SECRET_KEY=<yangi-random-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### 4. Deploy script ishga tushirish

```bash
chmod +x deploy.sh
./deploy.sh
```

### 5. Gunicorn ishga tushirish (test)

```bash
source venv/bin/activate
gunicorn typing_platform.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

Agar ishlayotganini ko'rsangiz, `Ctrl+C` bosib to'xtating va systemd service yarating.

### 6. Systemd Service yaratish

```bash
sudo cp systemd/typing-platform.service /etc/systemd/system/
sudo nano /etc/systemd/system/typing-platform.service
```

Faylda quyidagilarni o'zgartiring:
- `WorkingDirectory=/var/www/geeks-TTP` (loyiha joylashgan papka)
- `User=www-data` (yoki boshqa user)
- `Group=www-data`
- `PATH=/var/www/geeks-TTP/venv/bin`

Keyin:
```bash
sudo systemctl daemon-reload
sudo systemctl enable typing-platform
sudo systemctl start typing-platform
sudo systemctl status typing-platform
```

### 7. Nginx konfiguratsiyasi

```bash
sudo nano /etc/nginx/sites-available/typing-platform
```

Quyidagi konfiguratsiyani qo'shing (DEPLOYMENT.md dan nusxalang):
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location /static/ {
        alias /var/www/geeks-TTP/staticfiles/;
    }
    
    location /media/ {
        alias /var/www/geeks-TTP/media/;
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

Keyin:
```bash
sudo ln -s /etc/nginx/sites-available/typing-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8. SSL sertifikat (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 9. Firewall sozlash

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Xavfsizlik

1. **SECRET_KEY** - har doim yangi random key ishlating
2. **DEBUG=False** - production'da har doim False
3. **ALLOWED_HOSTS** - faqat o'z domain nomlaringizni qo'shing
4. **SSL/HTTPS** - har doim ishlating
5. **Firewall** - faqat kerakli portlarni oching

## Monitoring

```bash
# Application logs
tail -f /var/www/geeks-TTP/logs/django.log

# Systemd service logs
sudo journalctl -u typing-platform -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Backup

```bash
# Database backup (SQLite)
cp /var/www/geeks-TTP/db.sqlite3 /backup/db_$(date +%Y%m%d).sqlite3

# Database backup (PostgreSQL)
pg_dump -U your_user your_db > /backup/db_$(date +%Y%m%d).sql

# Media files backup
tar -czf /backup/media_$(date +%Y%m%d).tar.gz /var/www/geeks-TTP/media/
```

## Troubleshooting

### Service ishlamayapti
```bash
sudo systemctl status typing-platform
sudo journalctl -u typing-platform -n 50
```

### Nginx xatolik
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### Permission xatolik
```bash
sudo chown -R www-data:www-data /var/www/geeks-TTP
sudo chmod -R 755 /var/www/geeks-TTP
```

