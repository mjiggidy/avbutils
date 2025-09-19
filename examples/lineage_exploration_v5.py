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



def resolve_component_from_track(component:avb.components.Component, offset:int=0) -> avb.components.Component:
	"""Given a component, crawl through track effects or sequences to access the root component, such as a `avb.components.SourceClip`"""

	while isinstance(component, avb.components.Sequence) or isinstance(component, avb.trackgroups.TrackGroup) or isinstance(component, avb.trackgroups.Track):
		print("Then resolve", component)
		# Sequence? Find component at time
		if isinstance(component, avb.components.Sequence):
			component,_ = component.nearest_component_at_time(offset)

		elif isinstance(component, avb.trackgroups.Track):

			# NOTE: Precompute Mobs end with, like, some kind of track that has no component
			if "component" not in component.property_data:
				#print("********** BREAK")
				break
			component = resolve_component(component.component, offset)
		
		# Trackgrounp (TrackEffect, etc)?  Get relevant track from inner trackgroup
		elif isinstance(component, avb.trackgroups.TrackGroup):

			#print(component.media_kind, component.property_data)
			#exit()
			print("Uh oh")
			for t in component.tracks:

				try:
					component = resolve_component(t, offset)
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

			for mastermob in bin_handle.content.mastermobs():

				# Get the first track just so we gots sumn
				original_track = next(iter(mastermob.tracks))
				print(mastermob.name + f" ({avbutils.format_track_label(original_track)})")

				# Start us out with our first source clip
				source_clip = resolve_component(original_track.component, offset=0)

				while True:
					print(source_clip.mob)

					track_type = avbutils.TrackTypes(source_clip.media_kind)
					track_id   = source_clip.track_id

					source_mob_track = next(avbutils.get_tracks_from_composition(source_clip.mob, type=track_type, index=track_id))
					source_clip = resolve_component(source_mob_track.component)

					if not isinstance(source_clip, avb.components.SourceClip):
						break
					elif not(source_clip.mob):
						break