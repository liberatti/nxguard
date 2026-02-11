Name:           ssdeep
Version:        2.14.1
Release:        1%{?dist}
Summary:        Fuzzy hashing API and fuzzy hashing tool

License:        GPL-2.0
BuildRequires:  wget gcc gcc-c++ make automake libtool zlib-devel openssl-devel
Requires:       bash

%description
ssdeep is a fuzzy hashing API and tool.

%prep
cd %{_builddir}
rm -rf ssdeep-release-%{version}

wget -O ssdeep-release-%{version}.tar.gz \
  https://github.com/ssdeep-project/ssdeep/archive/refs/tags/release-%{version}.tar.gz

tar -xf ssdeep-release-%{version}.tar.gz

%build
cd ssdeep-release-%{version}
./bootstrap
./configure --prefix=/usr
make %{?_smp_mflags}

%install
rm -rf %{buildroot}
cd ssdeep-release-%{version}

make install DESTDIR=%{buildroot}

%files
/usr/bin/ssdeep
/usr/lib*/libfuzzy.so*
/usr/lib*/libfuzzy.a
/usr/lib*/libfuzzy.la
/usr/include/fuzzy.h
/usr/include/edit_dist.h
/usr/share/man/man1/ssdeep.1*

%post
/sbin/ldconfig

%changelog
* Sat Aug 19 2023 Gustavo Liberatti
- Create