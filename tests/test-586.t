
copy: tests/test-586
copyrev: 65cf82084ead2e531f85dd801eb2bc5a5f8f39ca

a test for issue586

  $ hg init a
  $ cd a
  $ echo a > a
  $ hg ci -Ama
  adding a

  $ hg init ../b
  $ cd ../b
  $ echo b > b
  $ hg ci -Amb
  adding b

  $ hg pull -f ../a
  pulling from ../a
  searching for changes
  warning: repository is unrelated
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  (run 'hg heads' to see heads, 'hg merge' to merge)
  $ hg merge
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg rm -f a
  $ hg ci -Amc

  $ hg st -A
  C b
  $ cd ..

a test for issue 1433, related to issue586

create test repos

  $ hg init repoa
  $ touch repoa/a
  $ hg -R repoa ci -Am adda
  adding a

  $ hg init repob
  $ touch repob/b
  $ hg -R repob ci -Am addb
  adding b

  $ hg init repoc
  $ cd repoc
  $ hg pull ../repoa
  pulling from ../repoa
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  (run 'hg update' to get a working copy)
  $ hg update
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ mkdir tst
  $ hg mv * tst
  $ hg ci -m "import a in tst"
  $ hg pull -f ../repob
  pulling from ../repob
  searching for changes
  warning: repository is unrelated
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  (run 'hg heads' to see heads, 'hg merge' to merge)

merge both repos

  $ hg merge
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ mkdir src

move b content

  $ hg mv b src
  $ hg ci -m "import b in src"
  $ hg manifest
  src/b
  tst/a

