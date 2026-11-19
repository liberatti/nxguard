Name:		nxguard-engine
Version:	1.31.9
Release:	1%{?dist}
Summary:	nxguard engine powered by nginx

License:	Apache-2.0
Source0:	%{name}-%{version}.tar.gz    

BuildRequires: openldap-devel luarocks openssl-devel gcc gcc-c++ zlib-devel openssl-devel make automake libtool readline-devel libinput libcurl-devel pcre2-devel libxml2-devel libxslt-devel libgcrypt-devel gd-devel perl-ExtUtils-Embed
Requires: bash, lua, ssdeep = 2.14.1, shadow-utils, util-linux, sudo

%undefine __brp_mangle_shebangs 

%description
nxguard engine core based on NGINX with LuaJIT and ModSecurity.

%prep

cd /root/rpmbuild/BUILD

install -d nginx-1.31.9/modules
mv ModSecurity-nginx-v1.0.4 nginx-1.31.9/modules/modsecurity-nginx-v1.0.4
mv nginx_ajp_module-1.0.0 nginx-1.31.9/modules/
mv ngx_devel_kit-0.3.3 nginx-1.31.9/modules/
mv lua-nginx-module-0.10.32rc7 nginx-1.31.9/modules/
mv lua-upstream-nginx-module-0.08 nginx-1.31.9/modules/
mv headers-more-nginx-module-0.38 nginx-1.31.9/modules/

%build
cd /root/rpmbuild/BUILD/lua-5.1.5
make -j$(nproc) linux

cd /root/rpmbuild/BUILD/modsecurity-v3.0.14
./configure --prefix=/opt/nxguard/modsec --with-yajl --with-pcre2 --with-ssdeep --with-lua
make -j 4
make install

cd /root/rpmbuild/BUILD/luajit2-2.1-20240815
make -j$(nproc) PREFIX=/opt/nxguard/luajit
make install PREFIX=/opt/nxguard/luajit DESTDIR=/root/rpmbuild/BUILD/luajit-build

cd /root/rpmbuild/BUILD/nginx-1.31.9
export LUAJIT_LIB=/root/rpmbuild/BUILD/luajit-build/opt/nxguard/luajit/lib
export LUAJIT_INC=/root/rpmbuild/BUILD/luajit-build/opt/nxguard/luajit/include/luajit-2.1
./configure --with-compat \
    --with-http_ssl_module \
    --with-stream \
    --with-stream_ssl_module \
    --with-stream_ssl_preread_module \
    --with-http_stub_status_module \
    --with-http_v2_module \
    --with-debug \
    --with-cc-opt='-D FD_SETSIZE=32768 -Wno-error' \
    --with-ld-opt='-Wl,-rpath,/opt/nxguard/luajit/lib' \
    --add-module=modules/ngx_devel_kit-0.3.3 \
    --add-module=modules/lua-nginx-module-0.10.32rc7 \
    --add-module=modules/lua-upstream-nginx-module-0.08 \
    --add-module=modules/headers-more-nginx-module-0.38 \
    --add-dynamic-module=modules/nginx_ajp_module-1.0.0 \
    --add-dynamic-module=modules/modsecurity-nginx-v1.0.4 \
    --prefix=/opt/nxguard \
    --conf-path=/opt/nxguard/nginx/conf/nginx.conf \
    --sbin-path=/opt/nxguard/nginx/sbin/nginx \
    --modules-path=/opt/nxguard/nginx/modules
sed -i 's/-Werror//g' objs/Makefile
make -j 4

%install
install -d %{buildroot}/opt/nxguard/html
install -d %{buildroot}/opt/nxguard/logs
install -d %{buildroot}/opt/nxguard/run
install -d %{buildroot}/opt/nxguard/cache
install -d %{buildroot}/opt/nxguard/data
install -d %{buildroot}/opt/nxguard/temp/client_body
install -d %{buildroot}/opt/nxguard/temp/fastcgi
install -d %{buildroot}/opt/nxguard/temp/proxy
install -d %{buildroot}/opt/nxguard/temp/scgi
install -d %{buildroot}/opt/nxguard/temp/uwsgi

install -d %{buildroot}/opt/nxguard/nginx/conf
install -d %{buildroot}/opt/nxguard/nginx/sbin
install -d %{buildroot}/opt/nxguard/nginx/modules

