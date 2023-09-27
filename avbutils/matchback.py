"""Helper functions for matching back components"""

import avb
from .timeline import get_tracks_from_composition, TrackTypes

class IsAsMatchedBackAsCanBe(StopIteration):
	"""This is as matched back as you can get, sir"""

def matchback_groupclip(group:avb.trackgroups.Selector, selected_track_index:int|None=None) -> avb.components.Component:
	"""Matchback a groupclip"""

	# Groupclip seems to be a TrackGroup with a `selected` property pointing to the active camera
	selected_track = group.tracks[selected_track_index if selected_track_index is not None else group.selected]
	return matchback_track(selected_track)

def matchback_trackgroup(track_group:avb.trackgroups.TrackGroup, media_kind:str="picture") -> avb.components.Component:

	filtered_tracks = [t for t in track_group.tracks if t.media_kind == media_kind]

	if len(filtered_tracks) != 1:
		return f"{track_group}: Got {filtered_tracks}"

	return matchback_track(filtered_tracks[0])

def matchback_track(track:avb.trackgroups.Track) -> avb.components.Component:
	"""Get the component of a Track"""

	return track.component

def matchback_sequence(sequence:avb.components.Sequence) -> avb.components.Component:
	"""Get components from a sequence"""
	
	# Sequences start and end with filler
	# Probably want to do a "get component at location" thing here

	if len(sequence.components) > 3:
		return f"Sequence has {len(sequence.components)} components: {sequence.components}"

	#print(f" Returning {sequence.components[1]}")
	return sequence.components[1]

def matchback_sourceclip(source_clip:avb.components.SourceClip) -> avb.components.Component:
	"""Resolve MOB for a given `SourceClip`"""

	return source_clip.root.content.find_by_mob_id(source_clip.mob_id)

	# TODO: This does weird things. Investigate:
	#return source_clip.track

def is_masterclip(component:avb.components.Component) -> bool:
	"""Is a component a masterclip?"""
	
	return isinstance(component, avb.trackgroups.Composition) and component.mob_type == "MasterMob"

def is_sourcemob(component:avb.components.Component) -> bool:
	"""Is a component a source mob?"""

	return isinstance(component, avb.trackgroups.Composition) and component.mob_type == "SourceMob"

def matchback_component(component:avb.components.Component) -> avb.components.Component:
	"""Generic: Matchback a given component"""

	if isinstance(component, avb.trackgroups.Composition):
		return next(get_tracks_from_composition(component, type=TrackTypes.PICTURE, index=1))

	if isinstance(component, avb.trackgroups.Selector):
		return matchback_groupclip(component)

	elif isinstance(component, avb.trackgroups.TrackGroup):
		return matchback_trackgroup(component)
	
	# Oooohh.... you know whaaaat.....
	elif isinstance(component, avb.trackgroups.Track):
		return matchback_track(component)
	
	elif isinstance(component, avb.components.SourceClip):
		return matchback_sourceclip(component)

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

		if isinstance(component, avb.trackgroups.Composition):
			component = next(get_tracks_from_composition(component, type=TrackTypes.PICTURE, index=1))

		if isinstance(component, avb.trackgroups.Selector):
			component = matchback_groupclip(component)

		elif isinstance(component, avb.trackgroups.TrackGroup):
			component = matchback_trackgroup(component)
		
		# Oooohh.... you know whaaaat.....
		elif isinstance(component, avb.trackgroups.Track):
			component = matchback_track(component)
		
		elif isinstance(component, avb.components.SourceClip):
			component = matchback_sourceclip(component)

		elif isinstance(component, avb.components.Sequence):
			component = matchback_sequence(component)

		elif isinstance(component, avb.components.Filler):
			break

		else:
			print(component)
			break
		
	return component