set -m
source /app/frontend/src/.env

cd /app/frontend
npx local-web-server \
  --port $server_port \
  --directory build \
  --spa index.html \
  --rewrite '/api/(.*) -> https://127.0.0.1:5000/api/$1' \
  --key /app/backend/messageapp.key \
  --cert /app/backend/messageapp.crt \
  --log.format tiny &

cd /app/backend
uwsgi --master --https 127.0.0.1:5000,messageapp.crt,messageapp.key -p 4 --wsgi-file app.py --callable app