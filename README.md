# MessageApp - backend server

## Manual building

### Required files:
```
.env
certs/messageapp.key
certs/messageapp.key
```
In a company setting, it is important that you use your own certificate for encrypting the HTTPS requests. The pre-built images are provided with a simple certificate for this purpose, but these can easily be changed by supplying your own in the `certs` folder and building the project.

### `.env` format
```env
secret_key=[Encryption key used by the Flask server]
sender_email=[Your password recovery email account]
password=[Your password recovery email password]
smtp_server=[Your password recovery email server]
```
### Build process
Make sure your frontend submodule is up-to-date.
```bash
git submodule update --init --recursive
```

Now, you can create and run the docker container.
```bash
docker build -t messageapp:latest .
docker run -p 127.0.0.1:3000:3000 messageapp
```

Pre-built images can also be downloaded from the Releases tab.
