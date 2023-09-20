
"""Utilities for working with timelines ("Sequences" in Media Composer parlance)"""

import collections.abc
import avb

def get_timelines_from_bin(bin:avb.bin.Bin) -> collections.abc.Generator[avb.trackgroups.Composition,None,None]:
	"""Get all top-level timelines ("Sequences" in Media Composer) in a given Avid bin"""
	return (mob for mob in bin.toplevel() if isinstance(mob, avb.trackgroups.Composition))

