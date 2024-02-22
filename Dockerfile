# syntax=docker/dockerfile:1

FROM ubuntu:latest

# Initialise Ubuntu
WORKDIR /
COPY requirements.txt .
RUN apt-get -y update
RUN apt-get -y install python3.11 pip curl libpcre3 libssl-dev
RUN curl -fsSL https://deb.nodesource.com/setup_21.x | bash -
RUN apt-get install -y nodejs

# Initialise Python Backend
RUN pip install -r requirements.txt
RUN pip install uwsgi -I --no-cache-dir
COPY .env /app/backend/
COPY *.py /app/backend/
COPY /certs/messageapp.crt /app/backend
COPY /certs/messageapp.key /app/backend

# Initialise Python Frontend
COPY /frontend /app/frontend
WORKDIR /app/frontend
RUN npm i
RUN npm i local-web-server
RUN npm run build

# Run wrapper script
WORKDIR /
RUN chown -R nobody /app/backend
COPY docker_cmd_wrapper.sh /
EXPOSE $flask_port
CMD ["bash", "./docker_cmd_wrapper.sh"]