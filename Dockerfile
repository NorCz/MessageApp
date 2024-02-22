# syntax=docker/dockerfile:1

FROM python:3.11 AS backend
WORKDIR /
COPY requirements.txt .
RUN pip install -r requirements.txt
ARG FLASK_APP=app.py
COPY *.py /app/backend/
WORKDIR /app/backend/
CMD ["python", "app.py"]

FROM node:hydrogen-slim
COPY /frontend /app/frontend
WORKDIR /app/frontend
RUN npm i
RUN npm install -g serve
RUN npm run build
WORKDIR /app/frontend/
COPY --from=backend /app/backend /app/backend
CMD ["serve", "-s", "build"]
EXPOSE 3000