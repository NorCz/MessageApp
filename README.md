Ten projekt został wykonany przez zespół "Algorytmiczni Dijkstrowicze" na [Ogólnopolskie Zawody Techniczne PRIMUS INTER PARES](https://zt.zsl.gda.pl/) organizowane przez Zespół Szkół Łączności
Im. Obrońców Poczty Polskiej w Gdańsku.

---

# [PL] MessageApp - serwer Backend
W procesie budowania Backend pakuje serwer Frontend i wystawia go na komunikację oraz wykorzystuje prosty mechanizm proxy, aby operować oboma serwerami na tym samym źródle. Komunikacja zewnętrzna i wewnętrzna z obu serwerów jest szyfrowana podanym certyfikatem.

Gotowe obrazy można pobrać z zakładki [Releases](https://github.com/NorCz/MessageApp/releases) lub bezpośrednio z [repozytorium Docker](https://hub.docker.com/repository/docker/nekuskus/messageapp/general).

## Specyfikacja
Serwer Frontend działa w technologii [React](https://react.dev/), jest budowany poprzez react-scripts i wystawiany na [local-web-server](https://github.com/lwsjs/local-web-server). Serwer Backend działa w technologii [Flask](https://flask.palletsprojects.com/en/3.0.x/) z użyciem silnika [SQLAlchemy](https://www.sqlalchemy.org/) w celu połączenia z bazą danych i jest uruchamiany poprzez serwer [uWSGI](https://github.com/unbit/uwsgi). Wszystkie procesy serwera są uruchamiane jako użytkownik `nobody` w celach bezpieczeństwa.

Baza danych wykorzystuje silnik [SQLite3](https://www.sqlite.org/). Baza danych wraz z kopiami bezpieczeństwa umieszczona jest na woluminie Docker, którym administrator systemu może prosto zarządzać bez ingerowania w sam kontener z bazą danych. Wolumin nie jest czyszczony między uruchomieniami kontenera oraz jest od niego niezależny, dzięki czemu możliwe jest proste aktualizowanie systemu komunikacji poprzez pobranie lub zbudowanie nowego obrazku i połączenie go z tym samym woluminem.

Kopie bezpieczeństwa wykonywane są w folderze `backups` na woluminie. Odtworzenie kopii zapasowej jest proste i polega na zatrzymaniu serwera poprzez interfejs uWSGI, a następnie zastąpieniu pliku bazy danych `project.db` wybranym plikiem kopii zapasowej.

Dokumentacja API jest dostępna w języku angielskim pod zakładką [Wiki](https://github.com/NorCz/MessageApp/wiki/MessageApp-Backend-API-Documentation).

### Wymagania
* [Docker](https://www.docker.com/products/docker-desktop/) lub inne oprogramowanie czy usługa zdolna do uruchamiania kontenerów Docker.

## Uruchamianie
Aby uruchomić usługę serwera należy uruchomić zbudowany lub pobrany kontener Docker. Można to zrobić z wiersza poleceń lub poprzez inne oprogramowanie czy usługi takie jak [Docker Desktop](https://www.docker.com/products/docker-desktop/), lub Amazon Web Services.
```bash
docker run -d --mount source=messageapp-dbvolume,target=/instance --env-file .env messageapp
```
Jeśli ustawiasz w pliku `.env` inny adres serwera niż `127.0.0.1`, powinieneś przekierować port na niego w poleceniu, którym uruchamiasz kontener Docker:
```bash
docker run -dp [server_address]:[server_port]:[server_port] --mount source=messageapp-dbvolume,target=/instance --env-file .env messageapp
```

Flaga `--mount source=messageapp-dbvolume,target=/instance` odpowiada za połączenie kontenera z istniejącym już woluminem lub stworzenie nowego woluminu. Możesz zastąpić nazwę `messageapp-dbvolume` własną.

Serwer Frontend jest teraz dostępny pod adresem `https://[server_address]:[server_port]` (default/prebuilt: `https://127.0.0.1:3000`). Serwer Backend dostępny jest przez proxy pod tym samym adresem na ścieżkach `/api/`.

> [!WARNING]
> Wszystkie adresy wypisywane przez kontener Docker są dla niego wewnętrzne i niedostępne z zewnątrz bez przekierowania. Te informacje są wypisywane w celach debugowania, a sam serwer wystawiony jest na zewnątrz tak jak zostało to opisane powyżej w dokumentacji.

Bezpośrednie zarządzanie serwerem Backend możliwe jest poprzez kolejkę serwera dostępną w kontenerze pod ścieżką `/app/backend/uwsgi-fifo`. Dokumentacja tego interfejsu dostępna w [dokumentacji uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/MasterFIFO.html). W szczególności ważne jest tutaj polecenie `q`, które pozwala bezpiecznie zakończyć działanie serwera. Aby uzyskać dostęp do linii komend kontenera, można wykorzystać poniższe polecenie.
```bash
docker exec -u 0 -it [nazwa_kontenera] bash
```

## Budowa manualna

### Wymagane pliki:
```
.env
certs/messageapp.crt
certs/messageapp.key
```
W środowisku firmowym zaleca się wykorzystać własny certyfikat w celu szyfrowania zapytań HTTPS. W gotowych obrazach zamieszczony jest prosty certyfikat przygotowany w tym celu, lecz można go prosto zastąpić zamieszczając własny certyfikat w folderze `certs` i budując projekt. Certyfikat powinien być zainstalowany na stacjach roboczych w firmie, na przykład poprzez usługę Active Directory lub obraz wykorzystywany do wczesnej konfiguracji tych stacji roboczych.

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
cron_backup_hour=[Godzina, o której wykonywany jest skrypt do zarządzania backupami]
cron_backup_count=[Ilość backupów do przechowywania]
```
### Proces budowy
Sklonuj lub pobierz to repozytorium.
```bash
git clone --recurse-submodules https://github.com/NorCz/MessageApp.git
```
Uaktualnij lokalną kopię modułu Frontend.
```bash
git pull --recurse-submodules
git submodule update --remote --merge
```
Teraz możesz zbudować i [uruchomić](#uruchamianie) kontener Docker.
```bash
docker build -t nekuskus/messageapp:latest .
```

# [EN] MessageApp - Backend server
The Backend bundles and exposes the Frontend server during build, and uses a simple proxy mechanism to operate both servers on the same origin. Both internal and external communication from the servers is encrypted using a provided certificate.

Prebuilt images can also be downloaded from the [Releases](https://github.com/NorCz/MessageApp/releases) tab, or directly from the [Docker repository](https://hub.docker.com/repository/docker/nekuskus/messageapp/general).

## Specification
The Frontend server is based on the [React](https://react.dev/) framework, uses react-scripts for building, and is served with [local-web-server](https://github.com/lwsjs/local-web-server). The Backend server is based on the [Flask](https://flask.palletsprojects.com/en/) framework, uses the [SQLAlchemy](https://www.sqlalchemy.org/) engine for managing a database connection, and is run through [uWSGI](https://github.com/unbit/uwsgi). All the server processes are run as the `nobody` user for safety.

The database runs on the [SQLite3](https://www.sqlite.org/) engine. Both the database itself and its backup copies are located on a Docker volume, which can be easily managed by the system administrator without interfering with the communication system. The volume is not cleared between container runs and is separate from it, which makes updating the system easy, requiring simply downloading or building a new version of the image and connecting it with the same volume. 

Backups are created in the `backups` folder within the volume. Restoring from a backup is trivial. You should first stop the server through the uWSGI interface and then replace the `project.db` database file with your chosen backup file.

API documentation is available under the [Wiki](https://github.com/NorCz/MessageApp/wiki/MessageApp-Backend-API-Documentation) tab.

### Requirements
* [Docker](https://www.docker.com/products/docker-desktop/), or other software or service capable of running Docker containers.

## Usage
You can start the server by running the Docker image. This can be done either from the terminal, or by using another software or service such as [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Amazon Web Services.
```bash
docker run -d --mount source=messageapp-dbvolume,target=/instance --env-file .env messageapp
```
If you're using a different server address from `127.0.0.1` in the `.env` file, you should also specify the forwarded port within the `run` command:
```bash
docker run -dp [server_address]:[server_port]:[server_port] --mount source=messageapp-dbvolume,target=/instance --env-file .env messageapp
```
The `--mount source=messageapp-dbvolume,target=/instance` flag is responsible for connecting a pre-existing volume or creating a new one. You can replace the name `messageapp-dbvolume` with another.

The Frontend server is now available at `https://[server_address]:[server_port]` (default/prebuilt: `https://127.0.0.1:3000`). The Backend server is available at the same address through proxy on `/api/` endpoints.

> [!WARNING]
> All addresses printed by the Docker container are internal to its network and unreachable from outside without explicit forwarding. These messages are meant for debugging purposes, the server address is still as configured by the user and explained in this documentation.

Direct management of the Backend server is possible through the server queue available in the container as `/app/backend/uwsgi-fifo`. This interface is described in the [uWSGI documentation](https://uwsgi-docs.readthedocs.io/en/latest/MasterFIFO.html). The command `q` is particularly important here, as it allows for gracefully shutting down the server instances. You can use the following command to access the server command-line.
```bash
docker exec -u 0 -it [container_name] bash
```

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
cron_backup_hour=[Hour of the day when the backup script is run]
cron_backup_count=[Number of backups to preserve]
```

### Build process
First, clone or download this repository.
```bash
git clone --recurse-submodules https://github.com/NorCz/MessageApp.git
```
Make sure your Frontend submodule is up-to-date.
```bash
git pull --recurse-submodules
git submodule update --remote --merge
```
Now, you can build and [run](#usage) the Docker container.
```bash
docker build -t nekuskus/messageapp:latest .
```
