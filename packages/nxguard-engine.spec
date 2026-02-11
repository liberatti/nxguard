Name:		nxguard-engine
Version:	1.27.1
Release:	1%{?dist}
Summary:	nxguard engine powered by openresty

License:	Apache-2.0
Source0:	%{name}-%{version}.tar.gz    

BuildRequires: openldap-devel luarocks openssl-devel gcc gcc-c++ zlib-devel openssl-devel make automake libtool readline-devel libinput libcurl-devel pcre2-devel libxml2-devel libxslt-devel libgcrypt-devel gd-devel perl-ExtUtils-Embed
Requires: bash, lua, ssdeep = 2.14.1, shadow-utils, util-linux, gcc, sudo

%undefine __brp_mangle_shebangs 

%description
%prep

cd /root/rpmbuild/BUILD

install -d openresty-1.27.1.1/modules
mv modsecurity-nginx-v1.0.3 openresty-1.27.1.1/modules/
mv nginx-sticky-module-ng-1.2.6 openresty-1.27.1.1/modules/
mv nginx_upstream_check_module-0.4.1 openresty-1.27.1.1/modules/
mv nginx_ajp_module-1.0.0 openresty-1.27.1.1/modules/


%build
cd /root/rpmbuild/BUILD/lua-5.1.5
make -j$(nproc) linux

cd /root/rpmbuild/BUILD/modsecurity-v3.0.12
./configure --prefix=/opt/nxguard/modsec --with-yajl --with-pcre2 --with-ssdeep --with-lua
make -j 4
make install

cd /root/rpmbuild/BUILD/openresty-1.27.1.1
./configure --with-compat\
    --with-http_ssl_module\
    --with-stream \
    --with-stream_ssl_module \
    --with-stream_ssl_preread_module \
    --with-http_stub_status_module\
	--with-http_v2_module\
	--without-lua_resty_mysql\
	--with-debug\
	--with-cc-opt='-D FD_SETSIZE=32768'\
    --add-dynamic-module=modules/nginx_ajp_module-1.0.0\
    --add-module=modules/nginx_upstream_check_module-0.4.1\
    --add-dynamic-module=modules/nginx-sticky-module-ng-1.2.6\
    --add-dynamic-module=modules/modsecurity-nginx-v1.0.3\
    --prefix=/opt/nxguard
make -j 4

%install
install -d %{buildroot}/opt/nxguard/html
install -d %{buildroot}/opt/nxguard/logs
install -d %{buildroot}/opt/nxguard/run
install -d %{buildroot}/opt/nxguard/cache
install -d %{buildroot}/opt/nxguard/data

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

install -d %{buildroot}/opt/nxguard/luajit/include/lua-5.1

cd /root/rpmbuild/BUILD/lua-5.1.5/src
install -p -m 0755 lua luac %{buildroot}/opt/nxguard/luajit/bin
install -p -m 0644 lua.h luaconf.h lualib.h lauxlib.h ../etc/lua.hpp %{buildroot}/opt/nxguard/luajit/include/lua-5.1
install -p -m 0644 liblua.a %{buildroot}/opt/nxguard/luajit/lib/lua/5.1

