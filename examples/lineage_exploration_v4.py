import sys, pathlib, typing
from os import PathLike
import avb, avbutils

def resolve_source_clip_from_component(component:avb.components.Component, offset:int=0) -> avb.components.SourceClip:
	"""Unwind the next SourceClip from a given track component, digging into track effects, etc"""
	
	# Unwind component until we get to the actual thing
	while isinstance(component, avb.components.Sequence) or isinstance(component, avb.trackgroups.TrackGroup) or isinstance(component, avb.trackgroups.Track):

		# Sequence? Find component at time
		# NOTE: offset, at this point, needs to be converted to resolve component
		if isinstance(component, avb.components.Sequence):
			component,_ = component.nearest_component_at_time(offset)

		elif isinstance(component, avb.trackgroups.Track):

			# NOTE: Precompute Mobs end with, like, some kind of track that has no component
			if "component" not in component.property_data:
				#print("********** BREAK")
				break
			component = resolve_source_clip_from_component(component.component, offset)
		
		# Trackgrounp (TrackEffect, etc)?  Get relevant track from inner trackgroup
		elif isinstance(component, avb.trackgroups.TrackGroup):

			#print(component.media_kind, component.property_data)
			#exit()
			for t in component.tracks:

				try:
					component = resolve_source_clip_from_component(t, offset)
				except ValueError:
					continue

	#		raise ValueError(f"Track not found: {avbutils.format_track_label(track)} not in {component}")
	
	return component

def matchback_composition(composition:avb.trackgroups.Composition, track:avb.trackgroups.Track, start:int=0, offset:int=0) -> avb.trackgroups.Composition:
	"""Get the next-oldest mob for a composition"""

	source_clip = resolve_source_clip_from_component(track.component, start+offset)
	
	# Sound tends to end in filler?
	if not isinstance(source_clip, avb.components.SourceClip):
		print(f"(Got {source_clip})")
		raise StopIteration
	
	# End of chain when we hit package ID = 0
	elif source_clip.mob_id.Data1 == 0:
		print(f"(Got {source_clip.mob_id})")
		raise StopIteration
	
	
	# Convert additional offset to SourceClip/next mob's timebase
	# NOTE: Rounding? Ew...
	source_clip_additional_offset = round(offset * (source_clip.edit_rate / composition.edit_rate))

	# Bounds check
	#if not (source_clip.length - (source_clip.start_time + source_clip_additional_offset)) > 0:
	#	raise ValueError(f"Offset exceeds composition bounds ({source_clip.length=} {source_clip.start_time=} {source_clip_additional_offset=})") #lool

	next_comp  = source_clip.mob
	
	try:
		next_track = next(avbutils.get_tracks_from_composition(next_comp, type=avbutils.TrackTypes.from_track(track), index=source_clip.track_id))
	except StopIteration:
		print(f"{avbutils.format_track_label(track)} not found in {next_comp} ({avbutils.format_track_labels(next_comp.tracks)})")

	return next_comp, next_track, source_clip.start_time, source_clip_additional_offset



def get_bin_paths(user_paths:list[PathLike]) -> typing.Generator[pathlib.Path, None, None]:
	"""Get bin paths from a list of file or folder paths"""

	for user_path in {pathlib.Path(u) for u in user_paths}:
		
		if user_path.is_dir():
			yield from (p for p in user_path.rglob("*.avb") if not p.name.startswith("."))
		elif user_path.is_file():
			yield user_path

def get_test_clips(bin_content:avb.bin.Bin) -> typing.Iterator[avb.trackgroups.Composition]:
	
	yield from bin_content.mastermobs()
	
	# Return first master mob
	#yield next(bin_content.mastermobs())

if __name__ == "__main__":

	for bin_path in get_bin_paths(sys.argv[1:]):
		print(bin_path)

		with avb.open(bin_path) as bin_handle:

			for mastermob in bin_handle.content.mastermobs():
				while True:
					try:
						print(mastermob)
						mastermob, track, start, offset = matchback_composition(mastermob, track=next(iter(mastermob.tracks)), start=0, offset=0)
					except StopIteration:
						break

