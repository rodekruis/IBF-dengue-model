FROM python:3.7.10-buster

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

RUN deps='build-essential gdal-bin python-gdal libgdal-dev kmod wget' && \
	apt-get update && \
	apt-get install -y $deps

RUN pip install --upgrade pip && \
	pip install GDAL==$(gdal-config --version)

WORKDIR /mosquito_model
ADD mosquito_model .
RUN pip install .