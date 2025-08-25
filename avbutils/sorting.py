"""Mechanisms for mimicking Media Composer's bin sorting"""

import enum, re

class BinSorting(enum.IntEnum):
	"""Options for sorting toplevel bin items"""

	DATE_CREATED = enum.auto()
	"""Sort bin items by creation date"""
	
	DATE_MODIFIED = enum.auto()
	"""Sort bin items by date modified"""

	NAME = enum.auto()
	"""Sort bin items by the Name column"""

	# NOTE: Maybe do this whole thing differently?
	# But be to be sensitive to pickling for multiprocessing

	@classmethod
	def get_sort_lambda(cls, method:"BinSorting"):
		"""Retrieve the actual sort lambda"""
		
		if method == cls.DATE_CREATED:
			return lambda x: x.creation_time
		elif method == cls.DATE_MODIFIED:
			return lambda x: x.last_modified
		elif method == cls.NAME:
			return lambda x: x.name
		else:
			return ValueError(f"Invalid sort method: {method}")
		
def human_sort(text) -> list[str,int]:
	"""Prepares string to mimics Avid's human-readable text sorting (ie 9 comes before 10)"""
	
	# Cast any numeric values to integers for `human_sort`
	_atoi = lambda text: int(text) if text.isdigit() else text.lower()

	return [_atoi(c) for c in re.split(r'(\d+)', text)]