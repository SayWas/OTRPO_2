FROM python:3.11.6

RUN mkdir /fastapi-pokeback

WORKDIR /fastapi-pokeback

COPY requirements.txt /fastapi-pokeback

RUN pip install -r requirements.txt

COPY . /fastapi-pokeback
