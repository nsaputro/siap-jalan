ARG BUILD_FROM
FROM $BUILD_FROM

WORKDIR /app

# Install Python deps first (better layer caching)
COPY app/requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY ui/ ./static/
COPY data/activity_templates.json ./data/activity_templates.json

# Entrypoint
COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
