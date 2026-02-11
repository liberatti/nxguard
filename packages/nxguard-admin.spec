Name:		nxguard-admin
Version:	1.0.6
Release:	1%{?dist}
Summary:	nxguard admin console

License:	Apache-2.0
Source0:	%{name}-%{version}.tar.gz    

BuildRequires:	python3.12-pip
#Requires:	nxguard-engine>=1.27.1

%description
nxguard admin console and API.

%build
# No compilation required for python

%install
install -d %{buildroot}/opt/nxguard/admin
cp -r %{_builddir}/admin/* %{buildroot}/opt/nxguard/admin/

install -d %{buildroot}/opt/nxguard/site-packages
cp -r %{_builddir}/site-packages/* %{buildroot}/opt/nxguard/site-packages

install -d %{buildroot}/opt/nxguard/luajit/share/lua/5.1/nxguard
cp -r %{_builddir}/luajit/* %{buildroot}/opt/nxguard/luajit/share/lua/5.1/nxguard

%files
%attr(0755, nxguard, nxguard) /opt/nxguard/admin
%attr(0755, nxguard, nxguard) /opt/nxguard/site-packages
%attr(0755, nxguard, nxguard) /opt/nxguard/luajit/share/lua/5.1/nxguard

%changelog
* Wed Feb 11 2026 Gustavo Liberatti
- Fix python dependencies installation and packaging
- Split Core Rule Set into its own package
