  requesting all changes
  $ hg --cwd a export tip > tip.patch
  $ hg --cwd b import ../tip.patch
  applying ../tip.patch
message should be same
  $ hg --cwd b tip | grep 'second change'

committer should be same

  $ hg --cwd b tip | grep someone
  user:        someone
  requesting all changes
  $ hg --cwd a export tip > tip.patch
  $ hg --config ui.patch='python ../dummypatch.py' --cwd b import ../tip.patch
  applying ../tip.patch
  requesting all changes
  $ hg --cwd a diff -r0:1 > tip.patch
  $ hg --cwd b import ../tip.patch
  applying ../tip.patch
  requesting all changes
  $ hg --cwd a diff -r0:1 > tip.patch
  $ hg --cwd b import -mpatch ../tip.patch
  applying ../tip.patch
  requesting all changes
  $ hg --cwd a diff -r0:1 > tip.patch
  $ hg --cwd b import -mpatch -d '1 0' -u 'user@nowhere.net' ../tip.patch
  applying ../tip.patch
  requesting all changes
  $ hg --cwd a diff -r0:1 > tip.patch
  $ hg --cwd b import --no-commit ../tip.patch
  applying ../tip.patch
  requesting all changes
  $ hg --cwd a diff -r0:1 > tip.patch
  $ sed 's/1,1/foo/' < tip.patch > broken.patch
  requesting all changes
  $ hg --cwd a export tip > dir/tip.patch
  $ hg -R b import tip.patch
  applying tip.patch
  requesting all changes
  $ hg --cwd a export tip | hg --cwd b import -
  requesting all changes
  $ hg --cwd a export tip | hg --cwd b import -m 'override' -
  > msg.set_payload('email commit message\n' + open('tip.patch', 'rb').read())
  requesting all changes
  $ hg --cwd a diff -r0:1 > tip.patch
  $ python mkmsg.py > msg.patch
  requesting all changes
  requesting all changes
  requesting all changes
  requesting all changes
  $ hg --cwd a export tip > tip.patch
  $ python mkmsg.py | hg --cwd b import -
  > msg.set_payload('email patch\n\nnext line\n---\n' + open('tip.patch').read())
  requesting all changes
  $ hg --cwd a diff -r0:1 > tip.patch
  $ python mkmsg2.py | hg --cwd b import -
  rolling back to revision 1 (undo commit)
  requesting all changes
  $ sed -e 's/d1\/d2\///' < tmp > tip.patch
  $ hg import  ../../../tip.patch
  applying ../../../tip.patch

  $ hg --cwd b tip | grep 'subdir change'
  summary:     subdir change

  $ hg --cwd b tip | grep someoneelse
  $ hg export tip > tip.patch
  $ hg import --no-commit -v tip.patch
  applying tip.patch
  $ hg --config patch.eol=auto import --no-commit -v tip.patch
  applying tip.patch
  abort: ../outside/foo not under root