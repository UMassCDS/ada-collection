FROM python:3.8-slim

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN deps='build-essential cmake gdal-bin python-gdal libgdal-dev kmod wget apache2' && \
	apt-get update && \
	apt-get install -y $deps && \
	pip install --upgrade pip && \
	pip install GDAL==$(gdal-config --version)

WORKDIR /neo
ADD . .
RUN pip install .