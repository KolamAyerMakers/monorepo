# HTTP Basics

## Core Idea

HTTP is a request-response protocol with methods, status codes, headers, and optional bodies. Tools such as curl display these fields as readable text; HTTP/2 and HTTP/3 do not use the same text wire format as HTTP/1.1.

## Practice Alone

Use `curl -I` for headers and plain `curl` for the body.

`-I` sends a `HEAD` request; plain curl sends `GET`. Use `-i` for GET headers and body together. HTTPS protects HTTP with TLS encryption and certificate verification.

## Done When

You can identify a status code and one header.

## Go Deeper

- [Client](client.md) explains the program initiating the request.
- [Server](server.md) explains the process responding to the request.
- [IP Networking](ip-networking.md) explains the DNS, address, port, and protocol layers below HTTP.
- [HTTP](http.md) gives a fuller HTTP request-response reference.
