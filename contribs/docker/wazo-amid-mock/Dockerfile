FROM python:3.9-slim-bullseye
LABEL maintainer="Wazo Maintainers <dev@wazo.community>"
ENV PIP_ROOT_USER_ACTION=ignore

RUN python3 -m pip install --no-cache-dir flask
COPY mock-wazo-amid.py /usr/local/bin/mock-wazo-amid.py

EXPOSE 9491

CMD ["/usr/local/bin/mock-wazo-amid.py", "9491"]
