# Estágio 1: Compilação das dependências do motor (OpenResty, ModSecurity, etc.)
FROM --platform=${BUILDPLATFORM:-linux/amd64} rockylinux:9 AS build_engine

ENV MODSECURITY_INC "/opt/nxguard/modsec/include"
ENV MODSECURITY_LIB "/opt/nxguard/modsec/lib"

RUN dnf -y install 'dnf-command(config-manager)' \
  && dnf config-manager --set-enabled devel \
  && dnf -y install \
    git wget openssl-devel gcc gcc-c++ zlib-devel make automake libtool readline-devel \
    libinput libcurl-devel pcre2-devel libxml2-devel libxslt-devel libgcrypt-devel gd-devel \
    libffi-devel rpmdevtools rpm-build rpm-devel yajl-devel lua-devel python3.12 python3.12-devel \
    yajl lua perl-ExtUtils-Embed shadow-utils util-linux python3.12-pip openldap-devel

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
RUN wget https://github.com/coreruleset/coreruleset/archive/refs/tags/v4.25.1.zip\
    && unzip -o v4.25.1.zip
RUN wget https://dl.fedoraproject.org/pub/epel/9/Everything/x86_64/Packages/l/luarocks-3.9.2-5.el9.noarch.rpm
RUN wget -O ssdeep-release-2.14.1.tar.gz \
  https://github.com/ssdeep-project/ssdeep/archive/refs/tags/release-2.14.1.tar.gz \
    && tar -xf ssdeep-release-2.14.1.tar.gz

RUN rpm -ivh luarocks-3.9.2-5.el9.noarch.rpm

WORKDIR /root/rpmbuild/SPECS

COPY packages/ssdeep.spec .
RUN rpmbuild -bb ssdeep.spec\
    && rpm -ivh /root/rpmbuild/RPMS/**/ssdeep*.rpm

COPY packages/nxguard-crs.spec .
RUN rpmbuild -bb nxguard-crs.spec

COPY packages/nxguard-engine.spec /root/rpmbuild/SPECS/
RUN rpmbuild --nobuild nxguard-engine.spec\
    && rpmbuild -bb nxguard-engine.spec

# Estágio 2: Construção do Frontend (Angular/Web)
FROM --platform=${BUILDPLATFORM:-linux/amd64} node:lts AS build_frontend

WORKDIR /app/web

COPY web/package*.json .
RUN npm install --legacy-peer-deps

COPY web /app/web
COPY *.json /app/web/

RUN npm run build

# Estágio 3: Construção do Backend Administrativo (Python/Admin)
FROM --platform=${BUILDPLATFORM:-linux/amd64} rockylinux:9 AS build_admin
ENV PYTHONUSERBASE=/opt/nxguard/site-packages
ENV PYTHONUNBUFFERED=1

RUN dnf -y install rpm-build rpmdevtools python3.12 python3.12-pip git gcc gcc-c++ libffi-devel openssl-devel \
    && rpmdev-setuptree

WORKDIR /root/rpmbuild/BUILD

COPY requirements.txt requirements.txt
RUN export PYTHONUSERBASE=/root/rpmbuild/BUILD/site-packages \
    && pip3.12 install --user -r requirements.txt

WORKDIR /root/rpmbuild/BUILD/admin

COPY --from=build_frontend /app/web/dist /root/rpmbuild/BUILD/admin/static
COPY --from=build_frontend /app/web/dist/index.html /root/rpmbuild/BUILD/admin/templates/
COPY --from=build_frontend /app/web/package.json /root/rpmbuild/BUILD/admin/

COPY *.py .
COPY api api
COPY engine engine
COPY lualib /root/rpmbuild/BUILD/luajit

WORKDIR /root/rpmbuild/SPECS
COPY packages/nxguard-admin.spec .
RUN rpmbuild --nobuild nxguard-admin.spec \
    && rpmbuild -bb nxguard-admin.spec

# Estágio 4: Imagem Final (Runtime)
FROM --platform=${BUILDPLATFORM:-linux/amd64} rockylinux:9-minimal AS main
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
    python3.12 \
    yajl \
    lua \
  && microdnf clean all

COPY --from=build_engine /root/rpmbuild/RPMS/**/*.rpm /RPMS/
COPY --from=build_admin /root/rpmbuild/RPMS/**/*.rpm /RPMS/

RUN rpm -ivh /RPMS/*.rpm && rm -rf /RPMS\
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
