FROM p0bailey/docker-flask

MAINTAINER Wazo Maintainers <dev@wazo.community>

COPY mock-wazo-confd.py /usr/local/bin/mock-wazo-confd.py

EXPOSE 9486

CMD ["/usr/local/bin/mock-wazo-confd.py", "9486"]
