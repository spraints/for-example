
copy: tests/test-bundle-r
copyrev: 7d013443ec7cbd2ea095497e0f8b469f5013c4e5

  $ hg init test
  $ cd test
  $ echo "0" >> afile
  $ hg add afile
  $ hg commit -m "0.0" -d "1000000 0"
  $ echo "1" >> afile
  $ hg commit -m "0.1" -d "1000000 0"
  $ echo "2" >> afile
  $ hg commit -m "0.2" -d "1000000 0"
  $ echo "3" >> afile
  $ hg commit -m "0.3" -d "1000000 0"
  $ hg update -C 0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo "1" >> afile
  $ hg commit -m "1.1" -d "1000000 0"
  created new head
  $ echo "2" >> afile
  $ hg commit -m "1.2" -d "1000000 0"
  $ echo "a line" > fred
  $ echo "3" >> afile
  $ hg add fred
  $ hg commit -m "1.3" -d "1000000 0"
  $ hg mv afile adifferentfile
  $ hg commit -m "1.3m" -d "1000000 0"
  $ hg update -C 3
  1 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg mv afile anotherfile
  $ hg commit -m "0.3m" -d "1000000 0"
  $ hg debugindex .hg/store/data/afile.i
     rev    offset  length   base linkrev nodeid       p1           p2
       0         0       3      0       0 362fef284ce2 000000000000 000000000000
       1         3       5      1       1 125144f7e028 362fef284ce2 000000000000
       2         8       7      2       2 4c982badb186 125144f7e028 000000000000
       3        15       9      3       3 19b1fc555737 4c982badb186 000000000000
  $ hg debugindex .hg/store/data/adifferentfile.i
     rev    offset  length   base linkrev nodeid       p1           p2
       0         0      75      0       7 2565f3199a74 000000000000 000000000000
  $ hg debugindex .hg/store/data/anotherfile.i
     rev    offset  length   base linkrev nodeid       p1           p2
       0         0      75      0       8 2565f3199a74 000000000000 000000000000
  $ hg debugindex .hg/store/data/fred.i
     rev    offset  length   base linkrev nodeid       p1           p2
       0         0       8      0       6 12ab3bcc5ea4 000000000000 000000000000
  $ hg debugindex .hg/store/00manifest.i
     rev    offset  length   base linkrev nodeid       p1           p2
       0         0      48      0       0 43eadb1d2d06 000000000000 000000000000
       1        48      48      1       1 8b89697eba2c 43eadb1d2d06 000000000000
       2        96      48      2       2 626a32663c2f 8b89697eba2c 000000000000
       3       144      48      3       3 f54c32f13478 626a32663c2f 000000000000
       4       192      58      3       6 de68e904d169 626a32663c2f 000000000000
       5       250      68      3       7 09bb521d218d de68e904d169 000000000000
       6       318      54      6       8 1fde233dfb0f f54c32f13478 000000000000
  $ hg verify
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  4 files, 9 changesets, 7 total revisions
  $ cd ..
  $ for i in 0 1 2 3 4 5 6 7 8; do
  >    mkdir test-"$i"
  >    hg --cwd test-"$i" init
  >    hg -R test bundle -r "$i" test-"$i".hg test-"$i"
  >    cd test-"$i"
  >    hg unbundle ../test-"$i".hg
  >    hg verify
  >    hg tip -q
  >    cd ..
  > done
  searching for changes
  1 changesets found
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  (run 'hg update' to get a working copy)
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  1 files, 1 changesets, 1 total revisions
  0:5649c9d34dd8
  searching for changes
  2 changesets found
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  (run 'hg update' to get a working copy)
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  1 files, 2 changesets, 2 total revisions
  1:10b2180f755b
  searching for changes
  3 changesets found
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  (run 'hg update' to get a working copy)
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  1 files, 3 changesets, 3 total revisions
  2:d62976ca1e50
  searching for changes
  4 changesets found
  adding changesets
  adding manifests
  adding file changes
  added 4 changesets with 4 changes to 1 files
  (run 'hg update' to get a working copy)
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  1 files, 4 changesets, 4 total revisions
  3:ac69c658229d
  searching for changes
  2 changesets found
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 1 files
  (run 'hg update' to get a working copy)
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  1 files, 2 changesets, 2 total revisions
  1:5f4f3ceb285e
  searching for changes
  3 changesets found
  adding changesets
  adding manifests
  adding file changes
  added 3 changesets with 3 changes to 1 files
  (run 'hg update' to get a working copy)
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  1 files, 3 changesets, 3 total revisions
  2:024e4e7df376
  searching for changes
  4 changesets found
  adding changesets
  adding manifests
  adding file changes
  added 4 changesets with 5 changes to 2 files
  (run 'hg update' to get a working copy)
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  2 files, 4 changesets, 5 total revisions
  3:1e3f6b843bd6
  searching for changes
  5 changesets found
  adding changesets
  adding manifests
  adding file changes
  added 5 changesets with 6 changes to 3 files
  (run 'hg update' to get a working copy)
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  3 files, 5 changesets, 6 total revisions
  4:27f57c869697
  searching for changes
  5 changesets found
  adding changesets
  adding manifests
  adding file changes
  added 5 changesets with 5 changes to 2 files
  (run 'hg update' to get a working copy)
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  2 files, 5 changesets, 5 total revisions
  4:088ff9d6e1e1
  $ cd test-8
  $ hg pull ../test-7
  pulling from ../test-7
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 4 changesets with 2 changes to 3 files (+1 heads)
  (run 'hg heads' to see heads, 'hg merge' to merge)
  $ hg verify
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  4 files, 9 changesets, 7 total revisions
  $ hg rollback
  rolling back to revision 4 (undo pull)
  $ cd ..

