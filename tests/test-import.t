generate patches for the test

  $ hg --cwd a export tip > exported-tip.patch
  $ hg --cwd a diff -r0:1 > diffed-tip.patch


  $ hg --cwd b import ../exported-tip.patch
  applying ../exported-tip.patch
message and committer should be same
  $ hg --cwd b tip
  changeset:   1:1d4bd90af0e4
  tag:         tip
  date:        Thu Jan 01 00:00:01 1970 +0000
  summary:     second change
  
  $ hg --config ui.patch='python ../dummypatch.py' --cwd b import ../exported-tip.patch
  applying ../exported-tip.patch
  $ hg --cwd b import ../diffed-tip.patch
  applying ../diffed-tip.patch
  $ hg --cwd b import -mpatch ../diffed-tip.patch
  applying ../diffed-tip.patch
  $ hg --cwd b import -mpatch -d '1 0' -u 'user@nowhere.net' ../diffed-tip.patch
  applying ../diffed-tip.patch
  $ hg --cwd b import --no-commit ../diffed-tip.patch
  applying ../diffed-tip.patch
  $ sed 's/1,1/foo/' < diffed-tip.patch > broken.patch
  $ hg -R b import ../exported-tip.patch
  applying ../exported-tip.patch
  $ hg --cwd b import - < exported-tip.patch
  $ hg --cwd b import -m 'override' - < exported-tip.patch
  > patch = open(sys.argv[1], 'rb').read()
  > msg.set_payload('email commit message\n' + patch)
  $ python mkmsg.py diffed-tip.patch > msg.patch
  $ python mkmsg.py exported-tip.patch | hg --cwd b import -
  > patch = open(sys.argv[1], 'rb').read()
  > msg.set_payload('email patch\n\nnext line\n---\n' + patch)
  $ python mkmsg2.py diffed-tip.patch | hg --cwd b import -
  repository tip rolled back to revision 1 (undo commit)
  working directory now based on revision 1
  $ sed -e 's/d1\/d2\///' < tmp > subdir-tip.patch
  $ hg import  ../../../subdir-tip.patch
  applying ../../../subdir-tip.patch
  $ hg --cwd b tip
  changeset:   1:3577f5aea227
  tag:         tip
  date:        Thu Jan 01 00:00:01 1970 +0000
  summary:     subdir change
  
  $ hg export tip > fuzzy-tip.patch
  $ hg import --no-commit -v fuzzy-tip.patch
  applying fuzzy-tip.patch

import with --no-commit should have written .hg/last-message.txt

  $ cat .hg/last-message.txt
  change (no-eol)


  $ hg --config patch.eol=auto import --no-commit -v fuzzy-tip.patch
  applying fuzzy-tip.patch
  abort: path contains illegal component: ../outside/foo