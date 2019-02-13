FROM p0bailey/docker-flask

MAINTAINER Wazo Maintainers <dev@wazo.community>

COPY mock-xivo-amid.py /usr/local/bin/mock-xivo-amid.py
COPY server.crt /usr/local/share/ssl/amid/server.crt
COPY server.key /usr/local/share/ssl/amid/server.key

EXPOSE 9491

CMD ["/usr/local/bin/mock-xivo-amid.py", "9491"]
