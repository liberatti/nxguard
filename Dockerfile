# Dockerfile para o projeto nxguard
# Este arquivo utiliza build multi-stage para compilar componentes do motor (engine),
# frontend e backend administrativo, resultando em uma imagem final otimizada.

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

RUN	wget https://openresty.org/download/openresty-1.27.1.1.tar.gz\
    && tar -xf openresty-1.27.1.1.tar.gz
RUN wget https://github.com/SpiderLabs/ModSecurity/releases/download/v3.0.12/modsecurity-v3.0.12.tar.gz\
    && tar -xf modsecurity-v3.0.12.tar.gz
RUN wget https://github.com/SpiderLabs/ModSecurity-nginx/releases/download/v1.0.3/modsecurity-nginx-v1.0.3.tar.gz\
    && tar -xf modsecurity-nginx-v1.0.3.tar.gz
RUN wget https://github.com/liberatti/nginx-sticky-module-ng/archive/refs/tags/1.2.6.tar.gz\
    && tar -xf 1.2.6.tar.gz
RUN wget https://github.com/liberatti/nginx_upstream_check_module/archive/refs/tags/0.4.1.tar.gz\
    && tar -xf 0.4.1.tar.gz
RUN wget https://github.com/liberatti/nginx_ajp_module/archive/refs/tags/v1.0.0.tar.gz\
    && tar -xf v1.0.0.tar.gz
RUN wget https://www.lua.org/ftp/lua-5.1.5.tar.gz\
    && tar -xf lua-5.1.5.tar.gz
RUN wget https://github.com/coreruleset/coreruleset/archive/refs/tags/v3.3.6.zip\
    && unzip -o v3.3.6.zip
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
RUN npm install

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

RUN rpm -ivh /RPMS/*.rpm && rm -rf /RPMS

WORKDIR /opt/nxguard/admin

USER nxguard

EXPOSE 5000

VOLUME [ "/data" ]

ENTRYPOINT ["gunicorn", "-c", "api/gunicorn_config.py", "main:app"]