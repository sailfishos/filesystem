Summary: The basic directory layout for a Linux system
Name: filesystem
Version: 3.16+git1
Release: 1
License: Public Domain
URL: https://pagure.io/filesystem
Source1: https://pagure.io/filesystem/raw/master/f/lang-exceptions
Source2: iso_639.sed
Source3: iso_3166.sed
Source4: aarch64.ldconfig.conf
BuildRequires: iso-codes
Requires(pre): setup

%description
The filesystem package is one of the basic packages that is installed
on a Linux system. Filesystem contains the basic directory layout
for a Linux operating system, including the correct permissions for
the directories.

%package content
Summary: Directory ownership content of the filesystem package
License: Public Domain

%description content
This subpackage of filesystem package contains just the file with
the directories owned by the filesystem package. This can be used
during the build process instead of calling rpm -ql filesystem.

%prep

%build

%install
rm -f $RPM_BUILD_DIR/filelist
rm -rf %{buildroot}
mkdir %{buildroot}
install -p -c -m755 %SOURCE2 %{buildroot}/iso_639.sed
install -p -c -m755 %SOURCE3 %{buildroot}/iso_3166.sed

cd %{buildroot}

mkdir -p afs boot dev \
        bin lib sbin \
%ifarch x86_64 ppc64 sparc64 s390x aarch64 ppc64le mips64 mips64el riscv64
        %{_lib} \
%endif
        etc/{X11/{applnk,fontpath.d,xinit/{xinitrc,xinput}.d},xdg/autostart,opt,pm/{config.d,power.d,sleep.d},skel,sysconfig,pki,bash_completion.d,rwtab.d,statetab.d} \
        home media mnt opt root run srv tmp \
        usr/{bin,games,include,%{_lib}/{bpf,games,X11,pm-utils/{module.d,power.d,sleep.d}},lib/{debug/{.dwz,usr},games,locale,modules,sysimage},libexec,local/{bin,etc,games,lib,%{_lib}/bpf,sbin,src,share/{applications,man/man{1,2,3,4,5,6,7,8,9,n,1x,2x,3x,4x,5x,6x,7x,8x,9x},info},libexec,include,},sbin,share/{aclocal,appdata,applications,augeas/lenses,backgrounds,bash-completion{,/completions,/helpers},desktop-directories,dict,doc,empty,games,gnome,help,icons,idl,info,licenses,man/man{1,2,3,4,5,6,7,8,9,n,1x,2x,3x,4x,5x,6x,7x,8x,9x,0p,1p,3p},metainfo,mime-info,misc,omf,pixmaps,sounds,themes,xsessions,X11,wayland-sessions},src,src/kernels,src/debug} \
        var/{adm,empty,ftp,lib/{games,misc,rpm-state},local,log,nis,preserve,spool/{mail,lpd},tmp,db,cache/bpf,opt,games,yp}

#do not create the symlink atm.
#ln -snf etc/sysconfig etc/default
ln -snf ../var/tmp usr/tmp
ln -snf spool/mail var/mail
#ln -snf usr/bin bin
#ln -snf usr/sbin sbin
#ln -snf usr/lib lib
#ln -snf usr/%{_lib} %{_lib}
ln -snf ../run var/run
ln -snf ../run/lock var/lock
ln -snf usr/bin usr/lib/debug/bin
ln -snf usr/lib usr/lib/debug/lib
ln -snf usr/%{_lib} usr/lib/debug/%{_lib}
ln -snf ../.dwz usr/lib/debug/usr/.dwz
ln -snf usr/sbin usr/lib/debug/sbin

sed -n -f %{buildroot}/iso_639.sed /usr/share/xml/iso-codes/iso_639.xml \
  >%{buildroot}/iso_639.tab
sed -n -f %{buildroot}/iso_3166.sed /usr/share/xml/iso-codes/iso_3166.xml \
  >%{buildroot}/iso_3166.tab

grep -v "^$" %{buildroot}/iso_639.tab | grep -v "^#" | while read a b c d ; do
    [[ "$d" =~ "^Reserved" ]] && continue
    [[ "$d" =~ "^No linguistic" ]] && continue

    locale=$c
    if [ "$locale" = "XX" ]; then
        locale=$b
    fi
    echo "%lang(${locale})	/usr/share/locale/${locale}" >> $RPM_BUILD_DIR/filelist
    echo "%lang(${locale}) %ghost %config(missingok) /usr/share/man/${locale}" >>$RPM_BUILD_DIR/filelist
