FROM python:3.6
LABEL maintainer="Ravi Kumar Srirangam"
RUN mkdir /app
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
EXPOSE 5000
ENTRYPOINT [ "python" ]
CMD [ "openscale.py" ]