should fail

  $ hg -R test bundle --base 2 -r tip test-bundle-branch1.hg test-3
  abort: --base is incompatible with specifying a destination
  $ hg -R test bundle -r tip test-bundle-branch1.hg
  abort: repository default-push not found!

  $ hg -R test bundle --base 2 -r tip test-bundle-branch1.hg
  2 changesets found
  $ hg -R test bundle --base 2 -r 7 test-bundle-branch2.hg
  4 changesets found
  $ hg -R test bundle --base 2 test-bundle-all.hg
  6 changesets found
  $ hg -R test bundle --base 3 -r tip test-bundle-should-fail.hg
  1 changesets found

empty bundle

  $ hg -R test bundle --base 7 --base 8 test-bundle-empty.hg
  no changes found

issue76 msg2163

  $ hg -R test bundle --base 3 -r 3 -r 3 test-bundle-cset-3.hg
  1 changesets found

issue1910

  $ hg -R test bundle --base 7 test-bundle-cset-7.hg
  4 changesets found

  $ hg clone test-2 test-9
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd test-9

revision 2

  $ hg tip -q
  2:d62976ca1e50
  $ hg unbundle ../test-bundle-should-fail.hg
  adding changesets
  transaction abort!
  rollback completed
  abort: 00changelog.i@ac69c658229d: unknown parent!

revision 2

  $ hg tip -q
  2:d62976ca1e50
  $ hg unbundle ../test-bundle-all.hg
  adding changesets
  adding manifests
  adding file changes
  added 6 changesets with 4 changes to 4 files (+1 heads)
  (run 'hg heads' to see heads, 'hg merge' to merge)

revision 8

  $ hg tip -q
  8:088ff9d6e1e1
  $ hg verify
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  4 files, 9 changesets, 7 total revisions
  $ hg rollback
  rolling back to revision 2 (undo unbundle)

revision 2

  $ hg tip -q
  2:d62976ca1e50
  $ hg unbundle ../test-bundle-branch1.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  (run 'hg update' to get a working copy)

revision 4

  $ hg tip -q
  4:088ff9d6e1e1
  $ hg verify
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  2 files, 5 changesets, 5 total revisions
  $ hg rollback
  rolling back to revision 2 (undo unbundle)
  $ hg unbundle ../test-bundle-branch2.hg
  adding changesets
  adding manifests
  adding file changes
  added 4 changesets with 3 changes to 3 files (+1 heads)
  (run 'hg heads' to see heads, 'hg merge' to merge)

revision 6

  $ hg tip -q
  6:27f57c869697
  $ hg verify
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  3 files, 7 changesets, 6 total revisions
  $ hg rollback
  rolling back to revision 2 (undo unbundle)
  $ hg unbundle ../test-bundle-cset-7.hg
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  (run 'hg update' to get a working copy)

revision 4

  $ hg tip -q
  4:088ff9d6e1e1
  $ hg verify
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  2 files, 5 changesets, 5 total revisions

  $ cd ../test
  $ hg merge 7
  warning: detected divergent renames of afile to:
   anotherfile
   adifferentfile
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m merge -d "1000000 0"
  $ cd ..
  $ hg -R test bundle --base 2 test-bundle-head.hg
  7 changesets found
  $ hg clone test-2 test-10
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd test-10
  $ hg unbundle ../test-bundle-head.hg
  adding changesets
  adding manifests
  adding file changes
  added 7 changesets with 4 changes to 4 files
  (run 'hg update' to get a working copy)

revision 9

  $ hg tip -q
  9:e3061ea42e4c
  $ hg verify
  checking changesets
  checking manifests
  crosschecking files in changesets and manifests
  checking files
  4 files, 10 changesets, 7 total revisions
