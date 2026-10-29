ARG BUILD_FROM
FROM ${BUILD_FROM}

RUN apk add --no-cache git tzdata \
 && pip install --no-cache-dir pyserial==3.5 paho-mqtt==2.1.0 PyYAML==6.0.3

ARG SOURCE_REPO
ARG SOURCE_REF
RUN git init -q /src \
 && git -C /src fetch -q --depth 1 "${SOURCE_REPO}" "${SOURCE_REF}" \
 && git -C /src checkout -q FETCH_HEAD \
 && mkdir -p /opt/dantherm-passivelink-webui \
 && cp /src/VERSION /src/gateway/*.py /opt/dantherm-passivelink-webui/ \
 && cp -r /src/gateway/webui /opt/dantherm-passivelink-webui/webui \
 && cp /src/docker/proxy/readonly_proxy.py /opt/bus_guard.py \
 && rm -rf /src

COPY start.py /start.py
WORKDIR /opt/dantherm-passivelink-webui
# s6 starts CMD without the container environment; with-contenv restores it,
# so TZ from Home Assistant reaches the controller (week plan, night mode).
CMD ["/command/with-contenv", "python3", "-u", "/start.py"]
