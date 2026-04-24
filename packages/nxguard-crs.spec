Name:		nxguard-crs
Version:	3.3.9
Release:	1%{?dist}
Summary:	OWASP Core Rule Set for nxguard
BuildArch:	noarch

License:	Apache-2.0
Source0:	%{name}-%{version}.tar.gz

#Requires:	nxguard-engine>=1.27.1

%description
OWASP Core Rule Set (CRS) for ModSecurity on nxguard.

%prep
cd /root/rpmbuild/BUILD

%build
# No compilation required for rules

%install
install -d %{buildroot}/opt/nxguard/modsec/coreruleset
cp -r /root/rpmbuild/BUILD/coreruleset-3.3.9/rules/* %{buildroot}/opt/nxguard/modsec/coreruleset/
#rm -f %{buildroot}/opt/nxguard/modsec/coreruleset/REQUEST-901-INITIALIZATION.conf

%files
%attr(0744, nxguard, nxguard) /opt/nxguard/modsec/coreruleset

%changelog
* Wed Feb 11 2026 Gustavo Liberatti
- Split Core Rule Set into its own package
