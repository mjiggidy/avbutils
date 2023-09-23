
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

	edit_rate = composition.edit_rate

	# TODO: I'm not yet confident index=1 will always be a Timecode component, or one matching the edit rate
	# TODO: So... let's see if we run into any problems
	
	try:
		timecode_track = next(get_tracks_from_composition(composition, type=TrackTypes.TIMECODE, index=1))
	except StopIteration:
		raise ValueError(f"Composition has no timecode tracks")
	
	timecode_component = timecode_track.component

	if not isinstance(timecode_component, avb.components.Timecode):
		raise ValueError(f"Timecode track 1 is not a Timecode component: {timecode_component}")

	if not timecode_component.edit_rate == composition.edit_rate:
		raise ValueError(f"Timecode track 1 does not match the composition's edit rate: TC {timecode_component.edit_rate} vs Composition {timecode_component.edit_rate}")
	
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