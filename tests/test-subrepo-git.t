  $ "$TESTDIR/hghave" git || exit 80

make git commits repeatable

  $ GIT_AUTHOR_NAME='test'; export GIT_AUTHOR_NAME
  $ GIT_AUTHOR_EMAIL='test@example.org'; export GIT_AUTHOR_EMAIL
  $ GIT_AUTHOR_DATE='1234567891 +0000'; export GIT_AUTHOR_DATE
  $ GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"; export GIT_COMMITTER_NAME
  $ GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"; export GIT_COMMITTER_EMAIL
  $ GIT_COMMITTER_DATE="$GIT_AUTHOR_DATE"; export GIT_COMMITTER_DATE

root hg repo

  $ hg init t
  $ cd t
  $ echo a > a
  $ hg add a
  $ hg commit -m a
  $ cd ..

new external git repo

  $ mkdir gitroot
  $ cd gitroot
  $ git init -q
  $ echo g > g
  $ git add g
  $ git commit -q -m g

add subrepo clone

  $ cd ../t
  $ echo 's = [git]../gitroot' > .hgsub
  $ git clone -q ../gitroot s
  $ hg add .hgsub
  $ hg commit -m 'new git subrepo'
  committing subrepository $TESTTMP/t/s
  $ hg debugsub
  path s
   source   ../gitroot
   revision da5f5b1d8ffcf62fb8327bcd3c89a4367a6018e7

record a new commit from upstream from a different branch

  $ cd ../gitroot
  $ git checkout -q -b testing
  $ echo gg >> g
  $ git commit -q -a -m gg

  $ cd ../t/s
  $ git pull -q >/dev/null 2>/dev/null
  $ git checkout -q -b testing origin/testing >/dev/null

  $ cd ..
  $ hg commit -m 'update git subrepo'
  committing subrepository $TESTTMP/t/s
  $ hg debugsub
  path s
   source   ../gitroot
   revision 126f2a14290cd5ce061fdedc430170e8d39e1c5a

clone root

  $ hg clone . ../tc
  updating to branch default
  cloning subrepo s
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd ../tc
  $ hg debugsub
  path s
   source   ../gitroot
   revision 126f2a14290cd5ce061fdedc430170e8d39e1c5a

update to previous substate

  $ hg update 1 2>/dev/null
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cat s/g
  g
  $ hg debugsub
  path s
   source   ../gitroot
   revision da5f5b1d8ffcf62fb8327bcd3c89a4367a6018e7

make $GITROOT pushable, by replacing it with a clone with nothing checked out

  $ cd ..
  $ git clone gitroot gitrootbare --bare -q
  $ rm -rf gitroot
  $ mv gitrootbare gitroot

clone root, make local change

  $ cd t
  $ hg clone . ../ta
  updating to branch default
  cloning subrepo s
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ cd ../ta
  $ echo ggg >> s/g
  $ hg commit -m ggg
  committing subrepository $TESTTMP/ta/s
  $ hg debugsub
  path s
   source   ../gitroot
   revision 79695940086840c99328513acbe35f90fcd55e57

clone root separately, make different local change

  $ cd ../t
  $ hg clone . ../tb
  updating to branch default
  cloning subrepo s
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ cd ../tb/s
  $ echo f > f
  $ git add f
  $ cd ..

  $ hg commit -m f
  committing subrepository $TESTTMP/tb/s
  $ hg debugsub
  path s
   source   ../gitroot
   revision aa84837ccfbdfedcdcdeeedc309d73e6eb069edc

user b push changes

  $ hg push 2>/dev/null
  pushing to $TESTTMP/t
  pushing branch testing of subrepo s
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

user a pulls, merges, commits

  $ cd ../ta
  $ hg pull
  pulling from $TESTTMP/t
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  (run 'hg heads' to see heads, 'hg merge' to merge)
  $ hg merge 2>/dev/null
  pulling subrepo s
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ cat s/f
  f
  $ cat s/g
  g
  gg
  ggg
  $ hg commit -m 'merge'
  committing subrepository $TESTTMP/ta/s
  $ hg debugsub
  path s
   source   ../gitroot
   revision f47b465e1bce645dbf37232a00574aa1546ca8d3
  $ hg push 2>/dev/null
  pushing to $TESTTMP/t
  pushing branch testing of subrepo s
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files

make upstream git changes

  $ cd ..
  $ git clone -q gitroot gitclone
  $ cd gitclone
  $ echo ff >> f
  $ git commit -q -a -m ff
  $ echo fff >> f
  $ git commit -q -a -m fff
  $ git push origin testing 2>/dev/null

make and push changes to hg without updating the subrepo

  $ cd ../t
  $ hg clone . ../td
  updating to branch default
  cloning subrepo s
  checking out detached HEAD in subrepo s
  check out a git branch if you intend to make changes
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd ../td
  $ echo aa >> a
  $ hg commit -m aa
  $ hg push
  pushing to $TESTTMP/t
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

sync to upstream git, distribute changes

  $ cd ../ta
  $ hg pull -u -q
  $ cd s
  $ git pull -q >/dev/null 2>/dev/null
  $ cd ..
  $ hg commit -m 'git upstream sync'
  committing subrepository $TESTTMP/ta/s
  $ hg debugsub
  path s
   source   ../gitroot
   revision 32a343883b74769118bb1d3b4b1fbf9156f4dddc
  $ hg push -q

  $ cd ../tb
  $ hg pull -q
  $ hg update 2>/dev/null
  pulling subrepo s
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg debugsub
  path s
   source   ../gitroot
   revision 32a343883b74769118bb1d3b4b1fbf9156f4dddc

update to a revision without the subrepo, keeping the local git repository

  $ cd ../t
  $ hg up 0
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ ls -a s
  .
  ..
  .git

  $ hg up 2
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ ls -a s
  .
  ..
  .git
  g

archive subrepos

  $ cd ../tc
  $ hg pull -q
  $ hg archive --subrepos -r 5 ../archive 2>/dev/null
  pulling subrepo s
  $ cd ../archive
  $ cat s/f
  f
  $ cat s/g
  g
  gg
  ggg
