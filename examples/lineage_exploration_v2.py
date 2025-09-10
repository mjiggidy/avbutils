import sys
import avb, avbutils

class StopMatchback(StopIteration):
	"""Track cannot be resolved further"""

class FillerDuringMatchback(ValueError):
	"""Encountered unexpected Filler while matching back"""

def get_mob_from_track_at_offset(track:avb.trackgroups.Track, offset:int) -> tuple[avb.trackgroups.Composition, avb.trackgroups.Track, int]:

	# Track contains a component that points to another mob
	# For a master/source mob, typically resolves to a Sequence -> SourceClip
	# Source clip references track_id and start_time, len from the mob it points to
	
	component = track.component

	if isinstance(component, avb.trackgroups.TrackEffect):
		# Unwrap TrackEffect
		track = next(filter(lambda t: t.media_kind == track.media_kind and t.index == track.index, component.tracks))
		component = track.component
	
	if isinstance(component, avb.components.Sequence):
		component, component_offset = track.component.nearest_component_at_time(offset)
		# NOTE: What to do about component_offset? ...add to offset or something?

	if isinstance(component, avb.components.Filler):
		print("(Got filler)")
		raise FillerDuringMatchback

	if component.track_id == 0:
		raise StopMatchback

	offset += component.start_time


	#print("Resolved", component)
	#print(component.property_data)

	resolved_mob = track.root.content.find_by_mob_id(component.mob_id)
	resolved_track = next(t for t in resolved_mob.tracks if t.media_kind == track.media_kind and t.index == component.track_id)

	try:
		print(resolved_mob.descriptor)
	except:
		pass

	# NOTE: Need to think about offset
	return resolved_mob, resolved_track, offset




# ############ #
# End of tests #
# ############ #

def trace_clip(composition:avb.trackgroups.Composition, track:avb.trackgroups.Track, frame_offset:int) -> list[avb.trackgroups.Composition]:

	print("---")
	print(f"{composition.name} is a {avbutils.MobTypes.from_composition(composition)} from {bin_handle.f.name}")
	print(f"Matching back from track {avbutils.format_track_label(track)} with frame offset {frame_offset}")
	print("---")

	comps = []

	while True:
		comps.append(composition)
		try:
			#print(frame_offset)
			composition, track, frame_offset = get_mob_from_track_at_offset(track, frame_offset)
		except StopMatchback:
			break
		except FillerDuringMatchback:
			break
	
	return comps

		
	
def is_valid_test_track(track:avb.trackgroups.Track) -> bool:
	return avbutils.TrackTypes.from_track(track) in (avbutils.TrackTypes.PICTURE, avbutils.TrackTypes.SOUND)

def is_valid_test_item(bin_item:avb.bin.BinItem) -> bool:
	"""Filter for valid testing item"""
	return avbutils.composition_is_masterclip(bin_item.mob)


# ############## #
# End of helpers #
# ############## #
if __name__ == "__main__":

	if not len(sys.argv) > 1:
		sys.exit(f"Usage: {__file__} bin_path.avb")
	
	bin_path = sys.argv[1]
	
	with avb.open(sys.argv[1]) as bin_handle:

		import random

		# Find valid comp and track for testing
		test_clip  = random.choice(list(filter(is_valid_test_item, bin_handle.content.items))).mob
		test_track = next(filter(is_valid_test_track, test_clip.tracks))
		
		comps = trace_clip(test_clip, test_track, frame_offset=0)

		#for comp in comps:
		#	print(comp.essence)