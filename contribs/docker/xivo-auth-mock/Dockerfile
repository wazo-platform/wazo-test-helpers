FROM p0bailey/docker-flask
MAINTAINER Wazo Maintainers <dev@wazo.community>

COPY mock-xivo-auth.py /usr/local/bin/mock-xivo-auth.py
COPY server.crt /usr/local/share/ssl/auth/server.crt
COPY server.key /usr/local/share/ssl/auth/server.key

VOLUME ["/usr/local/share/ssl"]
EXPOSE 9497

CMD ["/usr/local/bin/mock-xivo-auth.py", "9497"]
