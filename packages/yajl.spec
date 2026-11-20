Name:           yajl
Version:        2.1.0
Release:        1%{?dist}
Summary:        Yet Another JSON Library

License:        ISC
BuildRequires:  gcc gcc-c++ cmake make

%global debug_package %{nil}

%description
YAJL is a small event-driven (SAX-style) JSON parser written in ANSI C.

%package        devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description    devel
Development files for %{name}.

%build
cd %{_builddir}/yajl-%{version}
mkdir -p build && cd build
cmake -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=Release ..
make %{?_smp_mflags}

%install
rm -rf %{buildroot}
cd %{_builddir}/yajl-%{version}/build
make install DESTDIR=%{buildroot}
rm -f %{buildroot}/usr/lib*/libyajl_s.a

%files
%{_bindir}/json_reformat
%{_bindir}/json_verify
/usr/lib*/libyajl.so.*

%files devel
/usr/include/yajl
/usr/lib*/libyajl.so
/usr/*/pkgconfig/yajl.pc

%post
/sbin/ldconfig

%postun
/sbin/ldconfig

%changelog
* Fri Nov 20 2026 Gustavo Liberatti <gustavo@liberatti.com.br> - 2.1.0-1
- Initial yajl packaging for Rocky Linux 10
