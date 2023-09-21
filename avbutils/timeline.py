
"""Utilities for working with timelines ("Sequences" in Media Composer parlance)"""

import collections.abc
import avb

def get_timelines_from_bin(bin:avb.bin.Bin) -> collections.abc.Generator[avb.trackgroups.Composition,None,None]:
	"""Get all top-level timelines ("Sequences" in Media Composer) in a given Avid bin"""
	return (mob for mob in bin.toplevel() if isinstance(mob, avb.trackgroups.Composition))

def get_video_track_from_composition(composition:avb.trackgroups.Composition, media_kind:str="picture", track_index:int=1) -> avb.components.Sequence:
	"""Get V1 by default"""

	for track in composition.tracks:
		if track.index == track_index and track.media_kind == media_kind:
			return track.component
	
	raise IndexError(f"No V{track_index} found in sequence")