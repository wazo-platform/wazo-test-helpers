FROM p0bailey/docker-flask
MAINTAINER Wazo Maintainers <dev@wazo.community>

COPY wazo-auth-mock.py /usr/local/bin/wazo-auth-mock.py
COPY server.crt /usr/local/share/ssl/auth/server.crt
COPY server.key /usr/local/share/ssl/auth/server.key

EXPOSE 9497

CMD ["/usr/local/bin/wazo-auth-mock.py", "9497"]
