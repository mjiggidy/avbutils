"""
v3 method proves reliable
v4 refines v3
v5 focuses on using SourceClip as the "currency" rather than Compositions.
   I think that'll be cleaner overall, so we don't have to deal explicitly
   with tracks as much, outside of these functions.
"""



# Given a clip
# Choose a track
# ---
# Resolve its source clip for a given offset (adjusted for dest edit_rate)
# Match to corresponding track from mob
# ---
# Repeat

import sys, pathlib, typing
from os import PathLike
import avb, avbutils

def matchback_sourceclip(source_clip:avb.components.SourceClip, offset:int=0) -> avb.components.Component:
	"""Given a `SourceClip,` follow its reference to its source"""

	if not isinstance(source_clip, avb.components.SourceClip) or not source_clip.mob:
		#print("Got", source_clip)
		raise avbutils.IsAsMatchedBackAsCanBe
	
	# From the referenced mob, find the referenced track
	try:
		matched_track = next(t for t in source_clip.mob.tracks if t.media_kind == source_clip.media_kind and t.index == source_clip.track_id)
	except StopIteration:
		raise ValueError(f"Could not find track {source_clip.media_kind=}{source_clip.track_id=} in mob {source_clip.mob} ({avbutils.format_track_labels(source_clip.mob.tracks)})")
	
	# From the referenced track, recover the referenced component at the referenced start_time
	return resolve_root_component(matched_track.component, offset=source_clip.start_time+offset) # TODO: Need to do the offset conversion thing still(?)



def resolve_root_component(component:avb.components.Component, offset:int=0) -> avb.components.Component:
	"""Given a component, crawl through track effects or sequences to access the root component, such as a `avb.components.SourceClip`"""

	#print(component)

	while isinstance(component, avb.components.Sequence) or isinstance(component, avb.trackgroups.TrackGroup) or isinstance(component, avb.trackgroups.Track):
		#print("Then resolve", component)
		# Sequence? Find component at time
		if isinstance(component, avb.components.Sequence):
			component,_ = component.nearest_component_at_time(offset)

		elif isinstance(component, avb.trackgroups.Track):

			# NOTE: Precompute Mobs end with, like, some kind of track that has no component
			if "component" not in component.property_data:
				#print("********** BREAK")
				break
			component = resolve_root_component(component.component, offset)
		
		# Trackgrounp (TrackEffect, etc)?  Get relevant track from inner trackgroup
		elif isinstance(component, avb.trackgroups.TrackGroup):

			#print(component.media_kind, component.property_data)
			#exit()
			#print("Uh oh")
			for t in component.tracks:

				try:
					component = resolve_root_component(t, offset)
				except ValueError:
					continue

	#		raise ValueError(f"Track not found: {avbutils.format_track_label(track)} not in {component}")
	
	return component



################################
################################
################################

def get_bin_paths(user_paths:list[PathLike]) -> typing.Generator[pathlib.Path, None, None]:
	"""Get bin paths from a list of file or folder paths"""

	for user_path in {pathlib.Path(u) for u in user_paths}:
		
		if user_path.is_dir():
			yield from (p for p in user_path.rglob("*.avb") if not p.name.startswith("."))
		elif user_path.is_file():
			yield user_path

def get_test_clips(bin_content:avb.bin.Bin) -> typing.Iterator[avb.trackgroups.Composition]:
	
	# Return first master mob
	#yield next(bin_content.mastermobs())

	yield from bin_content.mastermobs()

if __name__ == "__main__":

	for bin_path in get_bin_paths(sys.argv[1:]):
		print(bin_path)

		with avb.open(bin_path) as bin_handle:

			for mastermob in bin_handle.content.mobs:

				# Get the first track just so we gots sumn
				print(str(mastermob.name) + f" ({avbutils.format_track_labels(mastermob.tracks)})")


				for source_track in mastermob.tracks:
					
					source_clip  = resolve_root_component(source_track.component, offset=0)

					while True:
						print(avbutils.format_track_label(source_track), " -> ", source_clip)
						
						try:
							source_clip = matchback_sourceclip(source_clip, offset=0)
						except avbutils.IsAsMatchedBackAsCanBe:
							print("---")
							break
						