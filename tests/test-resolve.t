
copy: tests/test-resolve
copyrev: 09ba722b4f14cef5902abd6cd590970811eb9ac1

test that a commit clears the merge state.

  $ hg init repo
  $ cd repo

  $ echo foo > file
  $ hg commit -Am 'add file'
  adding file

  $ echo bar >> file
  $ hg commit -Am 'append bar'


create a second head

  $ hg up -C 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo baz >> file
  $ hg commit -Am 'append baz'
  created new head

failing merge

  $ HGMERGE=internal:fail hg merge
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  use 'hg resolve' to retry unresolved file merges or 'hg update -C' to abandon

  $ echo resolved > file
  $ hg resolve -m file
  $ hg commit -m 'resolved'

resolve -l, should be empty

  $ hg resolve -l

test crashed merge with empty mergestate

  $ mkdir .hg/merge
  $ touch .hg/merge/state

resolve -l, should be empty

  $ hg resolve -l
