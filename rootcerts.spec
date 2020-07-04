# don't make useless debug packages
%define _enable_debug_packages %{nil}
%define debug_package %{nil}

# _without = java enabled, _with = java disabled
%ifnarch %mips riscv64
%bcond_without java
%endif

%define pkidir %{_sysconfdir}/pki
%define catrustdir %{_sysconfdir}/pki/ca-trust
%define classic_tls_bundle ca-bundle.crt
%define openssl_format_trust_bundle ca-bundle.trust.crt
%define p11_format_bundle ca-bundle.trust.p11-kit
%define legacy_default_bundle ca-bundle.legacy.default.crt
%define legacy_disable_bundle ca-bundle.legacy.disable.crt
%define java_bundle java/cacerts

Summary:        Bundle of CA Root Certificates
Name:           rootcerts
# <mrl> Use this versioning style in order to be easily backportable.
# Note that the release is the last two digits on the version.
# All BuildRequires for rootcerts should be done this way:
# BuildRequires: rootcerts >= 0:20070402.00, for example
# - NEVER specifying the %%{release}
Epoch:          1
Version:        20200704.00
Release:        1
License:        GPL
Group:          System/Servers
URL:            %{disturl}
# For Source0, the NSS commit trunk version of this file is here:
# https://hg.mozilla.org/projects/nss/raw-file/default/lib/ckfw/builtins/certdata.txt
# See https://hg.mozilla.org/projects/nss/log/default/lib/ckfw/builtins/certdata.txt for new versions
# The version tag for this package should come from the commit date of the version used from the NSS repository above
# To choose which NSS commit version to use, we can check the certdata.txt file used in either...
# the current Mozilla release:
# https://hg.mozilla.org/releases/mozilla-release/log/default/security/nss/lib/ckfw/builtins/certdata.txt
# or the Mozilla development commit trunk:
# https://hg.mozilla.org/mozilla-central/log/default/security/nss/lib/ckfw/builtins/certdata.txt
# Ideally, it should correspond to the version shipped in the NSS release we are using
Source0:	certdata.txt
# Similarly, Source1 comes from:
# https://hg.mozilla.org/projects/nss/raw-file/default/lib/ckfw/builtins/nssckbi.h
# Check the log to see if it needs to be updated:
# https://hg.mozilla.org/projects/nss/log/default/lib/ckfw/builtins/nssckbi.h
Source1:	nssckbi.h
Source2:	update-ca-trust
Source3:	trust-fixes
Source4:	certdata2pem.py
Source5:	ca-legacy.conf
Source6:	ca-legacy
Source9:	ca-legacy.8.txt
Source10:	update-ca-trust.8.txt
BuildRequires:  python3
BuildRequires:  openssl
BuildRequires:  nss
BuildRequires:  automake
BuildRequires:  libtool
%if %{with java}
BuildRequires:  java-devel
BuildRequires:  javapackages-tools
%endif
BuildRequires:	asciidoc
BuildRequires:	xsltproc 

BuildArch:      noarch
Provides:       ca-certificates

%description
This is a bundle of X.509 certificates of public Certificate
Authorities (CA). These were automatically extracted from Mozilla's
root CA list (the file "certdata.txt"). It contains the certificates
in both plain text and PEM format and therefore can be directly used
with an Apache/mod_ssl webserver for SSL client authentication. Just
configure this file as the SSLCACertificateFile.

%if %{with java}
%package java
Summary:        Bundle of CA Root Certificates for Java
Group:          Development/Java

%description java
Bundle of X.509 certificates of public Certificate Authorities (CA)
in a format used by Java Runtime Environment.
%endif

%prep
rm -rf %{name}
mkdir -p %{name}/certs/legacy-default
mkdir %{name}/certs/legacy-disable
mkdir %{name}/java

%build
pushd %{name}/certs
 cp %{SOURCE0} certdata.txt
 python3 %{SOURCE4} >c2p.log 2>c2p.err
