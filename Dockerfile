FROM python:3.10.4-alpine3.15

ENV PYTHONUNBUFFERED=1

RUN apk update && \
    apk add --no-cache \
    build-base \
    libffi-dev \
    mariadb-dev \
    && rm -rf /var/cache/apk/*


WORKDIR /app

COPY ./requirements.txt ./

RUN pip install -r requirements.txt

COPY ./ ./

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "dj_ia_py_david.wsgi:application"]
