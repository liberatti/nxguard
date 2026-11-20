# Estágio 1: Compilação das dependências do motor (Nginx, ModSecurity, etc.)
FROM rockylinux:10 AS build_engine

ENV MODSECURITY_INC "/opt/nxguard/modsec/include"
ENV MODSECURITY_LIB "/opt/nxguard/modsec/lib"

RUN dnf -y install 'dnf-command(config-manager)' epel-release \
  && (dnf config-manager --set-enabled crb || dnf config-manager --set-enabled devel || true) \
  && dnf -y install \
    git wget openssl-devel gcc gcc-c++ zlib-devel make automake libtool readline-devel \
    libinput libcurl-devel pcre2-devel libxml2-devel libxslt-devel libgcrypt-devel gd-devel \
    libffi-devel rpmdevtools rpm-build rpm-devel lua-devel python3 python3-devel \
    lua perl-ExtUtils-Embed shadow-utils util-linux python3-pip openldap-devel luarocks unzip cmake

WORKDIR /root/rpmbuild/BUILD

RUN wget https://nginx.org/download/nginx-1.31.9.tar.gz \
    && tar -xf nginx-1.31.9.tar.gz
RUN wget https://github.com/openresty/luajit2/archive/refs/tags/v2.1-20240815.tar.gz -O luajit2-2.1-20240815.tar.gz \
    && tar -xf luajit2-2.1-20240815.tar.gz
RUN wget https://github.com/vision5/ngx_devel_kit/archive/refs/tags/v0.3.3.tar.gz -O ngx_devel_kit-0.3.3.tar.gz \
    && tar -xf ngx_devel_kit-0.3.3.tar.gz
RUN wget https://github.com/openresty/lua-nginx-module/archive/refs/tags/v0.10.32rc7.tar.gz -O lua-nginx-module-0.10.32rc7.tar.gz \
    && tar -xf lua-nginx-module-0.10.32rc7.tar.gz
RUN wget https://github.com/openresty/lua-upstream-nginx-module/archive/refs/tags/v0.08.tar.gz -O lua-upstream-nginx-module-0.08.tar.gz \
    && tar -xf lua-upstream-nginx-module-0.08.tar.gz
RUN wget https://github.com/openresty/headers-more-nginx-module/archive/refs/tags/v0.38.tar.gz -O headers-more-nginx-module-0.38.tar.gz \
    && tar -xf headers-more-nginx-module-0.38.tar.gz
RUN wget https://github.com/openresty/lua-resty-core/archive/refs/tags/v0.1.35rc3.tar.gz -O lua-resty-core-0.1.35rc3.tar.gz \
    && tar -xf lua-resty-core-0.1.35rc3.tar.gz
RUN wget https://github.com/openresty/lua-resty-lrucache/archive/refs/tags/v0.15.tar.gz -O lua-resty-lrucache-0.15.tar.gz \
    && tar -xf lua-resty-lrucache-0.15.tar.gz
RUN wget https://github.com/openresty/lua-cjson/archive/refs/tags/2.1.0.14.tar.gz -O lua-cjson-2.1.0.14.tar.gz \
    && tar -xf lua-cjson-2.1.0.14.tar.gz
RUN wget https://github.com/openresty/lua-tablepool/archive/refs/tags/v0.02.tar.gz -O lua-tablepool-0.02.tar.gz \
    && tar -xf lua-tablepool-0.02.tar.gz
RUN wget https://github.com/openresty/lua-resty-string/archive/refs/tags/v0.15.tar.gz -O lua-resty-string-0.15.tar.gz \
    && tar -xf lua-resty-string-0.15.tar.gz
RUN wget https://github.com/openresty/lua-resty-lock/archive/refs/tags/v0.09.tar.gz -O lua-resty-lock-0.09.tar.gz \
    && tar -xf lua-resty-lock-0.09.tar.gz
RUN wget https://github.com/openresty/lua-resty-limit-traffic/archive/refs/tags/v0.09.tar.gz -O lua-resty-limit-traffic-0.09.tar.gz \
    && tar -xf lua-resty-limit-traffic-0.09.tar.gz
RUN wget https://github.com/openresty/lua-resty-upstream-healthcheck/archive/refs/tags/v0.10.tar.gz -O lua-resty-upstream-healthcheck-0.10.tar.gz \
    && tar -xf lua-resty-upstream-healthcheck-0.10.tar.gz
RUN wget https://github.com/SpiderLabs/ModSecurity/releases/download/v3.0.14/modsecurity-v3.0.14.tar.gz\
    && tar -xf modsecurity-v3.0.14.tar.gz
RUN wget https://github.com/SpiderLabs/ModSecurity-nginx/releases/download/v1.0.4/modsecurity-nginx-v1.0.4.tar.gz\
    && tar -xf modsecurity-nginx-v1.0.4.tar.gz
RUN wget https://github.com/liberatti/nginx_ajp_module/archive/refs/tags/v1.0.0.tar.gz\
    && tar -xf v1.0.0.tar.gz
RUN wget https://www.lua.org/ftp/lua-5.1.5.tar.gz\
    && tar -xf lua-5.1.5.tar.gz
