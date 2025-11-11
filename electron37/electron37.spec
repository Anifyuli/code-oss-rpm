%global electron_major 37
%global chromium_version 138.0.7204.251

Name:           electron%{electron_major}
Version:        37.5.1
Release:        1%{?dist}
Summary:        Build cross platform desktop apps with web technologies

# Electron is MIT, but bundles many libraries with different licenses
License:        MIT AND BSD-3-Clause AND Apache-2.0 AND ISC
URL:            https://electronjs.org/
# Note: Electron binaries are downloaded from official releases
# Building from source requires downloading ~20GB of Chromium deps and takes 6+ hours
Source0:        https://github.com/electron/electron/releases/download/v%{version}/electron-v%{version}-linux-x64.zip
Source1:        https://github.com/electron/electron/releases/download/v%{version}/chromedriver-v%{version}-linux-x64.zip
Source2:        https://github.com/electron/electron/releases/download/v%{version}/mksnapshot-v%{version}-linux-x64.zip
Source3:        electron-launcher.sh

BuildRequires:  unzip

# Runtime dependencies based on ldd output
Requires:       gtk3
Requires:       libnotify
Requires:       nss
Requires:       libXScrnSaver
Requires:       alsa-lib
Requires:       libXtst
Requires:       libdrm
Requires:       mesa-libgbm
Requires:       libxshmfence

# Electron bundles ffmpeg and other libs
Provides:       bundled(chromium) = %{chromium_version}
Provides:       bundled(nodejs)
Provides:       bundled(v8)
Provides:       bundled(ffmpeg)

# Only x86_64 is officially supported by upstream
ExclusiveArch:  x86_64

%description
Electron is a framework for creating native applications with web technologies
like JavaScript, HTML, and CSS. It takes care of the hard parts so you can
focus on the core of your application.

Note: This package contains pre-built binaries from upstream as building
Electron from source is extremely resource-intensive and requires downloading
~20GB of Chromium dependencies.

%prep
%setup -q -c -n electron-v%{version}-linux-x64
unzip -q %{SOURCE0}

%build
# This is a binary repackage, no build needed

%install
# Create directory structure
install -dm755 %{buildroot}%{_libdir}/%{name}
install -dm755 %{buildroot}%{_bindir}

# Install electron files (already extracted in %prep)
cp -a * %{buildroot}%{_libdir}/%{name}/ || true
chmod -R u+rwX,go+rX %{buildroot}%{_libdir}/%{name}/

# Install wrapper script
install -Dm755 %{SOURCE3} %{buildroot}%{_bindir}/%{name}

# Fix script to point to correct electron name
sed -i "s|@ELECTRON@|%{name}|g" %{buildroot}%{_bindir}/%{name}

# Install chromedriver
cd %{buildroot}%{_libdir}/%{name}
unzip -q %{SOURCE1}

# Install mksnapshot  
unzip -q %{SOURCE2}

# Remove .so files that conflict with system libraries
# but keep bundled versions that are needed
rm -f libffmpeg.so || true

%files
%{_bindir}/%{name}
%{_libdir}/%{name}/

%changelog
* Tue Nov 11 2025 Anifyuliansyah <anifyuli007@outlook.co.id> - 37.0.0-1
- Initial package for Electron 37
