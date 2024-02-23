# [PL] MessageApp - serwer Backend
W procesie budowania Backend pakuje serwer Frontend i wystawia go na komunikację, oraz wykorzystuje prosty mechanizm proxy aby operować oboma serwerami na tym samym źródle. Komunikacja zewnętrzna i wewnętrzna z obu serwerów jest szyfrowana podanym certyfikatem.

Gotowe obrazy można pobrać z zakładki [Releases](https://github.com/NorCz/MessageApp/releases), lub bezpośrednio z [repozytorium Docker](https://hub.docker.com/repository/docker/nekuskus/messageapp/general).

## Specyfikacja
Serwer Frontend działa w technologii [React](https://react.dev/), jest budowany poprzez react-scripts i wystawiany na [local-web-server](https://github.com/lwsjs/local-web-server). Serwer Backend działa w technologii [Flask](https://flask.palletsprojects.com/en/3.0.x/) z użyciem silnika [SQLAlchemy](https://www.sqlalchemy.org/) w celu połączenia z bazą danych i jest uruchamiany poprzez serwer [uWSGI](https://github.com/unbit/uwsgi). Wszystkie procesy serwera są uruchamiane jako użytkownik `nobody` w celach bezpieczeństwa.

Baza danych wykorzystuje silnik [SQLite3](https://www.sqlite.org/).

Dokumentacja API jest dostępna w języku angielskim pod zakładką [Wiki](https://github.com/NorCz/MessageApp/wiki/MessageApp-Backend-API-Documentation).

### Wymagania
* [Docker](https://www.docker.com/products/docker-desktop/), lub inne oprogramowanie lub usługa zdolna do uruchamiania kontenerów Docker.

## Uruchamianie
Aby uruchomić usługę serwera należy uruchomić zbudowany lub pobrany kontener Docker. Można to zrobić z wiersza poleceń, lub poprzez inne oprogramowanie czy usługi takie jak [Docker Desktop](https://www.docker.com/products/docker-desktop/) lub Amazon Web Services.
```bash
docker run -d --env-file .env messageapp
```
Jeśli ustawiasz w pliku `.env` inny adres serwera niż `127.0.0.1`, powinieneś przekierować port na niego w poleceniu, którym uruchamiasz kontener Docker:
```bash
docker run -dp [server_address]:[server_port]:[server_port] --env-file .env messageapp
```
Serwer jest teraz dostępny pod adresem `https://[server_address]:[server_port]` (default/prebuilt: `https://127.0.0.1:3000`).

## Budowa manualna

### Wymagane pliki:
```
.env
certs/messageapp.crt
certs/messageapp.key
```
W środowisku firmowym, zaleca się wykorzystać własny certyfikat w celu szyfrowania zapytań HTTPS. W gotowych obrazach zamieszczony jest prosty certyfikat przygotowany w tym celu, lecz można go prosto zastąpić zamieszczając własny certyfikat w folderze `certs` i budując projekt. Certyfikat powinien być zainstalowany na stacjach roboczych w firmie, na przykład poprzez usługę Active Directory lub obraz wykorzystywany do wczesnej konfiguracji tych stacji roboczych.

### Format pliku `.env`
```env
server_address=[Adress wykorzystywany przez serwer Frontend]
server_port=[Port wykorzystywany przez serwer Frontend]
secret_key=[Klucz szyfrowania wykorzystywany przez serwer Flask]
sender_email=[Konto pocztowe usługi odzyskiwania haseł]
password=[Hasło konta pocztowego usługi odzyskiwania haseł]
smtp_server=[Adres serwera pocztowego usługi odzyskiwania haseł]
smtp_port=[Port SMTP serwera pocztowego usługi odzyskiwania haseł]
uwsgi_worker_count=[Ilość wątków/procesów wykorzystywana przez serwer Backend]
```
### Proces budowy
Sklonuj lub pobierz to repozytorium.
```bash
git clone --recurse-submodules https://github.com/NorCz/MessageApp.git
```
Uaktualnij lokalną kopię modułu Frontend.
```bash
git submodule foreach git pull origin master
```
Teraz możesz zbudować i [uruchomić](#uruchamianie) kontener Docker.
```bash
docker build -t messageapp:latest .
```

# [EN] MessageApp - Backend server
The Backend bundles and exposes the Frontend server during build, and uses a simple proxy mechanism to operate both servers on the same origin. Both internal and external communication from the servers is encrypted using a provided certificate.

Prebuilt images can also be downloaded from the [Releases](https://github.com/NorCz/MessageApp/releases) tab, or directly from the [Docker repository](https://hub.docker.com/repository/docker/nekuskus/messageapp/general).

## Specification
The Frontend server is based on the [React](https://react.dev/) framework, uses react-scripts for building, and is served with [local-web-server](https://github.com/lwsjs/local-web-server). The Backend server is based on the [Flask](https://flask.palletsprojects.com/en/) framework, uses the [SQLAlchemy](https://www.sqlalchemy.org/) engine for managing a database connection, and is run through [uWSGI](https://github.com/unbit/uwsgi). All the server processes are run as the `nobody` user for safety.

API documentation is available under the [Wiki](https://github.com/NorCz/MessageApp/wiki/MessageApp-Backend-API-Documentation) tab.

### Requirements
* [Docker](https://www.docker.com/products/docker-desktop/), or other software or service capable of running Docker containers.

## Usage
You can start the server by running the Docker image. This can be done either from the terminal, or by using another software or service such as [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Amazon Web Services.
```bash
docker run -d --env-file .env messageapp
```
If you're using a different server address from `127.0.0.1` in the `.env` file, you should also specify the forwarded port within the `run` command:
```bash
docker run -dp [server_address]:[server_port]:[server_port] --env-file .env messageapp
```
The server is now available at `https://[server_address]:[server_port]` (default/prebuilt: `https://127.0.0.1:3000`).

## Manual building

### Required files:
```
.env
certs/messageapp.crt
certs/messageapp.key
```
In a company setting, it is recommended that you use your own certificate for encrypting the HTTPS requests. The prebuilt images are provided with a simple certificate for this purpose, but this can easily be changed by supplying your own in the `certs` folder and building the project. The certificate should be installed on company workstations, possibly via Active Directory services, or in the image used for initializing these workstations.

### `.env` format
```env
server_address=[Address used by the Frontend server]
server_port=[Port used by the Frontend server]
secret_key=[Encryption key used by the Flask server]
sender_email=[Your password recovery email account]
password=[Your password recovery email password]
smtp_server=[Your password recovery email server address]
smtp_port=[Your password recovery email server SMTP port]
uwsgi_worker_count=[Worker/process count used by the Backend server]
```

### Build process
First, clone or download this repository.
```bash
git clone --recurse-submodules https://github.com/NorCz/MessageApp.git
```
Make sure your Frontend submodule is up-to-date.
```bash
git submodule foreach git pull origin master
```
Now, you can build and [run](#usage) the Docker container.
```bash
docker build -t messageapp:latest .
```
