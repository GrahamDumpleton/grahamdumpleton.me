---
title: "Muru: HTTPS in development"
description: "How a Muru development run serves HTTPS with a certificate your browser trusts, so HTTP/2, Secure cookies and URL schemes can be tested without a proxy in front."
date: 2026-11-10
tags: ["python", "muru", "wsgi"]
draft: true
---

Everything I have shown of Muru so far has been served over plain HTTP on port 8080. That is how almost everyone runs a Python web application while developing it, and most of the time it is fine. The application in production is going to be behind HTTPS though, and there are some things which behave differently when it is, which you only find out about once it is deployed.

The usual way of testing those things locally is to put a proxy such as nginx or Caddy in front of the development server, generate a certificate for it, and then configure the application to trust the headers the proxy adds to say the original request was HTTPS. It is enough of a hassle that most people never bother. With a Muru development run it is one option.

## Turning it on

Given a WSGI application in `shop/wsgi.py`, add `--https` when starting it:

```
muructl run shop.wsgi:application --https
```

```
muru.host[61235]: preloaded shop.wsgi:application in 1 ms
muru.host[61235]: shop.wsgi:application is served as WSGI
muru.host[61235]: worker 0 started as pid 61241
muru.host[61235]: worker 0 (pid 61241) is ready
muru: serving shop.wsgi:application on http://127.0.0.1:8080 and https://127.0.0.1:8443 with 1 worker of 4 threads
...
muru: certificate for localhost, 127.0.0.1, ::1 issued by the mkcert authority in /Users/graham/Library/Application Support/mkcert (created, /Users/graham/Library/Caches/muru/certs/dev.pem)
```

The run now listens for HTTPS on port 8443 as well as HTTP on 8080, and it has created a certificate to use.

How that certificate was made depends on what you have installed. If you use [mkcert](https://github.com/FiloSottile/mkcert) and have run `mkcert -install` at some point, there is a local certificate authority on your machine which your browsers already trust. Muru finds it and issues the certificate from it, so the browser accepts the certificate without any warnings. If mkcert isn't installed, Muru falls back to creating a self-signed certificate, and prints out how to trust it, or how to install mkcert instead.

Either way, the certificate is kept in your user cache directory rather than in the project, so there is no risk of a private key ending up committed. It is reused on later runs, which the same line says by showing `reused` rather than `created`, and is only replaced when it nears expiry or is asked to cover a name it doesn't already. If you already have a certificate of your own you would prefer to use, `--tls-cert` and `--tls-key` will take that instead.

## Why bother

To see what difference HTTPS makes to the application, here is a WSGI application which reports back the URL scheme and protocol of the request, and the host it was sent to:

```python
def application(environ, start_response):
    body = f"{environ['wsgi.url_scheme']} {environ['SERVER_PROTOCOL']} {environ['HTTP_HOST']}\n".encode()
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [body]
```

Making a request to each of the two ports:

```
curl http://127.0.0.1:8080/
curl https://127.0.0.1:8443/
```

the result being:

```
http HTTP/1.1 127.0.0.1:8080
https HTTP/2.0 127.0.0.1:8443
```

Over HTTPS, the application sees `wsgi.url_scheme` set to `https`, and the request arrived as HTTP/2. Neither of these can be tested over plain HTTP. Browsers only use HTTP/2 over TLS, so if you want to know how your application behaves when a page pulls in dozens of assets over the one connection, this is the only way to find out locally. Any code which uses `wsgi.url_scheme` to construct absolute URLs, for redirects or links in emails, will get them wrong unless the request really did arrive over HTTPS. And cookies marked as `Secure`, which any session cookie in production should be, aren't sent back by the browser over plain HTTP at all. An application which sets `SESSION_COOKIE_SECURE` in its production settings can behave quite differently to the one you have been developing against.

What makes this simple to provide is how Muru is put together, which I went through in [how it fits together](/posts/2026/11/muru-how-it-fits-together/). TLS and HTTP/2 are handled by the edge, which is written in Rust and runs no Python code. By the time a request reaches the worker it has already been decrypted and parsed, and the application gets an ordinary WSGI `environ` with the scheme already set correctly. There is no proxy to configure, and no need to tell the application to trust an `X-Forwarded-Proto` header. It is also the same code which terminates TLS when running under the daemon in production, rather than something which only exists for development.

## Names other than localhost

Using `localhost` for everything gets awkward once you work on more than one project, since cookies are tied to the host name and not the port. Log in to one project on `localhost` and its session cookie gets sent to every other project you run on `localhost` too.

The `--host` option adds names to the certificate:

```
muructl run shop.wsgi:application --https --host shop.localhost
```

```
muru: certificate for localhost, 127.0.0.1, ::1, shop.localhost issued by the mkcert authority in /Users/graham/Library/Application Support/mkcert (created, /Users/graham/Library/Caches/muru/certs/dev.pem)
```

Modern browsers such as Chrome and Firefox, as well as `curl`, resolve any name ending in `.localhost` to the loopback address, so there is no need to edit `/etc/hosts` to use them. The project can then be reached at `https://shop.localhost:8443/`, with its cookies kept apart from those of any other project, and with a certificate the browser trusts for that name.

## HTTPS only

With `--https`, both HTTP and HTTPS are served, which can let a problem slip by if some page or redirect is quietly sending you back to plain HTTP. If you want to be sure everything is going over HTTPS, as it will be in production, use `--https-only` instead:

```
muructl run shop.wsgi:application --https-only --host shop.localhost
```

```
muru: serving shop.wsgi:application on https://127.0.0.1:8443 (http://127.0.0.1:8080 redirects to it) with 1 worker of 4 threads
```

Port 8080 is still listened on, but now answers every request with a redirect to the same path on the HTTPS port:

```
curl -i 'http://shop.localhost:8080/cart?item=42'
```

```
HTTP/1.1 307 Temporary Redirect
location: https://shop.localhost:8443/cart?item=42
server: muru
...
```

The redirect is a 307 rather than a 301 for two reasons. A 307 keeps the method, so a form posted to the HTTP port is posted again to the HTTPS port rather than turning into a `GET`. And browsers don't cache a 307, so if you later go back to running without HTTPS on the same port, the browser won't keep sending you off to a port where nothing is listening any more.

So you don't have to remember to type it each time, the same can be turned on for the project in `pyproject.toml`:

```toml
[tool.muru.run]
https_only = true
hosts = ["shop.localhost"]
```

These settings only apply to `muructl run`. They have no effect on how the application is served by the daemon in production, where certificates are a different matter altogether.

## What's next

None of this is especially complicated, but it is the sort of thing which only gets tested if it is easy, and getting it for free is a consequence of the edge doing all the work of facing clients. Next up I will look at what else Muru lets a single application do, which is to mix WSGI and ASGI, including handing a request from one to the other so an existing WSGI application can take on websockets.