install -d %{buildroot}/opt/nxguard/luajit/bin
install -d %{buildroot}/opt/nxguard/luajit/lib
install -d %{buildroot}/opt/nxguard/luajit/include/luajit-2.1
install -d %{buildroot}/opt/nxguard/luajit/share/luajit-2.1/jit
install -d %{buildroot}/opt/nxguard/luajit/share/lua/5.1
install -d %{buildroot}/opt/nxguard/luajit/lib/lua/5.1

install -d %{buildroot}/opt/nxguard/lualib/cjson
install -d %{buildroot}/opt/nxguard/lualib/resty
install -d %{buildroot}/opt/nxguard/lualib/ngx

install -d %{buildroot}/opt/nxguard/luajit/include/lua-5.1

cd /root/rpmbuild/BUILD/lua-5.1.5/src
install -p -m 0755 lua luac %{buildroot}/opt/nxguard/luajit/bin
install -p -m 0644 lua.h luaconf.h lualib.h lauxlib.h ../etc/lua.hpp %{buildroot}/opt/nxguard/luajit/include/lua-5.1
install -p -m 0644 liblua.a %{buildroot}/opt/nxguard/luajit/lib/lua/5.1

cd /root/rpmbuild/BUILD/luajit2-2.1-20240815
make install PREFIX=/opt/nxguard/luajit DESTDIR=%{buildroot}

