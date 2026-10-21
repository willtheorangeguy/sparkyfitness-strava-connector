FROM python:3.12.13-alpine
RUN apk add --no-cache tzdata
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY pyproject.toml LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir --no-deps . && adduser -D -u 10001 connector && mkdir /data && chown connector /data
USER connector
ENV DATA_DIR=/data PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
VOLUME ["/data"]
ENTRYPOINT ["sparkyfitness-strava"]
CMD ["watch"]
