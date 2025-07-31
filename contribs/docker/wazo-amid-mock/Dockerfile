FROM python:3.9-slim-bullseye
LABEL maintainer="Wazo Maintainers <dev@wazo.community>"
ENV PIP_ROOT_USER_ACTION=ignore

RUN python3 -m pip install --no-cache-dir flask
COPY wazo-amid-mock.py /usr/local/bin/wazo-amid-mock.py

EXPOSE 9491

CMD ["/usr/local/bin/wazo-amid-mock.py", "9491"]
