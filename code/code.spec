%global electron_version 37
%global nodejs_min 20

Name:           code
Version:        1.105.1
Release:        1%{?dist}
Summary:        Open source build of Visual Studio Code editor

License:        MIT
URL:            https://github.com/microsoft/vscode
Source0:        https://github.com/microsoft/vscode/archive/%{version}/vscode-%{version}.tar.gz
Source1:        https://github.com/Anifyuli/code-oss-rpm/blob/main/code/code.mjs
Source2:        https://github.com/Anifyuli/code-oss-rpm/blob/main/code/code.sh
Patch0:         https://github.com/Anifyuli/code-oss-rpm/blob/main/code/product_json.diff
Patch1:         https://github.com/Anifyuli/code-oss-rpm/blob/main/code/clipath.patch
Patch2:         https://github.com/Anifyuli/code-oss-rpm/blob/main/code/0009-openvsx-extension-signature.patch

BuildRequires:  nodejs >= %{nodejs_min}
BuildRequires:  npm
BuildRequires:  git-core
BuildRequires:  python3
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib
BuildRequires:  jq
BuildRequires:  pkgconfig(libsecret-1)
BuildRequires:  pkgconfig(x11)
BuildRequires:  pkgconfig(xkbfile)

Requires:       electron%{electron_version}
Requires:       libsecret
Requires:       libX11
Requires:       libxkbfile
Requires:       ripgrep

# Bundled node modules - we can't unbundle due to build complexity
Provides:       bundled(nodejs-modules)

Provides:       vscode = %{version}-%{release}
Provides:       code-oss = %{version}-%{release}

# Only x86_64 supported due to electron dependency
ExclusiveArch:  x86_64

%description
Visual Studio Code is a code editor redefined and optimized for building
and debugging modern web and cloud applications.

This is the open source build of VS Code (Code - OSS) without proprietary
Microsoft branding, telemetry, and marketplace. It uses the Open VSX Registry
for extensions instead of the Microsoft marketplace.

%prep
%autosetup -n vscode-%{version} -p1

# Set build metadata
builddate=$(date -u -Is | sed 's/\+00:00/Z/')
commit=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
sed -e "s/@COMMIT@/$commit/" -e "s/@DATE@/$builddate/" -i product.json

# Configure for system electron
electronver=$(jq -r '.devDependencies.electron // .packages[""].devDependencies.electron' package-lock.json)
cat >> .npmrc <<EOF
target "${electronver//v/}"
disturl "https://electronjs.org/headers"
runtime "electron"
build_from_source "true"
EOF

# Prepare desktop files
sed -i \
    -e 's|/usr/share/@@NAME@@/@@NAME@@|@@NAME@@|g' \
    -e 's|@@NAME_SHORT@@|Code|g' \
    -e 's|@@NAME_LONG@@|Code - OSS|g' \
    -e 's|@@NAME@@|code-oss|g' \
    -e 's|@@ICON@@|com.visualstudio.code.oss|g' \
    -e 's|@@EXEC@@|%{_bindir}/code-oss|g' \
    -e 's|@@LICENSE@@|MIT|g' \
    -e 's|@@URLPROTOCOL@@|vscode|g' \
    resources/linux/code{.appdata.xml,.desktop,-url-handler.desktop}

desktop-file-edit --set-key StartupWMClass --set-value code-oss \
    resources/linux/code.desktop

cp resources/linux/{code,code-oss}-url-handler.desktop
desktop-file-edit --set-key MimeType --set-value x-scheme-handler/code-oss \
    resources/linux/code-oss-url-handler.desktop

# Prepare shell completions
cp resources/completions/bash/code resources/completions/bash/code-oss
cp resources/completions/zsh/_code resources/completions/zsh/_code-oss

sed -i 's|@@APPNAME@@|code|g' resources/completions/{bash/code,zsh/_code}
sed -i 's|@@APPNAME@@|code-oss|g' resources/completions/{bash/code-oss,zsh/_code-oss}

# Disable unnecessary downloads
sed -i 's|validateChecksum: false,|validateChecksum: true,|' \
    build/lib/electron.{js,ts} 2>/dev/null || true

%build
# Prevent unnecessary downloads
export ELECTRON_SKIP_BINARY_DOWNLOAD=1
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Use build directory for caches
export npm_config_cache="%{_builddir}/.npm"
export XDG_CACHE_HOME="%{_builddir}/.cache"

# Install dependencies
npm ci --legacy-peer-deps

# Build minified production version
npm run gulp vscode-linux-x64-min

