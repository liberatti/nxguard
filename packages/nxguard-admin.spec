Name:		nxguard-admin
Version:	1.0.6
Release:	1%{?dist}
Summary:	nxguard admin console

License:	Apache-2.0
Source0:	%{name}-%{version}.tar.gz    

BuildRequires:	python3.12-pip, git
#Requires:	nxguard-engine>=1.27.1

%description
nxguard admin console and API.

%build
# No compilation required for python
mkdir -p %{_builddir}/site-packages
PYTHONUSERBASE=%{_builddir}/site-packages pip3.12 install --user -r requirements.txt

%install
install -d %{buildroot}/opt/nxguard/admin
cp -r %{_builddir}/admin/* %{buildroot}/opt/nxguard/admin/

install -d %{buildroot}/opt/nxguard/site-packages
cp -r %{_builddir}/site-packages/* %{buildroot}/opt/nxguard/site-packages

%files
%attr(0755, nxguard, nxguard) /opt/nxguard/admin
%attr(0755, nxguard, nxguard) /opt/nxguard/site-packages

%changelog
* Wed Feb 11 2026 Gustavo Liberatti
- Fix python dependencies installation and packaging
- Split Core Rule Set into its own package
