FROM debian:stretch
MAINTAINER Wazo Maintainers <dev@wazo.community>

RUN apt-get update && apt-get install -y netcat

ADD wait /wait

CMD ["/wait"]
