
copy: tests/test-remove-new
copyrev: 4f8cc62bd20787a28a8e0a1d030bddfbe66c951c

test that 'hg commit' does not crash if the user removes a newly added file

  $ hg init
  $ echo This is file a1 > a
  $ hg add a
  $ hg commit -m "commit #0" -d "1000000 0"
  $ touch b
  $ hg add b
  $ rm b
  $ hg commit -A -m"comment #1" -d "1000000 0"
  removing b
  nothing changed
  $ exit 0
