import sys, pathlib
from avbutils import LockInfo

lock = LockInfo.from_lockfile(sys.argv[1])

lock.to_lockfile(pathlib.Path(sys.argv[1]).with_name("out.lck"))