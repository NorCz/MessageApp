#!/bin/bash
set -m
set -f
source /app/frontend/src/.env

#Run backup
python3 /app/backend/backup_manager.py $cron_backup_count
service cron start
echo "$cron_backup_minute $cron_backup_hour * * * /usr/bin/python3 /app/backend/backup_manager.py $cron_backup_count > /proc/1/fd/1 2>&1" | crontab -

cd /app/frontend
su nobody -s /bin/bash -c 'ws \
  --port $server_port \
  --directory build \
  --spa index.html \
  --rewrite "/api/(.*) -> https://127.0.0.1:5000/api/$1" \
  --key /app/backend/messageapp.key \
  --cert /app/backend/messageapp.crt \
  --log.format tiny &'

cd /app/backend
uwsgi --master --uid nobody --gid nogroup --https 127.0.0.1:5000,messageapp.crt,messageapp.key -p $uwsgi_worker_count --enable-threads --wsgi-file app.py --callable app --master-fifo /app/backend/uwsgi-fifo --listen 4096