RUN wget https://github.com/coreruleset/coreruleset/archive/refs/tags/v4.25.2.zip\
    && unzip -o v4.25.2.zip
RUN wget -O ssdeep-release-2.14.1.tar.gz \
  https://github.com/ssdeep-project/ssdeep/archive/refs/tags/release-2.14.1.tar.gz \
    && tar -xf ssdeep-release-2.14.1.tar.gz
RUN wget https://github.com/lloyd/yajl/archive/refs/tags/2.1.0.tar.gz -O yajl-2.1.0.tar.gz \
    && tar -xf yajl-2.1.0.tar.gz

WORKDIR /root/rpmbuild/SPECS

COPY packages/yajl.spec .
RUN rpmbuild -bb yajl.spec \
    && rpm -ivh /root/rpmbuild/RPMS/**/yajl*.rpm

COPY packages/ssdeep.spec .
RUN rpmbuild -bb ssdeep.spec\
    && rpm -ivh /root/rpmbuild/RPMS/**/ssdeep*.rpm

COPY packages/nxguard-crs.spec .
RUN rpmbuild -bb nxguard-crs.spec

COPY packages/nxguard-engine.spec /root/rpmbuild/SPECS/
RUN rpmbuild --nobuild nxguard-engine.spec\
    && QA_RPATHS=0x0003 rpmbuild -bb nxguard-engine.spec

# Estágio 2: Construção do Frontend (Angular/Web)
FROM --platform=${BUILDPLATFORM:-linux/amd64} node:lts AS build_frontend

WORKDIR /app/web

COPY web/package*.json .
RUN npm install --legacy-peer-deps

COPY web /app/web
COPY *.json /app/web/

RUN npm run build

# Estágio 3: Construção do Backend Administrativo (Python/Admin)
FROM rockylinux:10 AS build_admin
ENV PYTHONUSERBASE=/opt/nxguard/site-packages
ENV PYTHONUNBUFFERED=1
ENV PIP_BREAK_SYSTEM_PACKAGES=1

RUN dnf -y install rpm-build rpmdevtools python3 python3-pip git gcc gcc-c++ libffi-devel openssl-devel \
    && rpmdev-setuptree

WORKDIR /root/rpmbuild/BUILD

COPY requirements.txt requirements.txt
RUN export PYTHONUSERBASE=/root/rpmbuild/BUILD/site-packages \
    && python3 -m pip install --user --ignore-installed --break-system-packages -r requirements.txt

WORKDIR /root/rpmbuild/BUILD/admin

COPY --from=build_frontend /app/web/dist /root/rpmbuild/BUILD/admin/static
COPY --from=build_frontend /app/web/dist/index.html /root/rpmbuild/BUILD/admin/templates/
COPY --from=build_frontend /app/web/package.json /root/rpmbuild/BUILD/admin/

COPY *.py .
COPY api api
COPY engine engine
COPY engine/lua/nxguard /root/rpmbuild/BUILD/luajit

WORKDIR /root/rpmbuild/SPECS
COPY packages/nxguard-admin.spec .
RUN rpmbuild --nobuild nxguard-admin.spec \
    && rpmbuild -bb nxguard-admin.spec

# Estágio de Exportação dos RPMs
FROM scratch AS rpms
COPY --from=build_engine /root/rpmbuild/RPMS/ /
COPY --from=build_admin /root/rpmbuild/RPMS/ /

# Estágio 4: Imagem Final (Runtime)
FROM rockylinux:10-minimal AS main
ENV APP_BASE=/opt/nxguard
ENV PATH ${PATH}:/opt/nxguard/.local/bin:/opt/nxguard/nginx/sbin:/opt/nxguard/site-packages/bin
ENV LUA_PATH "/opt/nxguard/lualib/share/lua/5.4/?.lua;/opt/nxguard/lualib/share/lua/5.4/resty/?.lua;;"
ENV LUA_CPATH "/opt/nxguard/lualib/lib64/lua/5.4/?.so;/opt/nxguard/lualib/lib/?.so;/opt/nxguard/lualib/?.so;;"
ENV PYTHONUSERBASE /opt/nxguard/site-packages
ENV PYTHONUNBUFFERED 1
RUN microdnf install -y \
    procps \
    openssl \
    bind-utils \
    shadow-utils \
    util-linux \
    sudo \
    python3 \
    python3-requests \
    lua \
  && microdnf clean all

COPY --from=build_engine /root/rpmbuild/RPMS/**/*.rpm /RPMS/
COPY --from=build_admin /root/rpmbuild/RPMS/**/*.rpm /RPMS/

RUN rm -f /RPMS/*-devel*.rpm \
 && rpm -ivh /RPMS/*.rpm && rm -rf /RPMS\
 && mkdir -p /data\
 && chown -R nxguard:nxguard /data\
 && chmod 775 /data

WORKDIR /opt/nxguard/admin

USER nxguard

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 cli.py health_check

VOLUME [ "/data" ]

ENTRYPOINT ["gunicorn", "-c", "api/gunicorn_config.py", "main:app"]
