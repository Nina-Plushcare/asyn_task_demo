# Use base python image with python 3.9
FROM python:3.9
# log messages immediately
ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt