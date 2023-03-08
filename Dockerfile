FROM python:3.10

ARG USER_ID
ARG GROUP_ID

COPY requirements.txt /tmp/requirements.txt
RUN set -x \
    && python -m venv /opt/valmi-app-backend \
    && /opt/valmi-app-backend/bin/python -m pip install -U pip -r /tmp/requirements.txt \
    && mkdir -p /workspace && chown -R $USER_ID:$GROUP_ID /workspace && chown -R $USER_ID:$GROUP_ID /opt/valmi-app-backend
#RUN addgroup --gid $GROUP_ID user
#RUN adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID user
 
#USER user

WORKDIR /workspace
#COPY . /workspace/
ENV PATH="/opt/valmi-app-backend/bin:${PATH}"
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /workspace/src
EXPOSE ${PORT}
#TODO: first time install - create db and run migrations and other stuff
ENTRYPOINT ["/workspace/docker-entrypoint.sh"]
CMD  python manage.py runserver ${PORT}
