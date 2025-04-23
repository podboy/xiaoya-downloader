FROM python:3.12-alpine as runner

ARG VERSION

LABEL version=$VERSION

WORKDIR /app

RUN pip install --no-cache-dir xiaoya-downloader==$VERSION

EXPOSE 3000

CMD ["xiaoya-downloader", "--stdout", "--debug"]
