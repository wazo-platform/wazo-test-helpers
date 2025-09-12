FROM debian:bookworm-slim
LABEL maintainer="Wazo Maintainers <dev@wazo.community>"

RUN apt-get -q update && apt-get install -yq netcat-openbsd

ADD wait /wait

CMD ["/wait"]
