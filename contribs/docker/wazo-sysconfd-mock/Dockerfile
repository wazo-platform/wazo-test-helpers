FROM python:3.9-slim-bullseye
MAINTAINER Wazo Maintainers <dev@wazo.community>

RUN python3 -m pip install --no-cache-dir flask
COPY wazo-sysconfd-mock.py /usr/local/bin/wazo-sysconfd-mock.py

EXPOSE 8668

CMD ["/usr/local/bin/wazo-sysconfd-mock.py", "8668"]
