# Battles App - 1v1 Typing Battles

## Avtomatik tozalash

Battle ma'lumotlari 14 kundan keyin avtomatik o'chiriladi. Buning uchun quyidagi command ni ishga tushirish kerak:

### Linux/Mac (Cron Job)

```bash
# Har kuni kechasi 2:00 da ishga tushadi
0 2 * * * cd /path/to/geeks-TTP && python manage.py cleanup_old_battles
```

Crontab ga qo'shish:
```bash
crontab -e
# Keyin yuqoridagi qatorni qo'shing
```

### Windows (Task Scheduler)

1. Task Scheduler ni oching
2. "Create Basic Task" ni tanlang
3. Name: "Cleanup Old Battles"
4. Trigger: Daily, 2:00 AM
5. Action: Start a program
   - Program: `python`
   - Arguments: `manage.py cleanup_old_battles`
   - Start in: `C:\Users\rashi\Documents\GitHub\geeks-TTP`

### Manual ishga tushirish

```bash
python manage.py cleanup_old_battles
# Yoki boshqa kunlar uchun:
python manage.py cleanup_old_battles --days 7
```