%install
# Install application files
install -dm755 %{buildroot}%{_libdir}/%{name}
cp -r --no-preserve=ownership --preserve=mode \
    VSCode-linux-x64/resources/app/* \
    %{buildroot}%{_libdir}/%{name}/

# Fix permissions
find %{buildroot}%{_libdir}/%{name} -type d -exec chmod 0755 {} \;
find %{buildroot}%{_libdir}/%{name} -type f -exec chmod 0644 {} \;

# Make native modules executable
find %{buildroot}%{_libdir}/%{name}/node_modules -name "*.node" -exec chmod 0755 {} \;

# Replace bundled ripgrep with system version
rm -f %{buildroot}%{_libdir}/%{name}/node_modules/@vscode/ripgrep/bin/rg
ln -sf %{_bindir}/rg \
    %{buildroot}%{_libdir}/%{name}/node_modules/@vscode/ripgrep/bin/rg

# Install launcher script
install -Dm755 %{SOURCE2} %{buildroot}%{_bindir}/code-oss
sed -i \
    -e "s|@ELECTRON@|electron%{electron_version}|g" \
    -e "s|@LIBDIR@|%{_libdir}|g" \
    -e "s|@NAME@|%{name}|g" \
    %{buildroot}%{_bindir}/code-oss

# Install electron entry point
install -Dm755 %{SOURCE1} %{buildroot}%{_libdir}/%{name}/code.mjs
sed -i "1s|.*|#!/usr/bin/electron%{electron_version}|" \
    %{buildroot}%{_libdir}/%{name}/code.mjs

# Symlink for 'code' command
ln -sf code-oss %{buildroot}%{_bindir}/code

# Install desktop files
install -Dm644 resources/linux/code.appdata.xml \
    %{buildroot}%{_metainfodir}/code-oss.appdata.xml
install -Dm644 resources/linux/code.desktop \
    %{buildroot}%{_datadir}/applications/code-oss.desktop
install -Dm644 resources/linux/code-url-handler.desktop \
    %{buildroot}%{_datadir}/applications/code-url-handler.desktop
install -Dm644 resources/linux/code-oss-url-handler.desktop \
    %{buildroot}%{_datadir}/applications/code-oss-url-handler.desktop

# Install icons
install -Dm644 VSCode-linux-x64/resources/app/resources/linux/code.png \
    %{buildroot}%{_datadir}/pixmaps/com.visualstudio.code.oss.png

install -dm755 %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
ln -sf %{_libdir}/%{name}/resources/app/out/vs/workbench/browser/parts/editor/media/code-icon.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/com.visualstudio.code.oss.svg

# Install bash completions
install -Dm644 resources/completions/bash/code \
    %{buildroot}%{_datadir}/bash-completion/completions/code
install -Dm644 resources/completions/bash/code-oss \
    %{buildroot}%{_datadir}/bash-completion/completions/code-oss

# Install zsh completions
install -Dm644 resources/completions/zsh/_code \
    %{buildroot}%{_datadir}/zsh/site-functions/_code
install -Dm644 resources/completions/zsh/_code-oss \
    %{buildroot}%{_datadir}/zsh/site-functions/_code-oss

# Install license files
install -Dm644 VSCode-linux-x64/resources/app/LICENSE.txt \
    %{buildroot}%{_datadir}/licenses/%{name}/LICENSE
install -Dm644 VSCode-linux-x64/resources/app/ThirdPartyNotices.txt \
    %{buildroot}%{_datadir}/licenses/%{name}/ThirdPartyNotices.txt

%check
# Validate desktop files
desktop-file-validate %{buildroot}%{_datadir}/applications/code-oss.desktop
desktop-file-validate %{buildroot}%{_datadir}/applications/code-url-handler.desktop
desktop-file-validate %{buildroot}%{_datadir}/applications/code-oss-url-handler.desktop

# Validate appdata
appstream-util validate-relax --nonet \
    %{buildroot}%{_metainfodir}/code-oss.appdata.xml

%files
%license LICENSE.txt ThirdPartyNotices.txt
%doc README.md
%{_bindir}/code
%{_bindir}/code-oss
%{_libdir}/%{name}/
%{_datadir}/applications/code-oss.desktop
%{_datadir}/applications/code-url-handler.desktop
%{_datadir}/applications/code-oss-url-handler.desktop
%{_metainfodir}/code-oss.appdata.xml
%{_datadir}/pixmaps/com.visualstudio.code.oss.png
%{_datadir}/icons/hicolor/scalable/apps/com.visualstudio.code.oss.svg
%{_datadir}/bash-completion/completions/code
%{_datadir}/bash-completion/completions/code-oss
%{_datadir}/zsh/site-functions/_code
%{_datadir}/zsh/site-functions/_code-oss

%changelog
* Tue Nov 11 2025 Anifyuliansyah <anifyuli007@outlook.co.id> - 1.105.1-1
- Initial RPM package for Code OSS

