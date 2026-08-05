# codedge-runner — g++ + nsjail 沙箱 + FastAPI（B 機部署，見 docs/server-plan.md）
# nsjail 不在 Debian/Ubuntu 官方套件庫，需自 source 建置（stage 1，僅 build 時一次）。

# ---- Stage 1: build nsjail ----
FROM ubuntu:24.04 AS nsjail-build
RUN apt-get update && apt-get install -y --no-install-recommends \
    autoconf bison flex gcc g++ git libprotobuf-dev libnl-route-3-dev \
    libtool make pkg-config protobuf-compiler ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/google/nsjail.git /nsjail \
    && make -C /nsjail -j"$(nproc)"

# ---- Stage 2: runtime ----
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ python3 python3-venv libprotobuf32t64 libnl-route-3-200 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=nsjail-build /nsjail/nsjail /usr/local/bin/nsjail

# PCH：預編常用標準庫標頭（compiler.py 以 -include /opt/pch/std.h 掛上）
# 旗標必須與 config.cxx_flags 完全一致，否則 g++ 拒用 .gch
RUN mkdir -p /opt/pch && printf '%s\n' \
    '#include <iostream>' '#include <iomanip>' '#include <fstream>' \
    '#include <sstream>' '#include <string>' '#include <vector>' \
    '#include <array>' '#include <map>' '#include <set>' \
    '#include <algorithm>' '#include <numeric>' '#include <cmath>' \
    '#include <cstdlib>' '#include <cstring>' '#include <ctime>' \
    > /opt/pch/std.h \
    && g++ -std=c++17 -O0 -Wall -x c++-header /opt/pch/std.h -o /opt/pch/std.h.gch

WORKDIR /srv
COPY requirements.txt .
RUN python3 -m venv /venv && /venv/bin/pip install --no-cache-dir -r requirements.txt
COPY app ./app

ENV RUNNER_SANDBOX=nsjail
EXPOSE 8080
# nsjail 需要 CAP_SYS_ADMIN 等權限 → compose 端設定（R5），此處僅定義行為
CMD ["/venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
