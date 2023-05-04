FROM python:3.9-slim-bullseye
MAINTAINER Wazo Maintainers <dev@wazo.community>

RUN python3 -m pip install --no-cache-dir flask
COPY wazo-auth-mock.py /usr/local/bin/wazo-auth-mock.py

EXPOSE 9497

CMD ["/usr/local/bin/wazo-auth-mock.py", "9497"]
