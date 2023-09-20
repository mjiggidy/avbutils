"""Utilites for working with bin locks (.lck files)"""

import pathlib

def get_lockfile_for_bin(bin_path:pathlib.Path) -> str|None:
	"""Return a Lockfile info if it exists"""

	lock_path = bin_path.with_suffix(".lck")
	if not lock_path.exists():
		return None
	
	with lock_path.open(encoding="utf-16le") as lock_handle:
		# TODO: Make a Lock Handle info struct thing
		return str(lock_handle.read())