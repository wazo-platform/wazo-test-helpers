FROM p0bailey/docker-flask
MAINTAINER Wazo Maintainers <dev@wazo.community>

COPY wazo-sysconfd-mock.py /usr/local/bin/wazo-sysconfd-mock.py

EXPOSE 8668

CMD ["/usr/local/bin/wazo-sysconfd-mock.py", "8668"]
