FROM p0bailey/docker-flask

MAINTAINER Wazo Maintainers <dev@wazo.community>

COPY mock-xivo-confd.py /usr/local/bin/mock-xivo-confd.py
COPY server.crt /usr/local/share/ssl/confd/server.crt
COPY server.key /usr/local/share/ssl/confd/server.key

VOLUME ["/usr/local/share/ssl"]
EXPOSE 9497

CMD ["/usr/local/bin/mock-xivo-confd.py", "9486"]
