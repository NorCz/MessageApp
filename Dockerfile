# syntax=docker/dockerfile:1

FROM ubuntu:22.04

# Initialise Ubuntu
WORKDIR /
COPY requirements.txt .
RUN apt-get -y update && apt-get -y install python3.11 pip curl libpcre3 libpcre3-dev libssl-dev
RUN curl -fsSL https://deb.nodesource.com/setup_21.x | bash - && apt-get install -y nodejs

# Initialise Python Backend
RUN pip install -r requirements.txt
RUN pip install uwsgi -I --no-cache-dir
COPY --chown=nobody:nogroup /.env /app/backend/
COPY --chown=nobody:nogroup *.py /app/backend/
COPY --chown=nobody:nogroup /certs/messageapp.crt /app/backend
COPY --chown=nobody:nogroup /certs/messageapp.key /app/backend

# Initialise React Frontend
COPY --chown=nobody:nogroup /frontend /app/frontend
COPY --chown=nobody:nogroup .env /app/frontend/src

WORKDIR /app/frontend
RUN npm i
RUN npm i -g local-web-server
RUN npm run build

# Run wrapper script
WORKDIR /
COPY --chown=nobody:nogroup docker_cmd_wrapper.sh /

# Symlink instance folder for smaller volume syntax in command
RUN mkdir /instance
RUN chown nobody:nogroup /instance
RUN ln -sf /instance /app/backend/instance

USER nobody:nogroup
EXPOSE $server_port
CMD ["bash", "./docker_cmd_wrapper.sh"]