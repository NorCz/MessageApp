#!/bin/bash
set -m
set -f
source /app/frontend/src/.env
service cron start
ulimit -s 65535

# Run backup helper
if [[ -v cron_backup_hour && -v cron_backup_minute && -v cron_backup_count ]]; then
  python3 -c "print('Found variables for backup: ${cron_backup_hour//$'\r'/} (cron_backup_hour), ${cron_backup_minute//$'\r'/} (cron_backup_minute), ${cron_backup_count//$'\r'/} (cron_backup_count).')"
  python3 -c "print('Starting backup service.')"
  echo "$cron_backup_minute $cron_backup_hour * * * /usr/bin/python3 /app/backend/backup_manager.py $cron_backup_count > /proc/1/fd/1 2>&1" | crontab -
else
  python3 -c "print('Variables for backup not found, not starting backup service.')"
fi


# Run AD helper
if [[ -v ad_server_dn && -v ad_group_cn && -v ad_username && -v ad_password ]]; then
  python3 -c "print('Found variables for AD: ${ad_server_dn//$'\r'/} (ad_server_dn), ${ad_group_cn//$'\r'/} (ad_group_cn), not logging ad_username and ad_password.')"
  python3 -c "print('Starting AD service.')"
  (crontab -l 2>/dev/null; echo "*/15 * * * * python3 /app/backend/create_ad_users.py > /proc/1/fd/1 2>&1") | crontab -
else
  python3 -c "print('Variables for AD not found, not starting AD service.')"
fi

cd /app/frontend
su nobody -s /bin/bash -c 'ws \
  --port $server_port \
  --directory build \
  --spa index.html \
  --rewrite "/api/(.*) -> https://127.0.0.1:5000/api/\$1" \
  --key /app/backend/messageapp.key \
  --cert /app/backend/messageapp.crt \
  --log.format tiny &'

cd /app/backend
uwsgi --master --uid nobody --gid nogroup --https 127.0.0.1:5000,messageapp.crt,messageapp.key -p "$uwsgi_worker_count" --enable-threads --wsgi-file app.py --callable app --master-fifo /app/backend/uwsgi-fifo --listen 4096