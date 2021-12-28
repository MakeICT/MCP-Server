# syntax=docker/dockerfile:1

# FROM python:3.9-slim-bullseye

FROM python:3.9-slim-bullseye

RUN useradd mcp

WORKDIR /home/mcp

# WORKDIR /app

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pip install pipenv
RUN pipenv install --system --dev

COPY . .

RUN chown -R mcp:mcp ./
RUN chmod +x boot.sh

USER mcp 

# RUN flask setup default

# CMD [ "python", "-m", "flask", "run", "--host=0.0.0.0"]
# ENTRYPOINT ["./boot.sh"]