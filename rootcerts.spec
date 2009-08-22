# _without = java enabled, _with = java disabled
%bcond_without java

Summary:	Bundle of CA Root Certificates
Name:		rootcerts
# <mrl> Use this versioning style in order to be easily backportable.
# Note that the release is the last two digits on the version.
# All BuildRequires for rootcerts should be done this way:
# BuildRequires: rootcerts >= 0:20070402.00, for example
# - NEVER specifying the %%{release}
Epoch:		1
Version:	20090814.00
Release:	%mkrel 1
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
BuildRequires:	perl openssl nss
%if %with java
BuildRequires:	java-rpmbuild
%endif
BuildArch:	noarch
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
perl ../generate-cacerts.pl %{java_home}/bin/keytool ../ca-bundle.crt
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

%clean
rm -rf %{buildroot}

%files 
%defattr(-,root,root)
%doc README LICENSE
%{_sysconfdir}/pki/tls/cert.pem
%config(noreplace) %{_sysconfdir}/pki/tls/certs/ca-bundle.crt
%config(noreplace) %{_sysconfdir}/pki/tls/rootcerts/*
%config(noreplace) %{_sysconfdir}/pki/tls/mozilla/certdata.txt

%if %with java
%files java
%defattr(-,root,root)
%dir %{_sysconfdir}/pki/java
%config(noreplace) %{_sysconfdir}/pki/java/cacerts
%endif
