FROM python:3.11-slim-bookworm
LABEL maintainer="Wazo Maintainers <dev@wazo.community>"
ENV PIP_ROOT_USER_ACTION=ignore

RUN python3 -m pip install --no-cache-dir flask
COPY wazo-auth-mock.py /usr/local/bin/wazo-auth-mock.py

EXPOSE 9497

CMD ["/usr/local/bin/wazo-auth-mock.py", "9497"]