popd
pushd %{name}
 (
   cat <<EOF
# This is a bundle of X.509 certificates of public Certificate
# Authorities.  It was generated from the Mozilla root CA list.
# These certificates and trust/distrust attributes use the file format accepted
# by the p11-kit-trust module.
#
# Source: nss/lib/ckfw/builtins/certdata.txt
# Source: nss/lib/ckfw/builtins/nssckbi.h
#
# Generated from:
EOF
   cat %{SOURCE1}  |grep -w NSS_BUILTINS_LIBRARY_VERSION | awk '{print "# " $2 " " $3}';
   echo '#';
 ) > %{p11_format_bundle}

 touch %{legacy_default_bundle}
 NUM_LEGACY_DEFAULT=`find certs/legacy-default -type f | wc -l`
 if [ $NUM_LEGACY_DEFAULT -ne 0 ]; then
     for f in certs/legacy-default/*.crt; do 
       echo "processing $f"
       tbits=`sed -n '/^# openssl-trust/{s/^.*=//;p;}' $f`
       alias=`sed -n '/^# alias=/{s/^.*=//;p;q;}' $f | sed "s/'//g" | sed 's/"//g'`
       targs=""
       if [ -n "$tbits" ]; then
          for t in $tbits; do
             targs="${targs} -addtrust $t"
          done
       fi
       if [ -n "$targs" ]; then
          echo "legacy default flags $targs for $f" >> info.trust
          openssl x509 -text -in "$f" -trustout $targs -setalias "$alias" >> %{legacy_default_bundle}
       fi
     done
 fi

 touch %{legacy_disable_bundle}
 NUM_LEGACY_DISABLE=`find certs/legacy-disable -type f | wc -l`
 if [ $NUM_LEGACY_DISABLE -ne 0 ]; then
     for f in certs/legacy-disable/*.crt; do 
       echo "processing $f"
       tbits=`sed -n '/^# openssl-trust/{s/^.*=//;p;}' $f`
       alias=`sed -n '/^# alias=/{s/^.*=//;p;q;}' $f | sed "s/'//g" | sed 's/"//g'`
       targs=""
       if [ -n "$tbits" ]; then
          for t in $tbits; do
             targs="${targs} -addtrust $t"
          done
       fi
       if [ -n "$targs" ]; then
          echo "legacy disable flags $targs for $f" >> info.trust
          openssl x509 -text -in "$f" -trustout $targs -setalias "$alias" >> %{legacy_disable_bundle}
       fi
     done
 fi

 P11FILES=`find certs -name \*.tmp-p11-kit | wc -l`
 if [ $P11FILES -ne 0 ]; then
   for p in certs/*.tmp-p11-kit; do 
     cat "$p" >> %{p11_format_bundle}
   done
 fi
 # Append our trust fixes
 cat %{SOURCE3} >> %{p11_format_bundle}
popd

#manpage
cp %{SOURCE10} %{name}/update-ca-trust.8.txt
asciidoc.py -v -d manpage -b docbook %{name}/update-ca-trust.8.txt
xsltproc --nonet -o %{name}/update-ca-trust.8 /etc/asciidoc/docbook-xsl/manpage.xsl %{name}/update-ca-trust.8.xml

cp %{SOURCE9} %{name}/ca-legacy.8.txt
asciidoc.py -v -d manpage -b docbook %{name}/ca-legacy.8.txt
xsltproc --nonet -o %{name}/ca-legacy.8 /etc/asciidoc/docbook-xsl/manpage.xsl %{name}/ca-legacy.8.xml


%install
mkdir -p -m 755 %{buildroot}%{pkidir}/java
mkdir -p -m 755 %{buildroot}%{catrustdir}/source
mkdir -p -m 755 %{buildroot}%{catrustdir}/source/anchors
mkdir -p -m 755 %{buildroot}%{catrustdir}/source/blacklist
mkdir -p -m 755 %{buildroot}%{catrustdir}/extracted
mkdir -p -m 755 %{buildroot}%{catrustdir}/extracted/pem
mkdir -p -m 755 %{buildroot}%{catrustdir}/extracted/openssl
mkdir -p -m 755 %{buildroot}%{catrustdir}/extracted/java
mkdir -p -m 755 %{buildroot}%{catrustdir}/extracted/edk2
mkdir -p -m 755 %{buildroot}%{_mandir}/man8
install -p -m 644 %{name}/update-ca-trust.8 %{buildroot}%{_mandir}/man8
install -p -m 644 %{name}/ca-legacy.8 %{buildroot}%{_mandir}/man8
install -d %{buildroot}%{_sysconfdir}/pki/tls/certs
install -d %{buildroot}%{_sysconfdir}/pki/tls/certs/source
install -d %{buildroot}%{_sysconfdir}/pki/tls/mozilla
install -d %{buildroot}%{_bindir}
install -p -m 644 %{SOURCE5} %{buildroot}%{catrustdir}/ca-legacy.conf
install -p -m 755 %{SOURCE2} %{buildroot}%{_bindir}/update-ca-trust
install -p -m 755 %{SOURCE6} %{buildroot}%{_bindir}/ca-legacy

install -m0644 %{name}/certs/certdata.txt %{buildroot}%{_sysconfdir}/pki/tls/mozilla/

mkdir -p -m 755 %{buildroot}%{catrustdir}/source
mkdir -p -m 755 %{buildroot}%{_datadir}/pki/ca-trust-source
install -p -m 644 %{name}/%{p11_format_bundle} %{buildroot}%{_datadir}/pki/ca-trust-source/%{p11_format_bundle}

mkdir -p -m 755 %{buildroot}%{_datadir}/pki/ca-trust-legacy
install -p -m 644 %{name}/%{legacy_default_bundle} %{buildroot}%{_datadir}/pki/ca-trust-legacy/%{legacy_default_bundle}
install -p -m 644 %{name}/%{legacy_disable_bundle} %{buildroot}%{_datadir}/pki/ca-trust-legacy/%{legacy_disable_bundle}

%if %with java
install -d %{buildroot}%{_sysconfdir}/pki/java
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


# touch ghosted files that will be extracted dynamically
# Set chmod 444 to use identical permission
touch %{buildroot}%{catrustdir}/extracted/pem/tls-ca-bundle.pem
chmod 444 %{buildroot}%{catrustdir}/extracted/pem/tls-ca-bundle.pem
touch %{buildroot}%{catrustdir}/extracted/pem/email-ca-bundle.pem
chmod 444 %{buildroot}%{catrustdir}/extracted/pem/email-ca-bundle.pem
touch %{buildroot}%{catrustdir}/extracted/pem/objsign-ca-bundle.pem
chmod 444 %{buildroot}%{catrustdir}/extracted/pem/objsign-ca-bundle.pem
touch %{buildroot}%{catrustdir}/extracted/openssl/%{openssl_format_trust_bundle}
chmod 444 %{buildroot}%{catrustdir}/extracted/openssl/%{openssl_format_trust_bundle}
touch %{buildroot}%{catrustdir}/extracted/%{java_bundle}
chmod 444 %{buildroot}%{catrustdir}/extracted/%{java_bundle}
touch %{buildroot}%{catrustdir}/extracted/edk2/cacerts.bin
chmod 444 %{buildroot}%{catrustdir}/extracted/edk2/cacerts.bin

# legacy filenames
ln -s %{catrustdir}/extracted/pem/tls-ca-bundle.pem \
    %{buildroot}%{pkidir}/tls/cert.pem
ln -s %{catrustdir}/extracted/pem/tls-ca-bundle.pem \
    %{buildroot}%{pkidir}/tls/certs/%{classic_tls_bundle}
ln -s %{catrustdir}/extracted/openssl/%{openssl_format_trust_bundle} \
    %{buildroot}%{pkidir}/tls/certs/%{openssl_format_trust_bundle}
ln -s %{catrustdir}/extracted/%{java_bundle} \
    %{buildroot}%{pkidir}/%{java_bundle}

%post
%{_bindir}/ca-legacy install
%{_bindir}/update-ca-trust

%files
%doc README 
%dir %{catrustdir}/source
%dir %{catrustdir}/source/anchors
%dir %{catrustdir}/source/blacklist
%{_sysconfdir}/pki/tls/cert.pem
%{_mandir}/man8/ca-legacy.8.*
%{_mandir}/man8/update-ca-trust.8.*
%config(noreplace) %{_sysconfdir}/pki/tls/mozilla/certdata.txt
%{_sysconfdir}/ssl/certs
%{_sysconfdir}/ssl/private
# symlinks for old locations
%{pkidir}/tls/certs/%{classic_tls_bundle}
%{pkidir}/tls/certs/%{openssl_format_trust_bundle}
# master bundle file with trust
%{_datadir}/pki/ca-trust-source/%{p11_format_bundle}

%{_datadir}/pki/ca-trust-legacy/%{legacy_default_bundle}
%{_datadir}/pki/ca-trust-legacy/%{legacy_disable_bundle}
# update/extract tool
%config(noreplace) %{catrustdir}/ca-legacy.conf
%{_bindir}/update-ca-trust
%{_bindir}/ca-legacy
%ghost %{catrustdir}/source/ca-bundle.legacy.crt
# files extracted files
%ghost %{catrustdir}/extracted/pem/tls-ca-bundle.pem
%ghost %{catrustdir}/extracted/pem/email-ca-bundle.pem
%ghost %{catrustdir}/extracted/pem/objsign-ca-bundle.pem
%ghost %{catrustdir}/extracted/openssl/%{openssl_format_trust_bundle}
%ghost %{catrustdir}/extracted/%{java_bundle}
%ghost %{catrustdir}/extracted/edk2/cacerts.bin


%if %{with java}
%files java
%dir %{_sysconfdir}/pki/java
%config(noreplace) %{_sysconfdir}/pki/java/cacerts
%endif

