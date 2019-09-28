# don't make useless debug packages
%define _enable_debug_packages %{nil}
%define debug_package %{nil}

# _without = java enabled, _with = java disabled
%ifnarch %mips riscv64
%bcond_without java
%endif

Summary:	Bundle of CA Root Certificates
Name:		rootcerts
# <mrl> Use this versioning style in order to be easily backportable.
# Note that the release is the last two digits on the version.
# All BuildRequires for rootcerts should be done this way:
# BuildRequires: rootcerts >= 0:20070402.00, for example
# - NEVER specifying the %%{release}
Epoch:		1
Version:	20190820.00
Release:	1
License:	GPL
Group:		System/Servers
URL:		%{disturl}
# S0 originates from http://switch.dl.sourceforge.net/sourceforge/courier/courier-0.52.1.tar.bz2
Source0:	rootcerts.tar.bz2
#  http://hg.mozilla.org/projects/nss/raw-file/tip/lib/ckfw/builtins/certdata.txt
Source1:	certdata.txt
Source2:	rootcerts-igp-brasil.txt
# http://www.cacert.org/certs/root.der
Source3:	cacert.org.der
# http://qa.mandriva.com/show_bug.cgi?id=29612
# https://www.verisign.com/support/verisign-intermediate-ca/secure-site-intermediate/index.html
Source4:	verisign-class-3-secure-server-ca.pem
#http://www.cacert.org/certs/root.crt
Source5:	cacert.org.crt
# Java JKS keystore generator:
# http://cvs.fedora.redhat.com/viewcvs/devel/ca-certificates/generate-cacerts.pl
Source6:	generate-cacerts.pl
# http://www.cacert.org/certs/class3.der
Source7:	cacert_class3.der
# certificates from signet
# http://www.signet.pl/repository/index.html
Source8:	http://www.signet.pl/repository/signetrootca/rootca_der.crt
Source9:	http://www.signet.pl/repository/publicca/publicxca_der.crt
# certificates from https://letsencrypt.org
Source10:	https://letsencrypt.org/certs/isrgrootx1.der
# Fix overwriting issue with generate-cacerts.pl
Patch0:		generate-cacerts-fix-entrustsslca.patch
# Some hacks to make generate-cacerts.pl work with some of our certificates
Patch1:		generate-cacerts-mandriva.patch
# Just rename identically named certificates that are not handled by mandriva.cpatch
Patch2:		generate-cacerts-rename-duplicates.patch
%if %{mdvver} > 3000000
Patch3:		rootcerts-fix-mkcerts-to-work-with-new-openssl.patch
Patch4:		use-openssl-rehash-instead-of-c_rehash.patch
%endif
BuildRequires:	perl
BuildRequires:	openssl
BuildRequires:	nss
BuildRequires:	automake
BuildRequires:	libtool
%if %{with java}
BuildRequires:	java-devel
BuildRequires:	javapackages-tools
%endif
BuildArch:	noarch
Provides:	ca-certificates

%description
This is a bundle of X.509 certificates of public Certificate
Authorities (CA). These were automatically extracted from Mozilla's
root CA list (the file "certdata.txt"). It contains the certificates
in both plain text and PEM format and therefore can be directly used
with an Apache/mod_ssl webserver for SSL client authentication. Just
configure this file as the SSLCACertificateFile.

%if %{with java}
%package java
Summary:	Bundle of CA Root Certificates for Java
Group:		Development/Java

%description java
Bundle of X.509 certificates of public Certificate Authorities (CA)
in a format used by Java Runtime Environment.
%endif

%prep
%setup -q -n rootcerts

mkdir -p builtins
cp %{SOURCE1} builtins/certdata.txt

# extract the license
head -4 builtins/certdata.txt > LICENSE

# add additional CA's here, needs to have the mozilla format...
cat %{SOURCE2} >> builtins/certdata.txt

# CAcert
cp %{SOURCE3} .
cp %{SOURCE5} .
cp %{SOURCE6} .
cp %{SOURCE7} .
cp %{SOURCE8} .
cp %{SOURCE9} .
cp %{SOURCE10} .

%patch0 -p0
%patch1 -p0
%patch2 -p0
%if %{mdvver} > 3000000
%patch3 -p1
%patch4 -p1
%endif

%build
rm -f configure
libtoolize --copy --force; aclocal; autoconf; automake --foreign --add-missing --copy

# CAcert
# http://wiki.cacert.org/wiki/NSSLib
addbuiltin -n "CAcert Inc." -t "CT,C,C" < cacert.org.der >> builtins/certdata.txt
addbuiltin -n "CAcert Inc. Class 3" -t "CT,C,C" < cacert_class3.der >> builtins/certdata.txt

# new verisign intermediate certificate
# -t trust        trust flags (cCTpPuw).
openssl x509 -in %{SOURCE4} -inform PEM -outform DER | \
	addbuiltin -n "VeriSign Class 3 Secure Server CA" \
	-t "CT,C,C" >> builtins/certdata.txt

perl mkcerts.pl > certs.sh

%configure --with-certdb=%{_sysconfdir}/pki/tls/rootcerts

%make_build

cat pem/*.pem > ca-bundle.crt
cat %{SOURCE4} >> ca-bundle.crt

%if %{with java}
mkdir java
cd java
LC_ALL=C perl ../generate-cacerts.pl %{java_home}/bin/keytool ../ca-bundle.crt
cd ..
%endif

%install
%make_install

install -d %{buildroot}%{_sysconfdir}/pki/tls/certs
install -d %{buildroot}%{_sysconfdir}/pki/tls/mozilla
install -d %{buildroot}%{_bindir}

install -m0644 ca-bundle.crt %{buildroot}%{_sysconfdir}/pki/tls/certs/
ln -s certs/ca-bundle.crt %{buildroot}%{_sysconfdir}/pki/tls/cert.pem

install -m0644 builtins/certdata.txt %{buildroot}%{_sysconfdir}/pki/tls/mozilla/

%if %{with java}
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

for d in certs private; do
    ln -sf %{_sysconfdir}/pki/tls/$d %{buildroot}%{_sysconfdir}/ssl/
done

%files
%doc README LICENSE
%{_sysconfdir}/pki/tls/cert.pem
%config(noreplace) %{_sysconfdir}/pki/tls/certs/ca-bundle.crt
%config(noreplace) %{_sysconfdir}/pki/tls/rootcerts/*
%config(noreplace) %{_sysconfdir}/pki/tls/mozilla/certdata.txt
%{_sysconfdir}/ssl/certs
%{_sysconfdir}/ssl/private

%if %{with java}
%files java
%dir %{_sysconfdir}/pki/java
%config(noreplace) %{_sysconfdir}/pki/java/cacerts
%endif
