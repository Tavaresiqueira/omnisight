FROM postgres:16-alpine
RUN apk add --no-cache age bash && adduser -D -u 10001 backup \
    && mkdir -m 0700 /backups && chown backup:backup /backups
COPY deploy/backup/backup.sh /scripts/backup.sh
USER backup
ENTRYPOINT ["/bin/bash", "/scripts/backup.sh"]
