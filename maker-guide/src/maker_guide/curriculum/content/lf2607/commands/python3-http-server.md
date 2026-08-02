# python3 -m http.server

## Use

```bash
PORT="$((10000 + $(id -u)))"
python3 -m http.server "$PORT" --bind 127.0.0.1
```

## What It Does

This starts a simple HTTP server in the current directory, listening only on localhost.

## Practice

Run it from the directory you want to serve. Press `Ctrl-C` in that terminal to stop it before another process uses the same port.

## Watch Out

It is a learning tool, not a production web server.
