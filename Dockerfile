FROM tiangolo/uwsgi-nginx-flask:python3.6
MAINTAINER Summer Students at SIB

WORKDIR /

ENV BT_TOKEN TEST
ENV PYTHONPATH "${PYTHONPATH}:/"

COPY ./backend /backend
COPY ./requirements.txt /requirements.txt

RUN pip3 install -r requirements.txt

CMD ["python3.6", "backend/DB/api/routes.py"]
