#
# This is the SPEC file for creating binary RPMs for the Dom0.
#
#
# The Qubes OS Project, http://www.qubes-os.org
#
# Copyright (C) 2013  Marek Marczykowski  <marmarek@invisiblethingslab.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#

%{!?python_sitearch: %define python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

%{!?version: %define version %(cat version)}

%define _dracutmoddir	/usr/lib/dracut/modules.d
%if %{fedora} < 17
%define _dracutmoddir   /usr/share/dracut/modules.d
%endif

Name:		qubes-core-dom0-linux
Version:	%{version}
Release:	1%{?dist}
Summary:	Linux-specific files for Qubes dom0

Group:		Qubes
Vendor:		Invisible Things Lab
License:	GPL
URL:		http://www.qubes-os.org

BuildRequires:  ImageMagick
BuildRequires:  pandoc
Requires:	qubes-core-dom0

%define _builddir %(pwd)

%description
Linux customizations required to use system as Qubes dom0.
Additionally some graphical elements for every Linux desktop envirnment (icons,
appmenus etc).

%prep
# we operate on the current directory, so no need to unpack anything
# symlink is to generate useful debuginfo packages
rm -f %{name}-%{version}
ln -sf . %{name}-%{version}
%setup -T -D

%build
python -m compileall appmenus-scripts
python -O -m compileall appmenus-scripts
(cd dom0-updates; make)
(cd doc; make manpages)

%install

### Appmenus

mkdir -p $RPM_BUILD_ROOT%{python_sitearch}/qubes/modules
cp appmenus-scripts/qubes-core-appmenus.py $RPM_BUILD_ROOT%{python_sitearch}/qubes/modules/10appmenus.py
cp appmenus-scripts/qubes-core-appmenus.pyc $RPM_BUILD_ROOT%{python_sitearch}/qubes/modules/10appmenus.pyc
cp appmenus-scripts/qubes-core-appmenus.pyo $RPM_BUILD_ROOT%{python_sitearch}/qubes/modules/10appmenus.pyo

mkdir -p $RPM_BUILD_ROOT/usr/libexec/qubes-appmenus
cp appmenus-scripts/*.sh $RPM_BUILD_ROOT/usr/libexec/qubes-appmenus/
cp appmenus-scripts/qubes-receive-appmenus $RPM_BUILD_ROOT/usr/libexec/qubes-appmenus/

install -D appmenus-scripts/qvm-sync-appmenus $RPM_BUILD_ROOT/usr/bin/qvm-sync-appmenus

mkdir -p $RPM_BUILD_ROOT/etc/qubes-rpc/policy
cp appmenus-scripts/qubes.SyncAppMenus $RPM_BUILD_ROOT/etc/qubes-rpc/
cp appmenus-scripts/qubes.SyncAppMenus.policy $RPM_BUILD_ROOT/etc/qubes-rpc/policy/

mkdir -p $RPM_BUILD_ROOT/usr/share/qubes-appmenus/
cp appmenus-files/* $RPM_BUILD_ROOT/usr/share/qubes-appmenus/

### Dom0 updates
install -D dom0-updates/qubes-dom0-updates.cron $RPM_BUILD_ROOT/etc/cron.daily/qubes-dom0-updates.cron
install -D dom0-updates/qubes-dom0-update $RPM_BUILD_ROOT/usr/bin/qubes-dom0-update
install -D dom0-updates/qubes-receive-updates $RPM_BUILD_ROOT/usr/libexec/qubes/qubes-receive-updates
install -m 0644 -D dom0-updates/qubes-cached.repo $RPM_BUILD_ROOT/etc/yum.real.repos.d/qubes-cached.repo
install -D dom0-updates/qfile-dom0-unpacker $RPM_BUILD_ROOT/usr/libexec/qubes/qfile-dom0-unpacker
install -m 0644 -D dom0-updates/qubes.ReceiveUpdates $RPM_BUILD_ROOT/etc/qubes-rpc/qubes.ReceiveUpdates
install -m 0664 -D dom0-updates/qubes.ReceiveUpdates.policy $RPM_BUILD_ROOT/etc/qubes-rpc/policy/qubes.ReceiveUpdates

install -d $RPM_BUILD_ROOT/var/lib/qubes/updates

### Icons
mkdir -p $RPM_BUILD_ROOT/usr/share/qubes/icons
for icon in icons/*.png; do
    convert -resize 48 $icon $RPM_BUILD_ROOT/usr/share/qubes/$icon
done

### Documentation
(cd doc; make DESTDIR=$RPM_BUILD_ROOT install)

%post

for i in /usr/share/qubes/icons/*.png ; do
	xdg-icon-resource install --novendor --size 48 $i
done

xdg-desktop-menu install /usr/share/qubes-appmenus/qubes-dispvm.directory /usr/share/qubes-appmenus/qubes-dispvm-firefox.desktop

sed '/^reposdir\s*=/d' -i /etc/yum.conf
echo reposdir=/etc/yum.real.repos.d >> /etc/yum.conf

sed '/^installonlypkgs\s*=/d' -i /etc/yum.conf
echo 'installonlypkgs = kernel, kernel-qubes-vm' >> /etc/yum.conf

%preun
if [ "$1" = 0 ] ; then
	# no more packages left

	for i in /usr/share/qubes/icons/*.png ; do
		xdg-icon-resource uninstall --novendor --size 48 $i
	done

    xdg-desktop-menu uninstall /usr/share/qubes-appmenus/qubes-dispvm.directory /usr/share/qubes-appmenus/qubes-dispvm-firefox.desktop
fi

%triggerin -- PackageKit
# dom0 have no network, but still can receive updates (qubes-dom0-update)
sed -i 's/^UseNetworkHeuristic=.*/UseNetworkHeuristic=false/' /etc/PackageKit/PackageKit.conf

%files
/etc/qubes-rpc/policy/qubes.SyncAppMenus.policy
/etc/qubes-rpc/qubes.SyncAppMenus
%{python_sitearch}/qubes/modules/10appmenus.py
%{python_sitearch}/qubes/modules/10appmenus.pyc
%{python_sitearch}/qubes/modules/10appmenus.pyo
/usr/libexec/qubes-appmenus/convert-apptemplate2vm.sh
/usr/libexec/qubes-appmenus/convert-dirtemplate2vm.sh
/usr/libexec/qubes-appmenus/create-apps-for-appvm.sh
/usr/libexec/qubes-appmenus/qubes-receive-appmenus
/usr/libexec/qubes-appmenus/remove-appvm-appmenus.sh
/usr/share/qubes-appmenus/qubes-appmenu-select.desktop
/usr/share/qubes-appmenus/qubes-dispvm-firefox.desktop
/usr/share/qubes-appmenus/qubes-dispvm.directory
/usr/share/qubes-appmenus/qubes-servicevm.directory.template
/usr/share/qubes-appmenus/qubes-start.desktop
/usr/share/qubes-appmenus/qubes-templatevm.directory.template
/usr/share/qubes-appmenus/qubes-vm.directory.template
/usr/share/qubes/icons/*.png
/usr/bin/qvm-sync-appmenus
# Dom0 updates
/etc/cron.daily/qubes-dom0-updates.cron
/etc/yum.real.repos.d/qubes-cached.repo
/usr/bin/qubes-dom0-update
%attr(4750,root,qubes) /usr/libexec/qubes/qfile-dom0-unpacker
/usr/libexec/qubes/qubes-receive-updates
/etc/qubes-rpc/qubes.ReceiveUpdates
%attr(0664,root,qubes) %config(noreplace) /etc/qubes-rpc/policy/qubes.ReceiveUpdates
%attr(0770,root,qubes) %dir /var/lib/qubes/updates
# Man
%{_mandir}/man1/qvm-*.1*
%{_mandir}/man1/qubes-*.1*


%changelog
