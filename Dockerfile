FROM  python:3.9.16-slim

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

WORKDIR /workspace

RUN groupadd -r valmi_group && useradd -r -g valmi_group valmi_user
RUN chown  -R valmi_user:valmi_group /workspace

USER valmi_user 

ENV PYTHONUNBUFFERED 1

ENTRYPOINT ["/workspace/docker-entrypoint.sh"]
CMD  python manage.py runserver 0.0.0.0:${PORT} --noreload