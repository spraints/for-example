  $ hg init

no bookmarks

  $ hg bookmarks
  no bookmarks set

bookmark rev -1

  $ hg bookmark X

list bookmarks

  $ hg bookmarks
   * X                         -1:000000000000

list bookmarks with color

  $ hg --config extensions.color= --config color.mode=ansi \
  >    bookmarks --color=always
  \x1b[0;32m * X                         -1:000000000000\x1b[0m (esc)

  $ echo a > a
  $ hg add a
  $ hg commit -m 0

bookmark X moved to rev 0

  $ hg bookmarks
   * X                         0:f7b1eb17ad24

look up bookmark

  $ hg log -r X
  changeset:   0:f7b1eb17ad24
  bookmark:    X
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     0
  

second bookmark for rev 0

  $ hg bookmark X2

bookmark rev -1 again

  $ hg bookmark -r null Y

list bookmarks

  $ hg bookmarks
     X                         0:f7b1eb17ad24
   * X2                        0:f7b1eb17ad24
     Y                         -1:000000000000

  $ echo b > b
  $ hg add b
  $ hg commit -m 1

bookmarks revset

  $ hg log -r 'bookmark()'
  changeset:   0:f7b1eb17ad24
  bookmark:    X
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     0
  
  changeset:   1:925d80f479bb
  bookmark:    X2
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     1
  
  $ hg log -r 'bookmark(Y)'
  $ hg log -r 'bookmark(X2)'
  changeset:   1:925d80f479bb
  bookmark:    X2
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     1
  
  $ hg log -r 'bookmark("re:X")'
  changeset:   0:f7b1eb17ad24
  bookmark:    X
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     0
  
  changeset:   1:925d80f479bb
  bookmark:    X2
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     1
  
  $ hg log -r 'bookmark(unknown)'
  abort: bookmark 'unknown' does not exist
  [255]

  $ hg help revsets | grep 'bookmark('
      "bookmark([name])"

bookmarks X and X2 moved to rev 1, Y at rev -1

  $ hg bookmarks
     X                         0:f7b1eb17ad24
   * X2                        1:925d80f479bb
     Y                         -1:000000000000

bookmark rev 0 again

  $ hg bookmark -r 0 Z

  $ hg update X
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo c > c
  $ hg add c
  $ hg commit -m 2
  created new head

bookmarks X moved to rev 2, Y at rev -1, Z at rev 0

  $ hg bookmarks
   * X                         2:db815d6d32e6
     X2                        1:925d80f479bb
     Y                         -1:000000000000
     Z                         0:f7b1eb17ad24

rename nonexistent bookmark

  $ hg bookmark -m A B
  abort: bookmark 'A' does not exist
  [255]

rename to existent bookmark

  $ hg bookmark -m X Y
  abort: bookmark 'Y' already exists (use -f to force)
  [255]

force rename to existent bookmark

  $ hg bookmark -f -m X Y

list bookmarks

  $ hg bookmark
     X2                        1:925d80f479bb
   * Y                         2:db815d6d32e6
     Z                         0:f7b1eb17ad24

rename without new name

  $ hg bookmark -m Y
  abort: new bookmark name required
  [255]

delete without name

  $ hg bookmark -d
  abort: bookmark name required
  [255]

delete nonexistent bookmark

  $ hg bookmark -d A
  abort: bookmark 'A' does not exist
  [255]

bookmark name with spaces should be stripped

  $ hg bookmark ' x  y '

list bookmarks

  $ hg bookmarks
     X2                        1:925d80f479bb
     Y                         2:db815d6d32e6
     Z                         0:f7b1eb17ad24
   * x  y                      2:db815d6d32e6

look up stripped bookmark name

  $ hg log -r '"x  y"'
  changeset:   2:db815d6d32e6
  bookmark:    Y
  bookmark:    x  y
  tag:         tip
  parent:      0:f7b1eb17ad24
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     2
  

reject bookmark name with newline

  $ hg bookmark '
  > '
  abort: bookmark name cannot contain newlines
  [255]

bookmark with existing name

  $ hg bookmark Z
  abort: bookmark 'Z' already exists (use -f to force)
  [255]

force bookmark with existing name

  $ hg bookmark -f Z

list bookmarks

  $ hg bookmark
     X2                        1:925d80f479bb
     Y                         2:db815d6d32e6
   * Z                         2:db815d6d32e6
     x  y                      2:db815d6d32e6

revision but no bookmark name

  $ hg bookmark -r .
  abort: bookmark name required
  [255]

bookmark name with whitespace only

  $ hg bookmark ' '
  abort: bookmark names cannot consist entirely of whitespace
  [255]

invalid bookmark

  $ hg bookmark 'foo:bar'
  abort: bookmark 'foo:bar' contains illegal character
  [255]

the bookmark extension should be ignored now that it is part of core

  $ echo "[extensions]" >> $HGRCPATH
  $ echo "bookmarks=" >> $HGRCPATH
  $ hg bookmarks
     X2                        1:925d80f479bb
     Y                         2:db815d6d32e6
   * Z                         2:db815d6d32e6
     x  y                      2:db815d6d32e6

test summary

  $ hg summary
  parent: 2:db815d6d32e6 tip
   2
  branch: default
  bookmarks: *Z Y x  y
  commit: (clean)
  update: 1 new changesets, 2 branch heads (merge)

test id

  $ hg id
  db815d6d32e6 tip Y/Z/x  y

test rollback

  $ echo foo > f1
  $ hg ci -Amr
  adding f1
  $ hg bookmark -f Y -r 1
  $ hg bookmark -f Z -r 1
  $ hg rollback
  repository tip rolled back to revision 2 (undo commit)
  working directory now based on revision 2
  $ hg bookmarks
     X2                        1:925d80f479bb
     Y                         2:db815d6d32e6
   * Z                         2:db815d6d32e6
     x  y                      2:db815d6d32e6

test clone

  $ hg bookmark -r 2 -i @
  $ hg bookmark -r 2 -i a@
  $ hg bookmarks
     @                         2:db815d6d32e6
     X2                        1:925d80f479bb
     Y                         2:db815d6d32e6
   * Z                         2:db815d6d32e6
     a@                        2:db815d6d32e6
     x  y                      2:db815d6d32e6
  $ hg clone . cloned-bookmarks
  updating to branch default
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg -R cloned-bookmarks bookmarks
     @                         2:db815d6d32e6
     X2                        1:925d80f479bb
     Y                         2:db815d6d32e6
     Z                         2:db815d6d32e6
     a@                        2:db815d6d32e6
     x  y                      2:db815d6d32e6

test clone with pull protocol

  $ hg clone --pull . cloned-bookmarks-pull
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 3 files (+1 heads)
  updating to branch default
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg -R cloned-bookmarks-pull bookmarks
     @                         2:db815d6d32e6
     X2                        1:925d80f479bb
     Y                         2:db815d6d32e6
     Z                         2:db815d6d32e6
     a@                        2:db815d6d32e6
     x  y                      2:db815d6d32e6

  $ hg bookmark -d @
  $ hg bookmark -d a@

test clone with a specific revision

  $ hg clone -r 925d80 . cloned-bookmarks-rev
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  updating to branch default
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg -R cloned-bookmarks-rev bookmarks
     X2                        1:925d80f479bb

create bundle with two heads

  $ hg clone . tobundle
  updating to branch default
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo x > tobundle/x
  $ hg -R tobundle add tobundle/x
  $ hg -R tobundle commit -m'x'
  $ hg -R tobundle update -r -2
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo y > tobundle/y
  $ hg -R tobundle branch test
  marked working directory as branch test
  (branches are permanent and global, did you want a bookmark?)
  $ hg -R tobundle add tobundle/y
  $ hg -R tobundle commit -m'y'
  $ hg -R tobundle bundle tobundle.hg
  searching for changes
  2 changesets found
  $ hg unbundle tobundle.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files (+1 heads)
  (run 'hg heads' to see heads, 'hg merge' to merge)
  $ hg update
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg bookmarks
     X2                        1:925d80f479bb
     Y                         2:db815d6d32e6
   * Z                         3:125c9a1d6df6
     x  y                      2:db815d6d32e6

test wrongly formated bookmark

  $ echo '' >> .hg/bookmarks
  $ hg bookmarks
     X2                        1:925d80f479bb
     Y                         2:db815d6d32e6
   * Z                         3:125c9a1d6df6
     x  y                      2:db815d6d32e6
  $ echo "Ican'thasformatedlines" >> .hg/bookmarks
  $ hg bookmarks
  malformed line in .hg/bookmarks: "Ican'thasformatedlines"
     X2                        1:925d80f479bb
     Y                         2:db815d6d32e6
   * Z                         3:125c9a1d6df6
     x  y                      2:db815d6d32e6

test missing revisions

  $ echo "925d80f479bc z" > .hg/bookmarks
  $ hg book
  no bookmarks set

test stripping a non-checked-out but bookmarked revision

  $ hg --config extensions.graphlog= log --graph
  o  changeset:   4:9ba5f110a0b3
  |  branch:      test
  |  tag:         tip
  |  parent:      2:db815d6d32e6
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     y
  |
  | @  changeset:   3:125c9a1d6df6
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     x
  |
  o  changeset:   2:db815d6d32e6
  |  parent:      0:f7b1eb17ad24
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     2
  |
  | o  changeset:   1:925d80f479bb
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     1
  |
  o  changeset:   0:f7b1eb17ad24
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     0
  
  $ hg book should-end-on-two
  $ hg co --clean 4
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg book four
  $ hg --config extensions.mq= strip 3
  saved backup bundle to * (glob)
should-end-on-two should end up pointing to revision 2, as that's the
tipmost surviving ancestor of the stripped revision.
  $ hg --config extensions.graphlog= log --graph
  @  changeset:   3:9ba5f110a0b3
  |  branch:      test
  |  bookmark:    four
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     y
  |
  o  changeset:   2:db815d6d32e6
  |  bookmark:    should-end-on-two
  |  parent:      0:f7b1eb17ad24
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     2
  |
  | o  changeset:   1:925d80f479bb
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     1
  |
  o  changeset:   0:f7b1eb17ad24
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     0
  
