"""Helper functions for matching back components"""

import avb
from .timeline import get_tracks_from_composition, TrackTypes
from . import compositions

class IsAsMatchedBackAsCanBe(StopIteration):
	"""This is as matched back as you can get, sir"""

def matchback_groupclip(group:avb.trackgroups.Selector, selected_track_index:int|None=None) -> avb.components.Component:
	"""Matchback a groupclip"""

	# Groupclip seems to be a TrackGroup with a `selected` property pointing to the active camera
	selected_track = group.tracks[selected_track_index if selected_track_index is not None else group.selected]
	return matchback_track(selected_track)

def matchback_trackgroup(track_group:avb.trackgroups.TrackGroup, media_kind:str="picture", use_first_track:bool=False) -> avb.components.Component:

	filtered_tracks = [t for t in track_group.tracks if t.media_kind == media_kind]

	if not use_first_track and len(filtered_tracks) != 1:
		raise ValueError(f"{track_group}: Got {filtered_tracks}")
	
	return matchback_track(filtered_tracks)

def matchback_track(track:avb.trackgroups.Track) -> avb.components.Component:
	"""Get the component of a Track"""
	return track.component

def matchback_sequence(sequence:avb.components.Sequence) -> avb.components.Component:
	"""Get components from a sequence"""
	
	# Sequences start and end with filler
	# Probably want to do a "get component at location" thing here

	if len(sequence.components) != 3:
		raise ValueError(f"Sequence has {len(sequence.components)} components: {sequence.components}")
	
	return list(sequence.components)[1]

def matchback_sourceclip(source_clip:avb.components.SourceClip) -> avb.components.Component:
	"""Resolve MOB for a given `SourceClip`"""

	return source_clip.root.content.find_by_mob_id(source_clip.mob_id)

	# TODO: This does weird things. Investigate:
	#return source_clip.track

def matchback_trackeffect(component:avb.trackgroups.TrackEffect) -> avb.components.Component:
	"""Track effect matchback... do my best"""

	for track in component.tracks:
		return matchback_track(track)
		if "components" not in track.component.property_data or len(track.component.components) == 1:
			continue
	raise ValueError("Empty effects track (TODO)")

def is_masterclip(component:avb.components.Component) -> bool:
	"""Is a component a masterclip?"""
	return isinstance(component, avb.trackgroups.Composition) and compositions.MobTypes.from_composition(component) == compositions.MobTypes.MASTER_MOB

def is_subclip(component:avb.components.Component) -> bool:
	"""Is a component a subclip?"""
	return isinstance(component, avb.trackgroups.Composition) and compositions.MobUsage.from_composition(component) == compositions.MobUsage.SUBCLIP

def is_sourcemob(component:avb.components.Component) -> bool:
	"""Is a component a source mob?"""
	return isinstance(component, avb.trackgroups.Composition) and compositions.MobTypes.from_composition(component) == compositions.MobTypes.SOURCE_MOB

def matchback_component(component:avb.components.Component, track_type:TrackTypes|None=None, track_index:int|None=None) -> avb.components.Component:
	"""Generic: Matchback a given component"""

	

	if isinstance(component, avb.trackgroups.Composition):
		return next(get_tracks_from_composition(component, type=track_type, index=1))

	elif isinstance(component, avb.trackgroups.Selector):
		return matchback_groupclip(component)
	
	elif isinstance(component, avb.components.SourceClip):
		return matchback_sourceclip(component)
	
	elif isinstance(component, avb.trackgroups.TrackEffect):
		return  matchback_trackeffect(component)

	elif isinstance(component, avb.trackgroups.TrackGroup):
		return matchback_trackgroup(component)
	
	# Oooohh.... you know whaaaat.....
	elif isinstance(component, avb.trackgroups.Track):
		return matchback_track(component)
	
	elif isinstance(component, avb.components.Sequence):
		return matchback_sequence(component)
	
	else:
		raise IsAsMatchedBackAsCanBe()

def matchback_to_sourcemob(component:avb.components.Component) -> avb.components.Component:
	"""Given a component, match it back until we're at the source mob"""

	# Keep goin' 'till we can't SourceMob no more??
	# TODO: VERY SKEPTICAL THAT THIS IS THE WAY TO GO.

	source_mob = None

	while True:
		try:
			component = matchback_component(component)
			if is_sourcemob(component):
				source_mob = component
		except IsAsMatchedBackAsCanBe:
			break
	
	return source_mob


def matchback_to_masterclip(component:avb.components.Component) -> avb.components.Component:
	"""Given a component, match it back until we're at the masterclip"""

	while not is_masterclip(component):

		try:
			component = matchback_component(component)
		except IsAsMatchedBackAsCanBe:
			print(f"Stalled at {component}")
			break
		
	return component

def matchback_to_sourceclip(component:avb.components.Component) -> avb.components.SourceClip:
	"""Match back fancy things (Selectors/Group Clips, Track Effects, etc) to their subclips"""

	while not isinstance(component, avb.components.SourceClip):

		try:
			component = matchback_component(component)
		except IsAsMatchedBackAsCanBe:
			print(f"Stalled at {component}")
			break
	
	return component