done
cat %{SOURCE1} | grep -v "^#" | grep -v "^$" | while read loc ; do
    locale=$loc
    locality=
    special=
    [[ "$locale" =~ "@" ]] && locale=${locale%%%%@*}
    [[ "$locale" =~ "_" ]] && locality=${locale##*_}
    [[ "$locality" =~ "." ]] && locality=${locality%%%%.*}
    [[ "$loc" =~ "_" ]] || [[ "$loc" =~ "@" ]] || special=$loc

    # If the locality is not official, skip it
    if [ -n "$locality" ]; then
        grep -q "^$locality" %{buildroot}/iso_3166.tab || continue
    fi
    # If the locale is not official and not special, skip it
    if [ -z "$special" ]; then
        grep -q -E "[[:space:]]${locale%%_*}[[:space:]]" \
           %{buildroot}/iso_639.tab || continue
    fi
    echo "%lang(${locale})	/usr/share/locale/${loc}" >> $RPM_BUILD_DIR/filelist
    echo "%lang(${locale})  %ghost %config(missingok) /usr/share/man/${loc}" >> $RPM_BUILD_DIR/filelist
done

rm -f %{buildroot}/iso_639.tab
rm -f %{buildroot}/iso_639.sed
rm -f %{buildroot}/iso_3166.tab
rm -f %{buildroot}/iso_3166.sed

cat $RPM_BUILD_DIR/filelist | grep "locale" | while read a b ; do
    mkdir -p -m 755 %{buildroot}/$b/LC_MESSAGES
done

cat $RPM_BUILD_DIR/filelist | grep "/share/man" | while read a b c d; do
    mkdir -p -m 755 %{buildroot}/$d/man{1,2,3,4,5,6,7,8,9,n,1x,2x,3x,4x,5x,6x,7x,8x,9x,0p,1p,3p}
done

for i in man{1,2,3,4,5,6,7,8,9,n,1x,2x,3x,4x,5x,6x,7x,8x,9x,0p,1p,3p}; do
   echo "/usr/share/man/$i" >>$RPM_BUILD_DIR/filelist
done

%ifarch aarch64
# Install the ldconfig
install -D -m644 %SOURCE4 %{buildroot}/%{_sysconfdir}/ld.so.conf.d/aarch64.conf
%endif

mkdir -p %{buildroot}/usr/share/filesystem
#find all dirs in the buildroot owned by filesystem and store them
find %{buildroot} -mindepth 0 | sed -e 's|%{buildroot}|/|' -e 's|//|/|' \
 | LC_ALL=C sort | grep -v filesystem >%{buildroot}%{_datadir}/filesystem/paths

%pretrans -p <lua>
--# If we are running in pretrans in a fresh root, there is no /usr and
--# symlinks. We cannot be sure, to be the very first rpm in the
--# transaction list. Let's create the needed base directories and symlinks
--# here, to place the files from other packages in the right locations.
--# When our rpm is unpacked by cpio, it will set all permissions and modes
--# later.
posix.mkdir("/usr")
posix.mkdir("/usr/bin")
posix.mkdir("/usr/sbin")
posix.mkdir("/usr/lib")
posix.mkdir("/usr/lib/debug")
posix.mkdir("/usr/lib/debug/usr/")
posix.mkdir("/usr/lib/debug/usr/bin")
posix.mkdir("/usr/lib/debug/usr/sbin")
posix.mkdir("/usr/lib/debug/usr/lib")
posix.mkdir("/usr/lib/debug/usr/%{_lib}")
posix.mkdir("/usr/%{_lib}")
--#posix.symlink("usr/bin", "/bin")
--#posix.symlink("usr/sbin", "/sbin")
--#posix.symlink("usr/lib", "/lib")
posix.symlink("usr/bin", "/usr/lib/debug/bin")
posix.symlink("usr/lib", "/usr/lib/debug/lib")
posix.symlink("usr/%{_lib}", "/usr/lib/debug/%{_lib}")
posix.symlink("../.dwz", "/usr/lib/debug/usr/.dwz")
posix.symlink("usr/sbin", "/usr/lib/debug/sbin")
--#posix.symlink("usr/%{_lib}", "/%{_lib}")
posix.mkdir("/run")
posix.mkdir("/proc")
posix.mkdir("/sys")
posix.chmod("/proc", 0555)
posix.chmod("/sys", 0555)
st = posix.stat("/media")
if st and st.type == "link" then
  os.remove("/media")
end
posix.mkdir("/var")
posix.symlink("../run", "/var/run")
posix.symlink("../run/lock", "/var/lock")
%ifarch aarch64
os.execute('ldconfig')
%endif
return 0

%posttrans
#we need to restorecon on some dirs created in %pretrans or by other packages
#no selinux in Sailfish OS base installation
#restorecon /var 2>/dev/null >/dev/null || :
#restorecon /var/run 2>/dev/null >/dev/null || :
#restorecon /var/lock 2>/dev/null >/dev/null || :
#restorecon -r /usr/lib/debug/ 2>/dev/null >/dev/null || :
#restorecon /sys 2>/dev/null >/dev/null || :
#restorecon /boot 2>/dev/null >/dev/null || :
#restorecon /dev 2>/dev/null >/dev/null || :
#restorecon /media 2>/dev/null >/dev/null || :
#restorecon /afs 2>/dev/null >/dev/null || :

%files content
%dir %{_datadir}/filesystem
%{_datadir}/filesystem/paths



%files -f filelist
%defattr(0755,root,root,0755)
/
/bin
%attr(700,root,root) /boot
%attr(555,root,root) /afs
/dev
%dir /etc
/etc/X11
/etc/xdg
/etc/opt
/etc/pm
/etc/skel
/etc/sysconfig
/etc/pki
/etc/bash_completion.d/
%dir /etc/rwtab.d
%dir /etc/statetab.d
/home
/lib
%ifarch x86_64 ppc64 sparc64 s390x aarch64 ppc64le mips64 mips64el riscv64
/%{_lib}
%endif
/media
%dir /mnt
%dir /opt
%ghost /proc
%attr(750,root,root) /root
/run
/sbin
/srv
%ghost %attr(555,root,root) /sys
%attr(1777,root,root) /tmp
%dir /usr
/usr/bin
/usr/games
/usr/include
/usr/lib
%dir /usr/lib/sysimage
%dir /usr/lib/locale
%dir /usr/lib/modules
%dir /usr/lib/debug
%dir /usr/lib/debug/.dwz
%ghost /usr/lib/debug/bin
%ghost /usr/lib/debug/lib
%ghost /usr/lib/debug/%{_lib}
%ghost /usr/lib/debug/usr
%ghost /usr/lib/debug/usr/bin
%ghost /usr/lib/debug/usr/sbin
%ghost /usr/lib/debug/usr/lib
%ghost /usr/lib/debug/usr/%{_lib}
%ghost /usr/lib/debug/usr/.dwz
%ghost /usr/lib/debug/sbin
%attr(555,root,root) /usr/lib/games
%ifarch x86_64 ppc64 sparc64 s390x aarch64 ppc64le mips64 mips64el riscv64
/usr/%{_lib}
%else
%attr(555,root,root) /usr/lib/bpf
%attr(555,root,root) /usr/lib/X11
%attr(555,root,root) /usr/lib/pm-utils
%endif
/usr/libexec
/usr/local
/usr/sbin
%dir /usr/share
/usr/share/aclocal
/usr/share/appdata
/usr/share/applications
/usr/share/augeas
/usr/share/backgrounds
%dir /usr/share/bash-completion
/usr/share/bash-completion/completions
/usr/share/bash-completion/helpers
/usr/share/desktop-directories
/usr/share/dict
/usr/share/doc
%dir /usr/share/empty
/usr/share/games
/usr/share/gnome
/usr/share/help
/usr/share/icons
/usr/share/idl
/usr/share/info
%dir /usr/share/licenses
%dir /usr/share/locale
%dir /usr/share/man
/usr/share/metainfo
/usr/share/mime-info
/usr/share/misc
/usr/share/omf
/usr/share/pixmaps
/usr/share/sounds
/usr/share/themes
/usr/share/xsessions
/usr/share/X11
/usr/share/wayland-sessions
/usr/src
/usr/tmp
%dir /var
/var/adm
%dir /var/cache
/var/cache/bpf
/var/db
/var/empty
/var/ftp
/var/games
/var/lib
/var/local
%ghost /var/lock
/var/log
/var/mail
/var/nis
/var/opt
/var/preserve
%ghost /var/run
%dir /var/spool
%attr(755,root,root) /var/spool/lpd
%attr(775,root,mail) /var/spool/mail
%attr(1777,root,root) /var/tmp
/var/yp
%ifarch aarch64
%config %{_sysconfdir}/ld.so.conf.d/aarch64.conf
%dir %{_sysconfdir}/ld.so.conf.d
%endif
