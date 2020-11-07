FROM python:3.7-slim as base
ENV PYROOT /pyroot
ENV PYTHONUSERBASE $PYROOT

FROM base AS builder
RUN pip install 'pipenv==2018.11.26'
#RUN apk add --no-cache gcc g++
#g++ libnsl libnsl-dev freetype
#RUN pip install pipenv

WORKDIR /build
COPY Pipfile* ./
RUN PIP_USER=1 PIP_IGNORE_INSTALLED=1 pipenv install --system --deploy --ignore-pipfile

FROM base
WORKDIR /hyperflow-viz-trace
COPY --from=builder $PYROOT/lib/ $PYROOT/lib/
COPY main.py ./
COPY bin.sh /usr/bin/hflow-viz-trace 
RUN chmod +x /usr/bin/hflow-viz-trace
