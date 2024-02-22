set -m
source /app/backend/.env

cd /app/frontend
npx local-web-server \
  --port $flask_port \
  --directory build \
  --spa index.html \
  --rewrite "/api/(.*) -> https://127.0.0.1:5000/api/$1" \
  --key /app/backend/messageapp.key \
  --cert /app/backend/messageapp.crt \
  --log.format tiny &

cd /app/backend
uwsgi --master --https 127.0.0.1:5000,messageapp.crt,messageapp.key --uid nobody --gid nogroup -p 4 --wsgi-file app.py --callable app