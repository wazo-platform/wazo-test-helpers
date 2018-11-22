FROM p0bailey/docker-flask
MAINTAINER Wazo Maintainers <dev@wazo.community>

COPY xivo-sysconfd-mock.py /usr/local/bin/xivo-sysconfd-mock.py

EXPOSE 8668

CMD ["/usr/local/bin/xivo-sysconfd-mock.py", "8668"]
