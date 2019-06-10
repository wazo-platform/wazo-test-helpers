FROM p0bailey/docker-flask

MAINTAINER Wazo Maintainers <dev@wazo.community>

COPY mock-wazo-confd.py /usr/local/bin/mock-wazo-confd.py
COPY server.crt /usr/local/share/ssl/confd/server.crt
COPY server.key /usr/local/share/ssl/confd/server.key

EXPOSE 9486

CMD ["/usr/local/bin/mock-wazo-confd.py", "9486"]
