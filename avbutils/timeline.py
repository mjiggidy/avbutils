
"""Utilities for working with timelines ("Sequences" in Media Composer parlance)"""

import collections.abc, enum
import avb
from timecode import Timecode, TimecodeRange

class TrackTypes(enum.Enum):
	"""Types of tracks supported in a trackgroup"""

	PICTURE  = "picture"
	SOUND    = "sound"
	TIMECODE = "timecode"
	EDGECODE = "edgecode"
	DATA_ESSENCE = "DataEssenceTrack" # TODO: Investigate

	@classmethod
	def from_track(cls, track:avb.trackgroups.Track) -> "TrackTypes":
		return cls(track.media_kind)

def format_track_label(track:avb.trackgroups.Track) -> str:
	# TODO: Integrate this into that there `TrackTypes` enum maybe or something

	if track.media_kind == "picture":
		return "V" + str(track.index)
	elif track.media_kind == "sound":
		return "A" + str(track.index)
	elif track.media_kind == "timecode":
		return "TC" + str(track.index)
	elif track.media_kind == "edgecode":
		return "EC" + str(track.index)
	else:
		return track.media_kind + (str(track.index) if "index" in track.propertydefs else "")
	
def format_track_labels(tracks:list[avb.trackgroups.Track]) -> str:
	"""Format mutliple track types for bin display (eg V1 A1-3,5-7 TC1-8 EC1)"""

	def _group_ranges(ranges:list[int]) -> list:
		"""Helper func: Group ranges together"""

		index_groups = []
		for idx in sorted(ranges):
			if index_groups and index_groups[-1][-1] == idx -1:
				index_groups[-1].append(idx)
			else:
				index_groups.append([idx])
		
		return index_groups
	
	# Collect all tracks
	
	track_groups = {}
	
	for track in tracks:
		if track.media_kind not in track_groups:
			track_groups[track.media_kind] = []
		track_groups[track.media_kind].append(track.index)
	
	# Combine into groups
	
	formatted_labels = []
	
	if "picture" in track_groups:
		ranges = _group_ranges(track_groups["picture"])
		formatted_labels.append("V"+','.join([
			f"{r[0]}-{r[-1]}" if len(r) > 1 else str(r[0]) for r in ranges
		]))
	if "sound" in track_groups:
		ranges = _group_ranges(track_groups["sound"])
		formatted_labels.append("A"+','.join([
			f"{r[0]}-{r[-1]}" if len(r) > 1 else str(r[0]) for r in ranges
		]))
	if "DataEssenceTrack" in track_groups:
		ranges = _group_ranges(track_groups["DataEssenceTrack"])
		formatted_labels.append("D"+','.join([
			f"{r[0]}-{r[-1]}" if len(r) > 1 else str(r[0]) for r in ranges
		]))
	if "timecode" in track_groups:
		ranges = _group_ranges(track_groups["timecode"])
		formatted_labels.append("TC"+','.join([
			f"{r[0]}-{r[-1]}" if len(r) > 1 else str(r[0]) for r in ranges
		]))
	if "edgecode" in track_groups:
		ranges = _group_ranges(track_groups["edgecode"])
		formatted_labels.append("EC"+','.join([
			f"{r[0]}-{r[-1]}" if len(r) > 1 else str(r[0]) for r in ranges
		]))
	
	return " ".join(formatted_labels)


def get_timelines_from_bin(bin:avb.bin.Bin) -> collections.abc.Generator[avb.trackgroups.Composition,None,None]:
	"""Get all top-level timelines ("Sequences" in Media Composer) in a given Avid bin"""
	return (mob for mob in bin.toplevel() if isinstance(mob, avb.trackgroups.Composition))

def get_tracks_from_composition(composition:avb.trackgroups.Composition, type:TrackTypes|None=None, index:int|None=None) -> collections.abc.Generator[avb.trackgroups.Track]:
	"""Filter tracks based on their properties"""

	for track in composition.tracks:
		if type and track.media_kind != type.value:
			continue
		elif index and track.index != index:
			continue
		yield track

def get_timecode_range_for_composition(composition:avb.trackgroups.Composition) -> TimecodeRange:
	"""Get a `TimecodeRange` representing the timecode extents of this composition"""

	# TODO: I'm not yet confident index=1 will always be a Timecode component, or one matching the edit rate
	# TODO: So... let's see if we run into any problems
	
	try:
		timecode_track = next(get_tracks_from_composition(composition, type=TrackTypes.TIMECODE, index=1))
	except StopIteration:
		raise ValueError(f"Composition has no timecode tracks")
	
	timecode_component = timecode_track.component

	# I think maybe SourceMobs store their timecode in a sequence like this?
	if isinstance(timecode_component, avb.components.Sequence):
		timecode_component = timecode_component.components[1]

	if not isinstance(timecode_component, avb.components.Timecode):
		raise ValueError(f"Timecode track 1 is not a Timecode component: {timecode_component}")

	if not timecode_component.edit_rate == composition.edit_rate:
		raise ValueError(f"Timecode track 1 does not match the composition's edit rate: TC {timecode_component.edit_rate} fps vs Composition {composition.edit_rate} fps")
	
	return TimecodeRange(
		start=Timecode(timecode_component.start, rate=round(timecode_component.edit_rate)),
		duration=timecode_component.length
	)

	

def get_video_track_from_composition(composition:avb.trackgroups.Composition, media_kind:str="picture", track_index:int=1) -> avb.components.Sequence:
	"""Get V1 by default"""

	raise DeprecationWarning("NAH USE THE OTHER")

	for track in composition.tracks:
		if track.index == track_index and track.media_kind == media_kind:
			return track.component
	
	raise IndexError(f"No V{track_index} found in sequence")