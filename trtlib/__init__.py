import collections.abc, re, pathlib
import avb
from .reelinfo import ReelInfo
from timecode import Timecode

DEFAULT_HEAD_DURATION = Timecode("8:00")
DEFAULT_TAIL_DURATION = Timecode("3:23")

def _atoi(text:str) -> int|str:
	"""Cast any numeric values to integers for `human_sort`"""
	return int(text) if text.isdigit() else text

def human_sort(text) -> list[str,int]:
	"""Mimics Avid's human-readable text sorting (ie 9 comes before 10)"""
	return [_atoi(c) for c in re.split(r'(\d+)', text)]

def get_sequence_info(
	sequence:avb.trackgroups.Composition,
	head_duration:Timecode=DEFAULT_HEAD_DURATION,
	tail_duration:Timecode=DEFAULT_TAIL_DURATION) -> ReelInfo:
	"""Get the properties of a given sequence"""

	#print(sequence.length, sequence.edit_rate)
	
	return ReelInfo(
		sequence_name=sequence.name,
		date_modified=sequence.creation_time,
		duration_total=Timecode(sequence.length, rate=round(sequence.edit_rate)),
		duration_head_leader=head_duration,
		duration_tail_leader=tail_duration
	)

def get_sequences_from_bin(bin:avb.bin.Bin) -> collections.abc.Generator[avb.trackgroups.Composition,None,None]:
	"""Get all top-level sequences in a given Avid bin"""
	return (mob for mob in bin.toplevel() if isinstance(mob, avb.trackgroups.Composition))

def get_reelinfo_from_path(
	bin_path:pathlib.Path,
	head_duration:Timecode=DEFAULT_HEAD_DURATION,
	tail_duration:Timecode=DEFAULT_TAIL_DURATION) -> ReelInfo:
	"""Given a Avid bin's file path, parse the bin and get the latest sequence info"""

	#print("Using",str(tail_duration))

	with avb.open(bin_path) as bin_handle:

		# avb.file.AVBFile -> avb.bin.Bin
		bin_contents = bin_handle.content
		
		# Get all sequences in bin
		sequences = get_sequences_from_bin(bin_contents)

		# Sorting by sequence name with human sorting for version numbers
		try:
			latest_sequence = sorted(sequences, key=lambda x:human_sort(x.name), reverse=True)[0]
		except IndexError:
			raise Exception(f"No sequences found in bin")
		
		# Get info from latest reel
		try:
			sequence_info = get_sequence_info(latest_sequence, head_duration=head_duration, tail_duration=tail_duration)
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