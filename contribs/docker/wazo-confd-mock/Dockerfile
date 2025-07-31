FROM python:3.9-slim-bullseye
LABEL maintainer="Wazo Maintainers <dev@wazo.community>"
ENV PIP_ROOT_USER_ACTION=ignore

RUN python3 -m pip install --no-cache-dir flask
COPY wazo-confd-mock.py /usr/local/bin/wazo-confd-mock.py

EXPOSE 9486

CMD ["/usr/local/bin/wazo-confd-mock.py", "9486"]
