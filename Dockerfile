FROM python:3.10-slim-bullseye

ARG YOUR_ENV

ENV YOUR_ENV=${YOUR_ENV} \
    PYTHOHNFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.2

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

COPY . .

RUN ["chmod", "+x", "install_geckodriver.sh"]
RUN ./install_geckodriver.sh
ENV PATH="${PATH}:/app/bin/"

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

CMD ["python", "./main.py"]