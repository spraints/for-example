
copy: tests/test-username-newline
copyrev: 4144cb52a6932bbe1dd9b0039856f9b265ebcf0b

  $ hg init
  $ touch a

  $ unset HGUSER
  $ echo "[ui]" >> .hg/hgrc
  $ echo "username= foo" >> .hg/hgrc
  $ echo "          bar1" >> .hg/hgrc

  $ hg ci -Am m
  adding a
  abort: username 'foo\nbar1' contains a newline
  
  $ rm .hg/hgrc

  $ HGUSER=`(echo foo; echo bar2)` hg ci -Am m
  abort: username 'foo\nbar2' contains a newline
  
  $ hg ci -Am m -u "`(echo foo; echo bar3)`"
  transaction abort!
  rollback completed
  abort: username 'foo\nbar3' contains a newline!

  $ true

