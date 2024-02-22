set -m

cd /app/frontend
npx local-web-server \
  --port 3000 \
  --directory build \
  --spa index.html \
  --https \
  --rewrite '/api/(.*) -> https://127.0.0.1:5000/api/$1' \
  --log.format tiny &

cd /app/backend
uwsgi --master --https 127.0.0.1:5000,messageapp.crt,messageapp.key --uid nobody --gid nogroup -p 4 --wsgi-file app.py --callable app