import collections.abc, re, pathlib, enum
import avb
from .reelinfo import ReelInfo
from timecode import Timecode

DEFAULT_HEAD_DURATION = Timecode("8:00")
DEFAULT_TAIL_DURATION = Timecode("4:00")

REEL_NUMBER_BIN_COLUMN_NAME = "Reel #"
"""The name of the Avid bin column from which to extract the Reel Number"""

def human_sort(text) -> list[str,int]:
	"""Mimics Avid's human-readable text sorting (ie 9 comes before 10)"""
	
	# Cast any numeric values to integers for `human_sort`
	_atoi = lambda text: int(text) if text.isdigit() else text

	return [_atoi(c) for c in re.split(r'(\d+)', text)]

def get_reel_number_from_sequence_attributes(attrs:avb.components.core.AVBPropertyData) -> str|None:
	"""Extract the 'Reel #' bin column data from a sequence's attributes.  Returns None if not set."""

	# Raise an exception if we weren't given property data.  Otherweise we'll treat failures as "that data just wasn't set"
	if not isinstance(attrs, avb.components.core.AVBPropertyData):
		raise ValueError(f"Expected AVBPropertyData, but got {type(attrs)} instead.")

	try:
		return attrs.get("_USER").get(REEL_NUMBER_BIN_COLUMN_NAME)
	except:
		return None

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

def get_reel_info(
	sequence:avb.trackgroups.Composition,
	head_duration:Timecode=DEFAULT_HEAD_DURATION,
	tail_duration:Timecode=DEFAULT_TAIL_DURATION) -> ReelInfo:
	"""Get the properties of a given sequence"""

	#print(sequence.length, sequence.edit_rate)
	#print(list(sequence.attributes.get("_USER").items()))
	
	return ReelInfo(
		sequence_name=sequence.name,
		date_modified=sequence.last_modified,
		reel_number=get_reel_number_from_sequence_attributes(sequence.attributes),
		duration_total=Timecode(sequence.length, rate=round(sequence.edit_rate)),
		duration_head_leader=head_duration,
		duration_tail_leader=tail_duration
	)

def get_sequences_from_bin(bin:avb.bin.Bin) -> collections.abc.Generator[avb.trackgroups.Composition,None,None]:
	"""Get all top-level sequences in a given Avid bin"""
	return (mob for mob in bin.toplevel() if isinstance(mob, avb.trackgroups.Composition))

def get_reel_info_from_path(
	bin_path:pathlib.Path,
	head_duration:Timecode=DEFAULT_HEAD_DURATION,
	tail_duration:Timecode=DEFAULT_TAIL_DURATION,
	sort_by:BinSorting=BinSorting.NAME)-> ReelInfo:
	"""Given a Avid bin's file path, parse the bin and get the latest sequence info"""

	#print("Using",str(tail_duration))

	with avb.open(bin_path) as bin_handle:

		# avb.file.AVBFile -> avb.bin.Bin
		bin_contents = bin_handle.content
		
		# Get all sequences in bin
		sequences = get_sequences_from_bin(bin_contents)

		# Sorting by sequence name with human sorting for version numbers
		try:
			latest_sequence = sorted(sequences, key=BinSorting.get_sort_lambda(sort_by), reverse=True)[0]
		except IndexError:
			raise Exception(f"No sequences found in bin")
		
		# Get info from latest reel
		try:
			sequence_info = get_reel_info(latest_sequence, head_duration=head_duration, tail_duration=tail_duration)
		except Exception as e:
			raise Exception(f"Error parsing sequence: {e}")
	
	return sequence_info

def get_lockfile_for_bin(bin_path:pathlib.Path) -> str|None:
	"""Return a Lockfile info if it exists"""

	lock_path = bin_path.with_suffix(".lck")
	if not lock_path.exists():
		return None
	
	with lock_path.open(encoding="utf-16le") as lock_handle:
		# TODO: Make a Lock Handle info struct thing
		return str(lock_handle.read())