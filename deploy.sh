#!/bin/bash
# VPS Deployment Script for Typing Trainer Platform

set -e  # Exit on error

echo "🚀 Typing Trainer Platform - VPS Deployment Script"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env fayli topilmadi!${NC}"
    echo "📝 .env.example faylini .env ga nusxalang va sozlang:"
    echo "   cp .env.example .env"
    echo "   nano .env  # yoki boshqa editor"
    exit 1
fi

echo -e "${GREEN}✅ .env fayli topildi${NC}"

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check Python version
echo "🐍 Python versiyasini tekshiryapman..."
python3 --version

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment yaratilmoqda..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Virtual environment faollashtirilmoqda..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  pip yangilanmoqda..."
pip install --upgrade pip

# Install dependencies
echo "📥 Dependencies o'rnatilmoqda..."
pip install -r requirements.txt

# Create logs directory
echo "📁 Logs papkasi yaratilmoqda..."
mkdir -p logs
chmod 755 logs

# Run migrations
echo "🗄️  Database migrations bajarilmoqda..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Collect static files
echo "📦 Static fayllar to'planmoqda..."
python manage.py collectstatic --noinput

# Create superuser if not exists (interactive)
echo "👤 Superuser yaratish (agar mavjud bo'lmasa)..."
python manage.py createsuperuser || echo "Superuser allaqachon mavjud yoki yaratilmadi"

# Check Django deployment settings
echo "🔍 Django deployment sozlamalari tekshirilmoqda..."
python manage.py check --deploy

echo ""
echo -e "${GREEN}✅ Deployment tayyor!${NC}"
echo ""
echo "📋 Keyingi qadamlar:"
echo "1. Gunicorn orqali server ishga tushiring:"
echo "   gunicorn typing_platform.wsgi:application --bind 0.0.0.0:8000 --workers 4"
echo ""
echo "2. Systemd service yaratish (tavsiya qilinadi):"
echo "   sudo nano /etc/systemd/system/typing-platform.service"
echo ""
echo "3. Nginx konfiguratsiyasi:"
echo "   DEPLOYMENT.md faylini ko'ring"
echo ""
echo -e "${GREEN}🎉 Muvaffaqiyatli!${NC}"