cd /root/rpmbuild/BUILD/lua-cjson-2.1.0.14
make LUA_INCLUDE_DIR=%{buildroot}/opt/nxguard/luajit/include/luajit-2.1
install -m 0755 cjson.so %{buildroot}/opt/nxguard/lualib/cjson.so
install -m 0644 lua/cjson/*.lua %{buildroot}/opt/nxguard/lualib/cjson/ || :

cd /root/rpmbuild/BUILD/lua-resty-core-0.1.35rc3
make install PREFIX=%{buildroot}/opt/nxguard/lualib

cd /root/rpmbuild/BUILD/lua-resty-lrucache-0.15
make install PREFIX=%{buildroot}/opt/nxguard/lualib

if [ -d %{buildroot}/opt/nxguard/lualib/lib/lua ]; then
  cp -r %{buildroot}/opt/nxguard/lualib/lib/lua/* %{buildroot}/opt/nxguard/lualib/ 2>/dev/null || :
  rm -rf %{buildroot}/opt/nxguard/lualib/lib
fi

cd /root/rpmbuild/BUILD/lua-tablepool-0.02
install lib/*.lua %{buildroot}/opt/nxguard/lualib/

cd /root/rpmbuild/BUILD/lua-resty-string-0.15
install lib/resty/*.lua %{buildroot}/opt/nxguard/lualib/resty/

cd /root/rpmbuild/BUILD/lua-resty-lock-0.09
install lib/resty/*.lua %{buildroot}/opt/nxguard/lualib/resty/

cd /root/rpmbuild/BUILD/lua-resty-limit-traffic-0.09
install -d %{buildroot}/opt/nxguard/lualib/resty/limit
install lib/resty/limit/*.lua %{buildroot}/opt/nxguard/lualib/resty/limit/

cd /root/rpmbuild/BUILD/lua-resty-upstream-healthcheck-0.10
install -d %{buildroot}/opt/nxguard/lualib/resty/upstream
install lib/resty/upstream/*.lua %{buildroot}/opt/nxguard/lualib/resty/upstream/

luarocks config lua_dir %{buildroot}/opt/nxguard/luajit
luarocks install --tree=/root/rpmbuild/BUILD/lualib lualdap --lua-version=5.1
luarocks install --tree=/root/rpmbuild/BUILD/lualib base64 --lua-version=5.1
install /root/rpmbuild/BUILD/lualib/share/lua/5.1/*.lua %{buildroot}/opt/nxguard/lualib/

luarocks install --tree=/root/rpmbuild/BUILD/lualib lua-resty-http --lua-version=5.1
luarocks install --tree=/root/rpmbuild/BUILD/lualib lua-resty-redis --lua-version=5.1
luarocks install --tree=/root/rpmbuild/BUILD/lualib lua-resty-openssl --lua-version=5.1
luarocks install --tree=/root/rpmbuild/BUILD/lualib lua-resty-jwt --lua-version=5.1
cp -r /root/rpmbuild/BUILD/lualib/share/lua/5.1/resty/* %{buildroot}/opt/nxguard/lualib/resty/
install /root/rpmbuild/BUILD/lualib/lib64/lua/5.1/* %{buildroot}/opt/nxguard/lualib/

cd /root/rpmbuild/BUILD/nginx-1.31.9
install -c objs/nginx %{buildroot}/opt/nxguard/nginx/sbin/nginx
install -c objs/*_module.so %{buildroot}/opt/nxguard/nginx/modules/

cd /root/rpmbuild/BUILD/modsecurity-v3.0.14
install -d %{buildroot}/opt/nxguard/modsec/bin
install -d %{buildroot}/opt/nxguard/modsec/conf
install -d %{buildroot}/opt/nxguard/modsec/lib/pkgconfig
install -d %{buildroot}/opt/nxguard/modsec/include/modsecurity/actions
install -d %{buildroot}/opt/nxguard/modsec/include/modsecurity/collection

install -c tools/rules-check/modsec-rules-check %{buildroot}/opt/nxguard/modsec/bin/modsec-rules-check
install -c src/.libs/* %{buildroot}/opt/nxguard/modsec/lib/
install -c -m 644 headers/modsecurity/actions/*.h %{buildroot}/opt/nxguard/modsec/include/modsecurity/actions/
install -c -m 644 headers/modsecurity/collection/*.h %{buildroot}/opt/nxguard/modsec/include/modsecurity/collection/
install -c -m 644 headers/modsecurity/*.h %{buildroot}/opt/nxguard/modsec/include/modsecurity/
install -c -m 644 examples/reading_logs_via_rule_message/reading_logs_via_rule_message.h %{buildroot}/opt/nxguard/modsec/include/modsecurity/
install -c -m 644 modsecurity.pc %{buildroot}/opt/nxguard/modsec/lib/pkgconfig/

%files
%attr(0744, nxguard, nxguard) /opt/nxguard/modsec
%attr(0744, nxguard, nxguard) /opt/nxguard/luajit
%attr(0744, nxguard, nxguard) /opt/nxguard/lualib
%attr(0744, nxguard, nxguard) /opt/nxguard/nginx
%attr(0744, nxguard, nxguard) /opt/nxguard/html
%attr(0744, nxguard, nxguard) /opt/nxguard/logs
%attr(0744, nxguard, nxguard) /opt/nxguard/run
%attr(0744, nxguard, nxguard) /opt/nxguard/cache

%post
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/sbin"

rm -f /opt/nxguard/modsec/lib/libmodsecurity.so.3 /opt/nxguard/modsec/lib/libmodsecurity.so
ln -s /opt/nxguard/modsec/lib/libmodsecurity.so.3.0.14 /opt/nxguard/modsec/lib/libmodsecurity.so.3
ln -s /opt/nxguard/modsec/lib/libmodsecurity.so.3.0.14 /opt/nxguard/modsec/lib/libmodsecurity.so
ln -s /opt/nxguard/logs /opt/nxguard/nginx/logs
ldconfig -n /opt/nxguard/modsec/lib

cd /opt/nxguard/luajit/lib
ln -sf libluajit-5.1.so.2.1.* libluajit-5.1.so 2>/dev/null || :
ln -sf libluajit-5.1.so.2.1.* libluajit-5.1.so.2 2>/dev/null || :
cd /opt/nxguard/luajit/bin
ln -sf luajit-2.1.* luajit 2>/dev/null || :
ldconfig -n 2>/dev/null /opt/nxguard/luajit/lib

if [ `grep -c nxguard /etc/passwd` = "0" ]; then
	useradd -r -d /opt/nxguard -s /bin/false nxguard
	echo 'nxguard ALL=(ALL:ALL) NOPASSWD: ALL' > /etc/sudoers.d/nxguard
fi
chown -R nxguard:nxguard /opt/nxguard

%changelog
* Thu Nov 19 2026 Gustavo Liberatti <gustavo@liberatti.com.br> - 1.31.9-1
- Convert engine from OpenResty bundle to NGINX 1.31.9 with standalone LuaJIT and ngx_http_lua_module

* Thu Aug 06 2026 Gustavo Liberatti <gustavo@liberatti.com.br> - 1.29.2-4
- Fix ModSecurity-nginx module path and LuaJIT build paths in %%prep and %%install

* Fri Apr 24 2026 Gustavo Liberatti <gustavo@liberatti.com.br> - 1.29.2-4
- Update project license to Apache 2.0 and improve documentation

* Tue Feb 04 2025 Gustavo Liberatti <gustavo@liberatti.com.br> - 1.29.2-3
- Create nxguard openresty with modsecurity 3x
