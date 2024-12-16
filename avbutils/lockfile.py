"""Utilites for working with bin locks (.lck files)"""

import pathlib, dataclasses

@dataclasses.dataclass()
class LockInfo:
	"""Represents a bin lock file (.lck)"""

	name:str
	"""Name of the Avid the lock belongs to"""

	def __postinit__(self):
		if self.name is None:
			raise ValueError("Username for the lock must not be empty")
		
	@staticmethod
	def _read_utf16le(buffer) -> str:

		b_name = b""
		while True:
			b_chars = buffer.read(2)
			if b_chars == b"\x00\x00":
				break
			b_name += b_chars
		return b_name.decode("utf-16le")

	@classmethod
	def from_lockfile(cls, lock_path:str) -> "LockInfo":
		"Read from .lck lockfile"

		with open(lock_path, "rb") as lock_file:
			try:
				name = cls._read_utf16le(lock_file)
			except UnicodeDecodeError as e:
				raise ValueError(f"{lock_path}: This does not appear to be a valid lock file ({e})")		
		return cls(name=name)
	
	def to_lockfile(self, lock_path:str):
		"""Write to .lck lockfile"""

		with open(lock_path, "wb") as lock_file:
			lock_file.write(self.name[:255].ljust(255, '\x00').encode("utf-16le"))

# TODO: LockfileInfo class

def get_lockfile_for_bin(bin_path:str) -> str|None:
	"""Return a Lockfile info if it exists"""

	lock_path = pathlib.Path(bin_path).with_suffix(".lck")
	if not lock_path.exists():
		return None
	
	with lock_path.open(encoding="utf-16le") as lock_handle:
		# TODO: Make a Lock Handle info struct thing
		try:
			return str(lock_handle.read())
		except UnicodeDecodeError as e:
			return "Unknown"