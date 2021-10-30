ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}-slim
WORKDIR /usr/src/app
COPY . .
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y gcc g++ curl
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python
ENV PATH="${PATH}:/root/.local/bin"
ENV VIRTUAL_ENV "/usr/src/venv"
RUN python -m venv $VIRTUAL_ENV
ENV PATH "$VIRTUAL_ENV/bin:$PATH"
RUN poetry install
