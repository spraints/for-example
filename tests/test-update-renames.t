
copy: tests/test-update-renames
copyrev: 6eb26a8d240ee8130bdc7471d9d71f455095f88b

# test update logic when there are renames

# update with local changes across a file rename

  $ hg init

  $ echo a > a
  $ hg add a
  $ hg ci -m a

  $ hg mv a b
  $ hg ci -m rename

  $ echo b > b
  $ hg ci -m change

  $ hg up -q 0

  $ echo c > a

  $ hg up
  merging a and b to b
  warning: conflicts during merge.
  merging b failed!
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  use 'hg resolve' to retry unresolved file merges

  $ cd ..

