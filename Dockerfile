# syntax=docker/dockerfile:1

FROM ubuntu:22.04

# Initialise Ubuntu
WORKDIR /
COPY requirements.txt .
RUN apt-get -y update && DEBIAN_FRONTEND=noninteractive apt-get -y install python3.11 pip curl libpcre3 libpcre3-dev libssl-dev tzdata ldap-utils
RUN curl -fsSL https://deb.nodesource.com/setup_21.x | bash - && apt-get install -y nodejs

RUN cp -p /usr/share/zoneinfo/Europe/Warsaw /etc/localtime

# Initialise React Frontend
COPY --chown=nobody:nogroup /frontend/ /app/frontend/
COPY --chown=nobody:nogroup .env /app/frontend/src

WORKDIR /app/frontend
RUN npm i
RUN npm i -g local-web-server
RUN npm run build


# Initialise Python Backend
WORKDIR /
RUN pip install -r requirements.txt
RUN pip install uwsgi -I --no-cache-dir
COPY --chown=nobody:nogroup /.env /app/backend/
COPY --chown=nobody:nogroup *.py /app/backend/
COPY --chown=nobody:nogroup /default_avatar.txt /app/backend
COPY --chown=nobody:nogroup /certs/messageapp.crt /app/backend
COPY --chown=nobody:nogroup /certs/messageapp.key /app/backend

# Run wrapper script
WORKDIR /
COPY --chown=nobody:nogroup docker_cmd_wrapper.sh /

# Symlink instance folder for smaller volume syntax in command
RUN mkdir /instance
RUN chown nobody:nogroup /instance
RUN ln -sf /instance /app/backend/instance

# Setup cron
RUN echo '#!/bin/sh\nexit 0' > /usr/sbin/policy-rc.d
RUN apt-get install -y cron
RUN service cron start

EXPOSE $server_port
CMD ["bash", "./docker_cmd_wrapper.sh"]