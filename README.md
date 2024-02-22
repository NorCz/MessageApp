# MessageApp - backend server

## Manual building
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
