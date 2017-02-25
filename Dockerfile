FROM python:3-alpine

MAINTAINER Jeremy Tuloup <jerem@jtp.io>

RUN pip install trello-full-backup

RUN mkdir -p /app
WORKDIR /app

CMD ["trello-full-backup"]
