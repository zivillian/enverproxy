  FROM python:3.9-alpine
  RUN apk --no-cache add git
  RUN pip3 install paho-mqtt
  RUN git clone https://github.com/zivillian/enverproxy.git /data/app
  RUN sed -i "s|/etc/enverproxy.conf|/data/app/enverproxy.conf|g" /data/app/enverproxy.py 
  RUN sed -i "s|mqtthost     = localhost|mqtthost     = 192.168.8.21|g" /data/app/enverproxy.conf
  RUN sed -i "s|verbosity   = 5|verbosity   = 2|g" /data/app/enverproxy.conf
  WORKDIR /data/app
  EXPOSE 1898
  CMD ["./enverproxy.py"]
  ENTRYPOINT ["python3"]
