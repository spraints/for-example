
copy: tests/test-clone-cgi
copyrev: 4829c2332c32ca2bb6af415b1f2b44650c249918

This is a test of the wire protocol over CGI-based hgweb.
initialize repository

  $ hg init test
  $ cd test
  $ echo a > a
  $ hg ci -Ama
  adding a
  $ cd ..
  $ cat >hgweb.cgi <<HGWEB
  > #
  > # An example CGI script to use hgweb, edit as necessary
  > import cgitb
  > cgitb.enable()
  > from mercurial import demandimport; demandimport.enable()
  > from mercurial.hgweb import hgweb
  > from mercurial.hgweb import wsgicgi
  > application = hgweb("test", "Empty test repository")
  > wsgicgi.launch(application)
  > HGWEB
  $ chmod 755 hgweb.cgi
  $ DOCUMENT_ROOT="/var/www/hg"; export DOCUMENT_ROOT
  $ GATEWAY_INTERFACE="CGI/1.1"; export GATEWAY_INTERFACE
  $ HTTP_ACCEPT="text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5"; export HTTP_ACCEPT
  $ HTTP_ACCEPT_CHARSET="ISO-8859-1,utf-8;q=0.7,*;q=0.7"; export HTTP_ACCEPT_CHARSET
  $ HTTP_ACCEPT_ENCODING="gzip,deflate"; export HTTP_ACCEPT_ENCODING
  $ HTTP_ACCEPT_LANGUAGE="en-us,en;q=0.5"; export HTTP_ACCEPT_LANGUAGE
  $ HTTP_CACHE_CONTROL="max-age=0"; export HTTP_CACHE_CONTROL
  $ HTTP_CONNECTION="keep-alive"; export HTTP_CONNECTION
  $ HTTP_HOST="hg.omnifarious.org"; export HTTP_HOST
  $ HTTP_KEEP_ALIVE="300"; export HTTP_KEEP_ALIVE
  $ HTTP_USER_AGENT="Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.8.0.4) Gecko/20060608 Ubuntu/dapper-security Firefox/1.5.0.4"; export HTTP_USER_AGENT
  $ PATH_INFO="/"; export PATH_INFO
  $ PATH_TRANSLATED="/var/www/hg/index.html"; export PATH_TRANSLATED
  $ REMOTE_ADDR="127.0.0.2"; export REMOTE_ADDR
  $ REMOTE_PORT="44703"; export REMOTE_PORT
  $ REQUEST_METHOD="GET"; export REQUEST_METHOD
  $ REQUEST_URI="/test/"; export REQUEST_URI
  $ SCRIPT_FILENAME="/home/hopper/hg_public/test.cgi"; export SCRIPT_FILENAME
  $ SCRIPT_NAME="/test"; export SCRIPT_NAME
  $ SCRIPT_URI="http://hg.omnifarious.org/test/"; export SCRIPT_URI
  $ SCRIPT_URL="/test/"; export SCRIPT_URL
  $ SERVER_ADDR="127.0.0.1"; export SERVER_ADDR
  $ SERVER_ADMIN="eric@localhost"; export SERVER_ADMIN
  $ SERVER_NAME="hg.omnifarious.org"; export SERVER_NAME
  $ SERVER_PORT="80"; export SERVER_PORT
  $ SERVER_PROTOCOL="HTTP/1.1"; export SERVER_PROTOCOL
  $ SERVER_SIGNATURE="<address>Apache/2.0.53 (Fedora) Server at hg.omnifarious.org Port 80</address>"; export SERVER_SIGNATURE
  $ SERVER_SOFTWARE="Apache/2.0.53 (Fedora)"; export SERVER_SOFTWARE

try hgweb request

  $ QUERY_STRING="cmd=changegroup&roots=0000000000000000000000000000000000000000"; export QUERY_STRING
  $ python hgweb.cgi >page1 2>&1
  $ python "$TESTDIR/md5sum.py" page1
  1f424bb22ec05c3c6bc866b6e67efe43  page1
