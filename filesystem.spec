Summary: The basic directory layout for a Linux system
Name: filesystem
Version: 3.1+git3
Release: 1
License: Public Domain
URL: https://fedorahosted.org/filesystem
Group: System/Base
BuildArch: noarch
Buildroot: %{_tmppath}/%{name}-%{version}-%{release}-root
# Raw source1 URL: https://fedorahosted.org/filesystem/browser/lang-exceptions?format=raw
Source1: https://fedorahosted.org/filesystem/browser/lang-exceptions
Source2: iso_639.sed
Source3: iso_3166.sed
Requires(pre): setup >= 2.5.4-1
BuildRequires: iso-codes
# The /run got moved in systemd 187 to this package, thus conflicts with older ones.
Conflicts: systemd < 187

%description
The filesystem package is one of the basic packages that is installed
on a Linux system. Filesystem contains the basic directory layout
for a Linux operating system, including the correct permissions for
the directories.

%prep
rm -f $RPM_BUILD_DIR/filelist

%build

%install
rm -rf %{buildroot}
mkdir %{buildroot}
install -p -c -m755 %SOURCE2 %{buildroot}/iso_639.sed
install -p -c -m755 %SOURCE3 %{buildroot}/iso_3166.sed

cd %{buildroot}

mkdir -p boot dev \
        bin lib sbin \
        etc/{X11/{applnk,fontpath.d},xdg/autostart,opt,pm/{config.d,power.d,sleep.d},xinetd.d,skel,sysconfig,pki} \
        home media mnt opt proc root run/lock srv sys tmp \
        usr/{bin,etc,games,include,%{_lib}/{games,sse2,tls,X11,pm-utils/{module.d,power.d,sleep.d}},lib/{games,locale,modules,sse2},libexec,local/{bin,etc,games,lib,%{_lib},sbin,src,share/{applications,man/man{1,2,3,4,5,6,7,8,9,n,1x,2x,3x,4x,5x,6x,7x,8x,9x},info},libexec,include,},sbin,share/{aclocal,applications,augeas/lenses,backgrounds,desktop-directories,dict,doc,empty,games,ghostscript/conf.d,gnome,icons,idl,info,man/man{1,2,3,4,5,6,7,8,9,n,1x,2x,3x,4x,5x,6x,7x,8x,9x,0p,1p,3p},mime-info,misc,omf,pixmaps,sounds,themes,xsessions,X11},src,src/kernels,src/debug} \
        var/{adm,empty,gopher,lib/{games,misc,rpm-state},local,lock/subsys,log,nis,preserve,run,spool/{mail,lpd},tmp,db,cache,opt,games,yp}

ln -snf ../var/tmp usr/tmp
ln -snf spool/mail var/mail

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
        egrep -q "[[:space:]]${locale%%_*}[[:space:]]" \
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

%post -p <lua>
posix.symlink("../run", "/var/run")
posix.symlink("../run/lock", "/var/lock")

%if "%_arch" == "aarch64"
%posttrans -p <lua>
-- Perform the lib64 migration if some packages are installing to
-- /lib. 

-- our lua doesn't have this function builtin yet
-- from https://github.com/stevedonovan/Penlight/blob/master/lua/pl/path.lua#L279
--- normalize a path name.
--  `A//B`, `A/./B`, and `A/foo/../B` all become `A/B`.
-- @string P a file path
function normpath(P)
    local append, concat, remove = table.insert, table.concat, table.remove
    -- Split path into anchor and relative path.
    local anchor = ''
    local sep = '/'
    -- According to POSIX, in path start '//' and '/' are distinct,
    -- but '///+' is equivalent to '/'.
    -- We dont care.
    if P:sub(1,1) == '/' then
        anchor = '/'
        P = P:match '^/*(.*)$'
    end

    local parts = {}
    for part in P:gmatch('[^'..sep..']+') do
        if part == '..' then
            if #parts ~= 0 and parts[#parts] ~= '..' then
                remove(parts)
            else
                append(parts, part)
            end
        elseif part ~= '.' then
            append(parts, part)
        end
    end
    P = anchor..concat(parts, sep)
    if P == '' then P = '.' end
    return P
end

