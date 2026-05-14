FROM python:3.11-slim

# HF Spaces convention: non-root user, UID 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Install dependencies first so the layer caches well
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy the project
COPY --chown=user . .

# HF Spaces routes traffic to whatever port we listen on (see README YAML app_port)
EXPOSE 7860

ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

CMD ["streamlit", "run", "app/streamlit_app.py", \
     "--server.port=7860", \
     "--server.address=0.0.0.0"]
