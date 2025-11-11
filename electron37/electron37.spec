%global electron_major 37
%global chromium_version 138.0.7204.251

Name:           electron%{electron_major}
Version:        37.5.1
Release:        1%{?dist}
Summary:        Build cross platform desktop apps with web technologies

License:        MIT AND BSD-3-Clause
URL:            https://electronjs.org
# Using official prebuilt binaries from GitHub releases
Source0:        https://github.com/electron/electron/releases/download/v%{version}/electron-v%{version}-linux-x64.zip
Source1:        electron-launcher.sh
Source2:        electron.desktop

BuildRequires:  unzip
BuildRequires:  desktop-file-utils

# Runtime dependencies based on Arch Linux electron package
Requires:       c-ares
Requires:       gcc-libs
Requires:       glibc
Requires:       gtk3
Requires:       libevent
Requires:       libffi
Requires:       libpulse
Requires:       nss
Requires:       zlib

Provides:       bundled(chromium) = %{chromium_version}
Provides:       bundled(nodejs)
Provides:       bundled(v8)

# Upstream only provides x86_64 binaries
ExclusiveArch:  x86_64

%description
Electron is a framework for creating native applications with web technologies
like JavaScript, HTML, and CSS.

This package contains prebuilt binaries from the official Electron releases.
Building from source would require downloading 20GB+ of Chromium dependencies
and 4-6 hours of build time.

%prep
# Extract the zip file
mkdir -p %{_builddir}/electron-v%{version}-linux-x64
cd %{_builddir}/electron-v%{version}-linux-x64
unzip -qo %{SOURCE0}

%build
# Binary repackage, no build needed

%install
# Install electron files
install -dm755 %{buildroot}%{_libdir}/%{name}
cp -a * %{buildroot}%{_libdir}/%{name}/

# Install launcher script
install -Dm755 %{SOURCE1} %{buildroot}%{_bindir}/%{name}
sed -i "s|@ELECTRON@|%{name}|g" %{buildroot}%{_bindir}/%{name}

# Install desktop file
install -Dm644 %{SOURCE2} %{buildroot}%{_datadir}/applications/%{name}.desktop
sed -i "s|@ELECTRON@|%{name}|g" %{buildroot}%{_datadir}/applications/%{name}.desktop

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop

%files
%{_bindir}/%{name}
%{_libdir}/%{name}/
%{_datadir}/applications/%{name}.desktop

%changelog
* Tue Nov 11 2025 Anifyuliansyah <anifyuli007@outlook.co.id> - 37.0.0-1
- Initial package for Electron 37