local function movedir(src, dest)
  -- move src/* dest/

  -- TODO: Check if src/dest are symlinks to each other and abort if needed
--  os.execute('echo '..src..';ls -laF '..src..'/')
--  os.execute('echo '..dest..';ls -laF '..dest..'/')
  local files = posix.dir(src)
  table.sort(files)
  for i,f in ipairs(files) do
    local sf = src..'/'..f
    local df = dest..'/'..f
    print('looking at '..sf)
    if f ~= '.' and f ~= '..' then
      local dinfo = posix.stat(df)
      local info = posix.stat(sf)

      if dinfo ~= nil then -- there is something there already...
	 print('WARNING - '..df..' already exists...')
	 if dinfo.type == 'link' then
	    -- # There's a symlink in the way
	    -- If the dest file is a symlink to the src then remove the dest so the src will replace it
	    local dlink_target = posix.readlink(df)
	    if dlink_target:sub(1,1) ~= '/' then -- relative file so normalise based on cwd=/dest
	       dlink_target = dest..'/'..dlink_target
	    end
	    local real_dtarget = normpath(dlink_target)
--            print(df..' links to '..dlink_target..' which points to '..real_dtarget)

	    -- is the src a link?
	    local real_src=""
	    if info.type == 'link' then
               local link_target = posix.readlink(sf)
	       if link_target:sub(1,1) ~= '/' then -- relative file so normalise based on cwd=/src
		  link_target = src..'/'..link_target
	       end
	       real_src = normpath(link_target)
--	       print(sf..' -> '..real_src)
	    end
	    -- why?
	    -- because /usr/bin/awk links to /usr/bin/../../bin/gawk
	    -- and /bin/awk points to /bin/gawk ... so the complete comparison is needed.
	    if real_dtarget==sf or real_dtarget==real_src then -- # remove the symlink
--               print('which is the src. So removing dest: '..df)
	       posix.unlink(df)
            else
		print('which is not the src so removing src: '..sf)
		posix.unlink(sf)
	    end
	 elseif dinfo.type == 'directory' then
            if info.type == 'directory' then
	       -- need to move all the files in sf/ to df/ in a bit
	    else
               print(' WARNING : '..df..' exists and is a directory but '..sf..' is a '..info.type..' Removing src')
              posix.unlink(sf)
	    end
         else
            print(' WARNING : '..df..' exists and is a '..dinfo.type..' file. Ignoring src.')
            posix.unlink(sf)
	 end
      end
      info = posix.stat(sf)
      if info == nil then
--	 print(sf..' removed')
      elseif info.type == 'link' then
         local link_target = posix.readlink(sf)
	 -- TODO: check if the symlink is relative and fix
         print(' - sym linking '..df..' -> '..link_target)
  	 posix.symlink(link_target, df)
         posix.unlink(sf)
      elseif info.type == 'directory' and dinfo ~= nil and dinfo.type == 'directory' then
        print(sf..' and '..df..' are directories... recursing')
	movedir(sf, df)
      elseif info.type == 'directory' or info.type == 'regular' then
        print(' - moving')
        os.rename(src..'/'..f, dest..'/'..f)
      else -- character, block, fifo, socket
	print(' - is a '..info.type.." file and can't be handled")
      end
    end
  end
  print('files in '..src)
  local files = posix.dir(src)
  table.sort(files)
  for i,f in ipairs(files) do
    print(src.."/"..f)
  end
  print('remove '..src)
  ret,errmsg = posix.rmdir(src)
  assert(ret == 0, errmsg)
end
  
local function link_moved_dir(src, dest)

  print('ls -laF /\n')
  os.execute('ls -laF /')
  print('ls -laFR '..src..'/\n')
  os.execute('ls -laFR '..src..'/')
  print('ls -laFR '..dest..'/\n')
  os.execute('ls -laFR '..dest..'/')

  print('moving '..src..' to '..dest)
  movedir(src, dest)

  print('ls -laF /\n')
  os.execute('ls -laF /')
  print('ls -laFR '..dest..'/\n')
  os.execute('ls -laFR '..dest..'/')

  print('linking '..src..' to '..dest)
  ret,errmsg = posix.symlink(dest, src)
  assert(ret == 0, errmsg)
  print('ls -laF /\n')
  os.execute('ls -laF /')
  return true
end

---------------------------------------------
-- Execution starts here

-- turn off buffering so we see os.execute in the right place
io.stdout:setvbuf 'no'

print('filesystem posttrans: Moving lib to lib64 (arch = %_obs_port_arch or %_arch)')
link_moved_dir('lib', 'lib64')

print('Execute ldconfig')
os.execute('ldconfig')
print('filesystem posttrans: All done')
%endif ## aarch64

%files -f filelist
%exclude /documentation.list 
%defattr(0755,root,root,-)
/
/bin
%attr(600,root,root) /boot
/dev
%dir /etc
/etc/X11
/etc/xdg
/etc/opt
/etc/pm
/etc/xinetd.d
/etc/skel
/etc/sysconfig
/etc/pki
/home
/lib
%ifarch x86_64 ppc ppc64 sparc sparc64 s390 s390x
/%{_lib}
%endif
/media
%dir /mnt
%dir /opt
/proc
%attr(750,root,root) /root
/run
/sbin
/srv
/sys
%attr(1777,root,root) /tmp
%dir /usr
/usr/bin
/usr/etc
/usr/games
/usr/include
/usr/lib
%ifarch x86_64 ppc ppc64 sparc sparc64 s390 s390x
/usr/%{_lib}
%endif
/usr/libexec
/usr/local
/usr/sbin
%dir /usr/share
/usr/share/aclocal
/usr/share/applications
/usr/share/augeas
/usr/share/backgrounds
/usr/share/desktop-directories
/usr/share/dict
/usr/share/doc
%dir /usr/share/empty
/usr/share/games
/usr/share/ghostscript
/usr/share/gnome
/usr/share/icons
/usr/share/idl
/usr/share/info
%dir /usr/share/locale
%dir /usr/share/man
/usr/share/mime-info
/usr/share/misc
/usr/share/omf
/usr/share/pixmaps
/usr/share/sounds
/usr/share/themes
/usr/share/xsessions
/usr/share/X11
/usr/src
/usr/tmp
%dir /var
/var/adm
/var/cache
/var/db
/var/empty
/var/games
/var/gopher
/var/lib
/var/local
%ghost %dir %attr(755,root,root) /var/lock
%ghost /var/lock/subsys
/var/log
/var/mail
/var/nis
/var/opt
/var/preserve
%ghost %attr(755,root,root) /var/run
%dir /var/spool
%attr(755,root,root) /var/spool/lpd
%attr(775,root,mail) /var/spool/mail
%attr(1777,root,root) /var/tmp
/var/yp

