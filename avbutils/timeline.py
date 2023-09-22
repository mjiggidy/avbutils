
"""Utilities for working with timelines ("Sequences" in Media Composer parlance)"""

import collections.abc, enum
import avb

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

def get_video_track_from_composition(composition:avb.trackgroups.Composition, media_kind:str="picture", track_index:int=1) -> avb.components.Sequence:
	"""Get V1 by default"""

	for track in composition.tracks:
		if track.index == track_index and track.media_kind == media_kind:
			return track.component
	
	raise IndexError(f"No V{track_index} found in sequence")