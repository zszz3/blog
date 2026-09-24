FROM python:3.12-alpine

WORKDIR /app
COPY server/neitui_api.py server/neitui_api.py
COPY src/data/neitui.json src/data/neitui.json
RUN adduser -D -u 10001 neitui && mkdir /data && chown neitui:neitui /data
USER neitui
EXPOSE 8080
CMD ["python", "-u", "server/neitui_api.py"]
