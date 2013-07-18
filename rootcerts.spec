# don't make useless debug packages
%define _enable_debug_packages	%{nil}
%define debug_package		%{nil}

# _without = java enabled, _with = java disabled
%if %mdkversion < 200900
%bcond_with java
%else
%ifnarch %mips
%bcond_without java
%else
%bcond_with java
%endif
%endif

Summary:	Bundle of CA Root Certificates
Name:		rootcerts
# <mrl> Use this versioning style in order to be easily backportable.
# Note that the release is the last two digits on the version.
# All BuildRequires for rootcerts should be done this way:
# BuildRequires: rootcerts >= 0:20070402.00, for example
# - NEVER specifying the %%{release}
Epoch:		1
Version:	20121229.00
Release:	2
License:	GPL
Group:		System/Servers
URL:		http://www.mandriva.com
# S0 originates from http://switch.dl.sourceforge.net/sourceforge/courier/courier-0.52.1.tar.bz2
Source0:	rootcerts.tar.bz2
# www.mail-archive.com/ modssl-users@modssl.org/msg16980.html
Source1:	certdata.txt
Source2:	rootcerts-igp-brasil.txt
# http://www.cacert.org/certs/root.der
Source3:	cacert.org.der
# http://qa.mandriva.com/show_bug.cgi?id=29612
# https://www.verisign.com/support/verisign-intermediate-ca/secure-site-intermediate/index.html
Source4:	verisign-class-3-secure-server-ca.pem
# Java JKS keystore generator:
# http://cvs.fedora.redhat.com/viewcvs/devel/ca-certificates/generate-cacerts.pl
Source6:	generate-cacerts.pl
# Fix overwriting issue with generate-cacerts.pl
Patch0:		generate-cacerts-fix-entrustsslca.patch
# Some hacks to make generate-cacerts.pl work with some of our certificates
Patch1:		generate-cacerts-mandriva.patch
# Just rename identically named certificates that are not handled by mandriva.cpatch
Patch2:		generate-cacerts-rename-duplicates.patch
BuildRequires:	perl openssl nss automake libtool
%if %with java
BuildRequires:	java-rpmbuild
%endif
Buildroot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
This is a bundle of X.509 certificates of public Certificate
Authorities (CA). These were automatically extracted from Mozilla's
root CA list (the file "certdata.txt"). It contains the certificates
in both plain text and PEM format and therefore can be directly used
with an Apache/mod_ssl webserver for SSL client authentication. Just
configure this file as the SSLCACertificateFile.

%if %with java
%package java
Summary:	Bundle of CA Root Certificates for Java
Group:		Development/Java

%description java
Bundle of X.509 certificates of public Certificate Authorities (CA)
in a format used by Java Runtime Environment.
%endif

%prep

%setup -q -n rootcerts

#cvs -d :pserver:anonymous@cvs-mirror.mozilla.org:/cvsroot co -p mozilla/security/nss/lib/ckfw/builtins/certdata.txt > certdata.txt

mkdir -p builtins
cp %{SOURCE1} builtins/certdata.txt

# extract the license
head -36 builtins/certdata.txt > LICENSE

# add additional CA's here, needs to have the mozilla format...
cat %{SOURCE2} >> builtins/certdata.txt

# CAcert
cp %{SOURCE3} .

cp %{SOURCE6} .
%patch0 -p0
%patch1 -p0
%patch2 -p0

%build 
rm -f configure
libtoolize --copy --force; aclocal; autoconf; automake --foreign --add-missing --copy

# CAcert
# http://wiki.cacert.org/wiki/NSSLib
addbuiltin -n "CAcert Inc." -t "CT,C,C" < cacert.org.der >> builtins/certdata.txt

# new verisign intermediate certificate
# -t trust        trust flags (cCTpPuw).
openssl x509 -in %{SOURCE4} -inform PEM -outform DER | \
	addbuiltin -n "VeriSign Class 3 Secure Server CA" \
	-t "CT,C,C" >> builtins/certdata.txt

perl mkcerts.pl > certs.sh

