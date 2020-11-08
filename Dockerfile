FROM python:3.8-slim as builder
WORKDIR /usr/src/app

COPY ./hyperflow_viz_trace ./hyperflow_viz_trace
COPY ./setup.py .
RUN pip install -e .
