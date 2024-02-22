# [PL] MessageApp - serwer Backendu
W procesie budowania Backend zawiera serwer Frontendu i wystawia go na komunikację, oraz wykorzystuje prosty mechanizm proxy aby operować oboma serwerami na tym samym źródle. Komunikacja zewnętrzna i wewnętrzna z obu serwerów jest szyfrowana podanym certyfikatem.

Dokumentacja API jest dostępna w języku angielskim pod zakładką [Wiki](https://github.com/NorCz/MessageApp/wiki/MessageApp-Backend-API-Documentation).

Gotowe obrazy można pobrać z zakładki [Releases](https://github.com/NorCz/MessageApp/releases), lub bezpośrednio z [repozytorium Docker](https://hub.docker.com/repository/docker/nekuskus/messageapp/general).

## Wymagiania
* [Docker](https://www.docker.com/products/docker-desktop/), lub inne oprogramowanie lub usługa zdolna do uruchamiania kontenerów Docker.

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
smtp_server=[Serwer pocztowy usługi odzyskiwania haseł]
smtp_port=[Port SMTP serwera pocztowego usługi odzyskiwania haseł]
```
### Proces budowy
Uaktualnij lokalną kopię modułu Frontendu.
```bash
git submodule update --init --recursive
```

Teraz możesz zbudować i uruchomić kontener Docker.
```bash
docker build -t messageapp:latest .
docker run -d --env-file .env messageapp
```

# [EN] MessageApp - Backend server
The Backend bundles and exposes the Frontend server during build, and uses a simple proxy mechanism to operate both servers on the same origin. Both internal and external communication from the servers is encrypted using a provided certificate.

API documentation is available under the [Wiki](https://github.com/NorCz/MessageApp/wiki/MessageApp-Backend-API-Documentation) tab.

Prebuilt images can also be downloaded from the [Releases](https://github.com/NorCz/MessageApp/releases) tab, or directly from the [Docker repository](https://hub.docker.com/repository/docker/nekuskus/messageapp/general).

## Requirements
* [Docker](https://www.docker.com/products/docker-desktop/), or other software or service capable of running Docker containers.

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
smtp_server=[Your password recovery email server]
smtp_port=[Your password recovery email server SMTP port]
```
### Build process
Make sure your Frontend submodule is up-to-date.
```bash
git submodule update --init --recursive
```

Now, you can create and run the Docker container.
```bash
docker build -t messageapp:latest .
docker run -d --env-file .env messageapp
```