%configure2_5x --with-certdb=%{_sysconfdir}/pki/tls/rootcerts
%make
cat pem/*.pem > ca-bundle.crt
cat %{SOURCE4} >> ca-bundle.crt

%if %with java
mkdir -p java
cd java
LC_ALL=C perl ../generate-cacerts.pl %{java_home}/bin/keytool ../ca-bundle.crt
cd ..
%endif

%install
rm -rf %{buildroot}

%makeinstall_std

install -d %{buildroot}%{_sysconfdir}/pki/tls/certs
install -d %{buildroot}%{_sysconfdir}/pki/tls/mozilla
install -d %{buildroot}%{_bindir}

install -m0644 ca-bundle.crt %{buildroot}%{_sysconfdir}/pki/tls/certs/
ln -s certs/ca-bundle.crt %{buildroot}%{_sysconfdir}/pki/tls/cert.pem

install -m0644 builtins/certdata.txt %{buildroot}%{_sysconfdir}/pki/tls/mozilla/

%if %with java
install -d %{buildroot}%{_sysconfdir}/pki/java
install -m0644 java/cacerts %{buildroot}%{_sysconfdir}/pki/java/
%endif

cat > README << EOF

R O O T C E R T S
-----------------

This is a bundle of X.509 certificates of public Certificate
Authorities (CA). These were automatically extracted from Mozilla's
root CA list (the file "certdata.txt"). It contains the certificates
in both plain text and PEM format and therefore can be directly used
with an Apache/mod_ssl webserver for SSL client authentication. Just
configure this file as the SSLCACertificateFile.

EOF

# fix #58107
install -d %{buildroot}%{_sysconfdir}/ssl
ln -sf %{_sysconfdir}/pki/tls/certs %{buildroot}%{_sysconfdir}/ssl/certs

%clean
rm -rf %{buildroot}

%files 
%defattr(-,root,root)
%doc README LICENSE
%{_sysconfdir}/pki/tls/cert.pem
%config(noreplace) %{_sysconfdir}/pki/tls/certs/ca-bundle.crt
%config(noreplace) %{_sysconfdir}/pki/tls/rootcerts/*
%config(noreplace) %{_sysconfdir}/pki/tls/mozilla/certdata.txt
%{_sysconfdir}/ssl/certs

%if %with java
%files java
%defattr(-,root,root)
%dir %{_sysconfdir}/pki/java
%config(noreplace) %{_sysconfdir}/pki/java/cacerts
%endif


%changelog
* Sat Jun 30 2012 Oden Eriksson <oeriksson@mandriva.com> 1:20120628.00-1mdv2012.0
+ Revision: 807609
- new certdata.txt file from upstream

* Thu Feb 23 2012 Oden Eriksson <oeriksson@mandriva.com> 1:20120218.00-1
+ Revision: 779386
- new certdata.txt as of 2012/02/18

* Thu Jan 26 2012 Oden Eriksson <oeriksson@mandriva.com> 1:20120117.00-1
+ Revision: 769149
- new certdata.txt file from upstream cvs as of 2012/01/17

* Sat Nov 05 2011 Oden Eriksson <oeriksson@mandriva.com> 1:20111103.00-1
+ Revision: 720507
- 20111103

  + Paulo Andrade <pcpa@mandriva.com.br>
    - Assume a working java-1.6.0-openjdk on arm

* Wed Sep 07 2011 Oden Eriksson <oeriksson@mandriva.com> 1:20110902.00-1
+ Revision: 698537
- DigiNotar, bye bye

* Wed Aug 31 2011 Oden Eriksson <oeriksson@mandriva.com> 1:20110830.00-1
+ Revision: 697585
- new certdata.txt file (fixes MFSA 2011-34 Protection against fraudulent DigiNotar certificates)

* Fri Aug 12 2011 Oden Eriksson <oeriksson@mandriva.com> 1:20110801.00-1
+ Revision: 694114
- fix deps (wtf?)
- new certdata.txt file as of august the first 2011

* Mon May 09 2011 Oden Eriksson <oeriksson@mandriva.com> 1:20110413.00-1
+ Revision: 673014
- whoops, forgot to drop the patch
- new certdata.txt from upstream cvs as of 2011/04/13

* Thu May 05 2011 Oden Eriksson <oeriksson@mandriva.com> 1:20110323.00-2
+ Revision: 669429
- mass rebuild

* Fri Mar 25 2011 Oden Eriksson <oeriksson@mandriva.com> 1:20110323.00-1
+ Revision: 648516
- new certdata.txt file from upstream (2011/03/23)

* Sat Dec 25 2010 Oden Eriksson <oeriksson@mandriva.com> 1:20101202.00-1mdv2011.0
+ Revision: 624972
- new certdata.txt file from upstream cvs (20101202)

* Thu Nov 25 2010 Oden Eriksson <oeriksson@mandriva.com> 1:20101119.00-1mdv2011.0
+ Revision: 601001
- new certdata.txt from upstream (2010-11-19)

* Thu Sep 09 2010 Oden Eriksson <oeriksson@mandriva.com> 1:20100827.00-1mdv2011.0
+ Revision: 576922
- new certdata.txt file as of 2010/08/27

* Mon May 17 2010 Oden Eriksson <oeriksson@mandriva.com> 1:20100408.00-1mdv2010.1
+ Revision: 544960
- drop the RSA Security 1024 V3 Root cert

* Tue Apr 06 2010 Oden Eriksson <oeriksson@mandriva.com> 1:20100403.01-1mdv2010.1
+ Revision: 532249
- new certdata.txt from upstream (20100403)

* Fri Mar 12 2010 Oden Eriksson <oeriksson@mandriva.com> 1:20100216.01-1mdv2010.1
+ Revision: 518349
- fix #58107 (provide compatibility symlink for Adobe Flash)
- new certdata.txt (20100216) from upstream

* Wed Feb 03 2010 Oden Eriksson <oeriksson@mandriva.com> 1:20091203.04-1mdv2010.1
+ Revision: 500052
- P3: remove the offending MD5 Collisions Forged Rogue CA 25c3 cert

* Thu Jan 28 2010 Oden Eriksson <oeriksson@mandriva.com> 1:20091203.03-1mdv2010.1
+ Revision: 497698
- avoid making useless (empty) debug packages

* Thu Jan 28 2010 Oden Eriksson <oeriksson@mandriva.com> 1:20091203.02-1mdv2010.1
+ Revision: 497654
- fix the bcond stuff (thanks anssi)

* Thu Jan 28 2010 Oden Eriksson <oeriksson@mandriva.com> 1:20091203.01-1mdv2010.1
+ Revision: 497593
- disable java cert generations on older products

* Sun Jan 24 2010 Oden Eriksson <oeriksson@mandriva.com> 1:20091203.00-1mdv2010.1
+ Revision: 495449
- new certdata.txt file as of 2009/12/03
- the java certs won't build unless using a safe locale

* Mon Oct 19 2009 Anssi Hannula <anssi@mandriva.org> 1:20090831.00-1mdv2010.0
+ Revision: 458242
- add multiple "-alt" suffixes to java certificate shortnames if more
  than 2 certificates share the same name
  (cacerts-rename-duplicates.patch modified)

  + Oden Eriksson <oeriksson@mandriva.com>
    - new certdata.txt from mozilla

* Mon Sep 28 2009 Olivier Blin <blino@mandriva.org> 1:20090814.00-2mdv2010.0
+ Revision: 450336
- disable java on mips & arm, implying it's not noarch anymore
  (from Arnaud Patard)

* Sat Aug 22 2009 Oden Eriksson <oeriksson@mandriva.com> 1:20090814.00-1mdv2010.0
+ Revision: 419733
- new snapshot (20090814)

* Sun Aug 02 2009 Oden Eriksson <oeriksson@mandriva.com> 1:20090521.00-1mdv2010.0
+ Revision: 407545
- new cvs snap (20090521)
- the IGC/A cert was added upstream (S5)

* Mon Mar 23 2009 Anssi Hannula <anssi@mandriva.org> 1:20090115.00-1mdv2009.1
+ Revision: 360711
- java: rename identically named certificates that are not handled by
  mandriva.patch

  + Oden Eriksson <oeriksson@mandriva.com>
    - new certdata.txt file

* Sat Jan 24 2009 Oden Eriksson <oeriksson@mandriva.com> 1:20081017.00-2mdv2009.1
+ Revision: 333321
- roll back the certdata.txt file for now
- new certdata.txt file

* Fri Oct 24 2008 Oden Eriksson <oeriksson@mandriva.com> 1:20081017.00-1mdv2009.1
+ Revision: 296928
- new S1

* Sat Jul 05 2008 Anssi Hannula <anssi@mandriva.org> 1:20080503.00-2mdv2009.0
+ Revision: 232015
- add java subpackage that contains cacerts file for JRE, and a
  --with[out] java build option to disable it

* Fri Jul 04 2008 Oden Eriksson <oeriksson@mandriva.com> 1:20080503.00-1mdv2009.0
+ Revision: 231658
- new certdata.txt

* Wed Jun 18 2008 Thierry Vignaud <tv@mandriva.org> 1:20080117.00-2mdv2009.0
+ Revision: 225323
- rebuild

* Thu Feb 14 2008 Oden Eriksson <oeriksson@mandriva.com> 1:20080117.00-1mdv2008.1
+ Revision: 168072
- new certdata.txt (Guenter Knauf)

* Thu Dec 20 2007 Oden Eriksson <oeriksson@mandriva.com> 1:20070713.00-1mdv2008.1
+ Revision: 135400
- new S1 from upstream cvs

* Mon Dec 17 2007 Thierry Vignaud <tv@mandriva.org> 1:20070402.00-1mdv2008.1
+ Revision: 126645
- kill re-definition of %%buildroot on Pixel's request

