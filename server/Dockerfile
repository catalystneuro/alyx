FROM python:3.7-buster

# Configuration defaults
ENV ALYX_ROOT "/opt/alyx"
ENV HTTP_PORT "8000"
ENV DJANGO_USER "www-data"
ARG USER_ID=33
ENV DJANGO_USER_ID "${USER_ID}"
ENV VENV_NAME ".venv-docker"

# Setup system environment variables neded for python to run smoothly
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

# Install system requirements
RUN apt-get update && apt-get install -y \
    # postgres requirements
    libpq-dev \
    # Needed for typed-ast dependency
    build-essential \
    # python requirements
    python3-dev python3-pip python3-venv \
    # trimesh dependencies
    libspatialindex-dev && \
    # cleanup apt caches to keep image small
    rm -rf /var/lib/apt/lists/*

# Setup Python virtualenv separately from code dir in /opt/.venv-docker.
#   It needs to be outside of the code dir because the code is mounted as a volume
#   and would overwite the docker-specific venv with the incompatible host venv.
WORKDIR "$ALYX_ROOT"
ADD alyx/requirements.txt .
RUN pip install virtualenv && \
    virtualenv "/opt/$VENV_NAME"
ENV PATH="/opt/$VENV_NAME/bin:${PATH}"

# Install the python dependencies from requirements.txt into /opt/alyx/.venv-docker.
RUN pip install -r requirements.txt
RUN rm requirements.txt
RUN userdel "$DJANGO_USER" && addgroup --system --gid "$DJANGO_USER_ID" "$DJANGO_USER" && \
    adduser --system --uid "$DJANGO_USER_ID" --no-create-home --ingroup "$DJANGO_USER" --shell /bin/false "$DJANGO_USER"

# Read on venv
RUN chown -R "$DJANGO_USER_ID":"$DJANGO_USER_ID" "/opt/$VENV_NAME/"

# Workers require to write data and own the directory
RUN chown -R "$DJANGO_USER_ID":"$DJANGO_USER_ID" "/var/log/"

USER "$DJANGO_USER"

