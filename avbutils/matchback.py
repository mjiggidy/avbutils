"""Helper functions for matching back components"""

import avb

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

def matchback_sourceclip(source_clip:avb.components.SourceClip, bin_handle:avb.file.AVBFile) -> avb.components.Component:
	"""Resolve MOB for a given `SourceClip`"""

	return bin_handle.content.find_by_mob_id(source_clip.mob_id)

def is_masterclip(component:avb.components.Component) -> bool:
	"""Is a component a masterclip?"""
	
	return isinstance(component, avb.trackgroups.Composition) and component.mob_type == "MasterMob"