FROM debian:bullseye-slim
LABEL maintainer="Wazo Maintainers <dev@wazo.community>"

RUN apt-get -q update && apt-get install -yq netcat

ADD wait /wait

CMD ["/wait"]
