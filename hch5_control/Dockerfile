ARG BUILD_FROM
FROM ${BUILD_FROM}

RUN apk add --no-cache git tzdata \
 && pip install --no-cache-dir pyserial==3.5 paho-mqtt PyYAML

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
CMD ["python3", "-u", "/start.py"]
