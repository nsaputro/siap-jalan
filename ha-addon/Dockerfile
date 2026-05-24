ARG BUILD_FROM
FROM $BUILD_FROM

WORKDIR /app

# Install Python deps first (better layer caching)
COPY ha-addon/app/requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY ha-addon/app/ ./app/
COPY ha-addon/ui/ ./static/
COPY data/activity_templates.json ./data/activity_templates.json

# Entrypoint
COPY ha-addon/run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