install /root/rpmbuild/BUILD/openresty-1.27.1.1/COPYRIGHT %{buildroot}/opt/nxguard/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/LuaJIT-2.1-20240815/src
install -m 0755 luajit %{buildroot}/opt/nxguard/luajit/bin/luajit-2.1.ROLLING
install -m 0644 libluajit.a %{buildroot}/opt/nxguard/luajit/lib/libluajit-5.1.a || :
install -m 0755 libluajit.so %{buildroot}/opt/nxguard/luajit/lib/libluajit-5.1.so.2.1.ROLLING
install -m 0644 lua.h lualib.h lauxlib.h luaconf.h lua.hpp luajit.h  %{buildroot}/opt/nxguard/luajit/include/luajit-2.1

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/LuaJIT-2.1-20240815/src/jit
install -m 0644 bc.lua bcsave.lua dump.lua p.lua v.lua zone.lua dis_x86.lua dis_x64.lua dis_arm.lua dis_arm64.lua dis_arm64be.lua dis_ppc.lua dis_mips.lua dis_mipsel.lua dis_mips64.lua dis_mips64el.lua dis_mips64r6.lua dis_mips64r6el.lua vmdef.lua %{buildroot}/opt/nxguard/luajit/share/luajit-2.1/jit

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-cjson-2.1.0.14
install -m 0644 cjson.so %{buildroot}/opt/nxguard/lualib/cjson.so
install -m 0644 lua/*.lua %{buildroot}/opt/nxguard/lualib/
install -m 0644 lua/cjson/*.lua %{buildroot}/opt/nxguard/lualib/cjson/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-signal-0.04
install -d %{buildroot}/opt/nxguard/lualib/resty
install lib/resty/*.lua %{buildroot}/opt/nxguard/lualib/resty
install librestysignal.so %{buildroot}/opt/nxguard/lualib/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-rds-parser-0.06
install -d %{buildroot}/opt/nxguard/lualib/rds
install parser.so %{buildroot}/opt/nxguard/lualib/rds

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-dns-0.23
install -d %{buildroot}/opt/nxguard/lualib/resty/dns/
install lib/resty/dns/*.lua %{buildroot}/opt/nxguard/lualib/resty/dns/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-memcached-0.17
install -d %{buildroot}/opt/nxguard/lualib/resty
install lib/resty/*.lua %{buildroot}/opt/nxguard/lualib/resty

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-string-0.16
install -d %{buildroot}/opt/nxguard/lualib/resty
install lib/resty/*.lua %{buildroot}/opt/nxguard/lualib/resty

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-upload-0.11
install -d %{buildroot}/opt/nxguard/lualib/resty
install lib/resty/*.lua %{buildroot}/opt/nxguard/lualib/resty

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-websocket-0.12
install -d %{buildroot}/opt/nxguard/lualib/resty/websocket
install lib/resty/websocket/*.lua %{buildroot}/opt/nxguard/lualib/resty/websocket/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-lock-0.09
install -d %{buildroot}/opt/nxguard/lualib/resty/
install lib/resty/*.lua %{buildroot}/opt/nxguard/lualib/resty/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-lrucache-0.15
install -d %{buildroot}/opt/nxguard/lualib/resty/lrucache
install lib/resty/*.lua %{buildroot}/opt/nxguard/lualib/resty/
install lib/resty/lrucache/*.lua %{buildroot}/opt/nxguard/lualib/resty/lrucache/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-core-0.1.30
install -d %{buildroot}/opt/nxguard/lualib/resty/core/
install -d %{buildroot}/opt/nxguard/lualib/ngx/
install -d %{buildroot}/opt/nxguard/lualib/ngx/ssl
install lib/resty/*.lua %{buildroot}/opt/nxguard/lualib/resty/
install lib/resty/core/*.lua %{buildroot}/opt/nxguard/lualib/resty/core/
install lib/ngx/*.lua %{buildroot}/opt/nxguard/lualib/ngx/
install lib/ngx/ssl/*.lua %{buildroot}/opt/nxguard/lualib/ngx/ssl/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-upstream-healthcheck-0.08
install -d %{buildroot}/opt/nxguard/lualib/resty/upstream/
install lib/resty/upstream/*.lua %{buildroot}/opt/nxguard/lualib/resty/upstream/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-limit-traffic-0.09
install -d %{buildroot}/opt/nxguard/lualib/resty/limit/
install lib/resty/limit/*.lua %{buildroot}/opt/nxguard/lualib/resty/limit/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-resty-shell-0.03
install -d %{buildroot}/opt/nxguard/lualib/resty/
install lib/resty/*.lua %{buildroot}/opt/nxguard/lualib/resty/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/lua-tablepool-0.03
install lib/*.lua %{buildroot}/opt/nxguard/lualib/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/opm-0.0.8
install -d %{buildroot}/opt/nxguard/bin
install bin/* %{buildroot}/opt/nxguard/bin/

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/resty-cli-0.30
install bin/* %{buildroot}/opt/nxguard/bin/

cp /root/rpmbuild/BUILD/openresty-1.27.1.1/build/resty.index  %{buildroot}/opt/nxguard/
cp -r /root/rpmbuild/BUILD/openresty-1.27.1.1/build/pod %{buildroot}/opt/nxguard/

#export LUA_INCDIR=/root/rpmbuild/BUILD/openresty-1.27.1.1/LuaJIT-2.1-20240815/src/
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

install -d %{buildroot}/opt/nxguard/luajit/share/lua/5.1/nxguard
cp -r %{_builddir}/luajit/* %{buildroot}/opt/nxguard/luajit/share/lua/5.1/nxguard

cd /root/rpmbuild/BUILD/openresty-1.27.1.1/build/nginx-1.27.1
install -c objs/nginx %{buildroot}/opt/nxguard/nginx/sbin/nginx
install -c conf/* %{buildroot}/opt/nxguard/nginx/conf
install -c objs/*_module.so %{buildroot}/opt/nxguard/nginx/modules/

cd /root/rpmbuild/BUILD/modsecurity-v3.0.12
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
%attr(0744, root, root) /opt/nxguard/modsec
%attr(0744, root, root) /opt/nxguard/bin
%attr(0744, root, root) /opt/nxguard/luajit
%attr(0744, root, root) /opt/nxguard/lualib
%attr(0744, root, root) /opt/nxguard/nginx
%attr(0744, root, root) /opt/nxguard/pod
%attr(0744, root, root) /opt/nxguard/resty.index
%attr(0744, root, root) /opt/nxguard/COPYRIGHT
%attr(0744, root, root) /opt/nxguard/html
%attr(0744, root, root) /opt/nxguard/logs
%attr(0744, root, root) /opt/nxguard/run
%attr(0744, root, root) /opt/nxguard/cache
%attr(0755, nxguard, nxguard) /opt/nxguard/luajit/share/lua/5.1/nxguard

%post
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/sbin"

rm -f /opt/nxguard/modsec/lib/libmodsecurity.so.3 /opt/nxguard/modsec/lib/libmodsecurity.so
ln -s /opt/nxguard/modsec/lib/libmodsecurity.so.3.0.12 /opt/nxguard/modsec/lib/libmodsecurity.so.3
ln -s /opt/nxguard/modsec/lib/libmodsecurity.so.3.0.12 /opt/nxguard/modsec/lib/libmodsecurity.so
ln -s /opt/nxguard/logs /opt/nxguard/nginx/logs
ldconfig -n /opt/nxguard/modsec/lib

cd /opt/nxguard/luajit/lib
ln -sf libluajit-5.1.so.2.1.ROLLING /opt/nxguard/luajit/lib/libluajit-5.1.so && \
ln -sf libluajit-5.1.so.2.1.ROLLING /opt/nxguard/luajit/lib/libluajit-5.1.so.2 || :
ln -sf luajit-2.1.ROLLING /opt/nxguard/luajit/bin/luajit
ldconfig -n 2>/dev/null /opt/nxguard/luajit/lib

if [ `grep -c nxguard /etc/passwd` = "0" ]; then
	useradd -r -d /opt/nxguard -s /bin/false nxguard
	echo 'nxguard ALL=(ALL:ALL) NOPASSWD: ALL' > /etc/sudoers.d/nxguard
fi
chown -R nxguard:nxguard /opt/nxguard

%changelog
* Thu Feb 04 2025 Gustavo Liberatti
- Create nxguard openresty with modsecurity 3x
