set -m
source /app/frontend/src/.env

cd /app/frontend
ws \
  --port $server_port \
  --directory build \
  --spa index.html \
  --rewrite '/api/(.*) -> https://127.0.0.1:5000/api/$1' \
  --key /app/backend/messageapp.key \
  --cert /app/backend/messageapp.crt \
  --log.format tiny &

cd /app/backend
uwsgi --master --https 127.0.0.1:5000,messageapp.crt,messageapp.key -p $uwsgi_worker_count --enable-threads --wsgi-file app.py --callable app