Name:		nxguard-crs
Version:	3.3.6
Release:	alpha%{?dist}
Summary:	OWASP Core Rule Set for nxguard
BuildArch:	noarch

License:	Apache-2.0
Source0:	%{name}-%{version}.tar.gz    

BuildRequires:	wget unzip
Requires:	nxguard-openresty

%description
OWASP Core Rule Set (CRS) for ModSecurity on nxguard.

%prep
cd /root/rpmbuild/BUILD
if [[ ! -e v3.3.6.zip ]];then
	wget https://github.com/coreruleset/coreruleset/archive/refs/tags/v3.3.6.zip
	unzip -o v3.3.6.zip
fi

%build
# No compilation required for rules

%install
install -d %{buildroot}/opt/nxguard/modsec/coreruleset
cp -r /root/rpmbuild/BUILD/coreruleset-3.3.6/rules/* %{buildroot}/opt/nxguard/modsec/coreruleset/
rm -f %{buildroot}/opt/nxguard/modsec/coreruleset/REQUEST-901-INITIALIZATION.conf

%files
%attr(0744, nxguard, nxguard) /opt/nxguard/modsec/coreruleset

%changelog
* Wed Feb 11 2026 Gustavo Liberatti
- Split Core Rule Set into its own package
