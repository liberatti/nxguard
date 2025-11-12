FROM --platform=${BUILDPLATFORM:-linux/amd64} rockylinux:9 AS engine

ENV MODSECURITY_INC "/opt/nxguard/modsec/include"
ENV MODSECURITY_LIB "/opt/nxguard/modsec/lib"

RUN dnf -y install 'dnf-command(config-manager)' \
  && dnf config-manager --set-enabled devel \
  && dnf -y install \
    git wget openssl-devel gcc gcc-c++ zlib-devel make automake libtool readline-devel \
    libinput libcurl-devel pcre2-devel libxml2-devel libxslt-devel libgcrypt-devel gd-devel \
    libffi-devel rpmdevtools rpm-build rpm-devel yajl-devel lua-devel python3.12 python3.12-devel \
    yajl lua perl-ExtUtils-Embed shadow-utils util-linux python3.12-pip openldap-devel \
  && dnf clean all

WORKDIR /root/rpmbuild/SPECS
COPY packages/ssdeep.spec .
RUN rpmbuild -bb ssdeep.spec \
  && rpm -ivh /root/rpmbuild/RPMS/**/ssdeep-*.rpm

RUN wget https://dl.fedoraproject.org/pub/epel/9/Everything/x86_64/Packages/l/luarocks-3.9.2-5.el9.noarch.rpm \
  && rpm -ivh luarocks-3.9.2-5.el9.noarch.rpm \
  && rm -f luarocks-3.9.2-5.el9.noarch.rpm

COPY packages/nxguard-openresty.spec /root/rpmbuild/SPECS/
RUN rpmbuild -bb nxguard-openresty.spec

FROM --platform=${BUILDPLATFORM:-linux/amd64} node:lts AS frontend

WORKDIR /app
RUN mkdir web
COPY web/package*.json web/
RUN cd web \
 && npm install \
 && npm cache clean --force

COPY web web
COPY *.json web/

RUN cd web && npm run build

FROM --platform=${BUILDPLATFORM:-linux/amd64} rockylinux:9-minimal AS main

ENV PATH ${PATH}:/opt/nxguard/.local/bin:/opt/nxguard/nginx/sbin
ENV LUA_PATH "/opt/nxguard/lualib/share/lua/5.4/?.lua;/opt/nxguard/lualib/share/lua/5.4/resty/?.lua;;"
ENV LUA_CPATH "/opt/nxguard/lualib/lib64/lua/5.4/?.so;/opt/nxguard/lualib/lib/?.so;/opt/nxguard/lualib/?.so;;"
ENV PYTHONUSERBASE /opt/nxguard/site-packages

RUN microdnf install -y procps openssl bind-utils shadow-utils util-linux gcc-c++ \
    libX11 libXext libXi libXrender libXtst freetype sudo \
    python3.12 python3.12-devel python3.12-pip yajl lua wget git\
  && microdnf update -y\
  && microdnf clean all\
  && python3.12 -m pip install --upgrade pip\
  && python3.12 -m pip install --upgrade setuptools

COPY --from=engine /root/rpmbuild/RPMS/**/*.rpm /RPMS/
RUN rpm -ivh /RPMS/*.rpm && rm -rf /RPMS

WORKDIR /opt/nxguard/admin

COPY requirements.txt .
RUN pip3.12 install -r requirements.txt

COPY *.py .
COPY api api
COPY engine engine
RUN mkdir -p /opt/nxguard/luajit/share/lua/5.1/nxguard/
COPY lualib /opt/nxguard/luajit/share/lua/5.1/nxguard/

COPY --from=frontend /app/web/dist /opt/nxguard/admin/static
COPY --from=frontend /app/web/dist/index.html /opt/nxguard/admin/templates/

RUN chown -R nxguard /opt/nxguard

USER nxguard

EXPOSE 5000
EXPOSE 80
EXPOSE 443

VOLUME [ "/data" ]
#ENV EVENTLET_NO_GREENDNS yes
ENTRYPOINT ["gunicorn", "-c", "gunicorn.conf.py", "main:app"]
#ENTRYPOINT ["gunicorn", "-k", "eventlet", "-w", "4", "main:app", "-b", "0.0.0.0:5000","--preload"]