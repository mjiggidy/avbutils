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

	if isinstance(component, avb.trackgroups.TrackEffect) or isinstance(component, avb.trackgroups.TimeWarp):
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





def inspect_comp_stack(comps:list[avb.trackgroups.Composition]):

	for comp in comps:

		print("\n---\n")
		print(comp)
		
		tracks_tc = [t for t in comp.tracks if t.media_kind == "timecode"]
		if tracks_tc:
			print(f"Has {len(tracks_tc)} timecode tracks:")
			for track in tracks_tc:
				print_timecode_track(track)


		tracks_edge = [t for t in comp.tracks if t.media_kind == "edgecode"]
		if tracks_edge:
			print(f"Has {len(tracks_edge)} edgecode tracks")
		
		print(comp.descriptor)

		if isinstance(comp.descriptor, avb.essence.TapeDescriptor):
			print(f"Tape name: {comp.name}")

		elif isinstance(comp.descriptor, avb.essence.MediaDescriptor):

			if isinstance(comp.descriptor.locator, avb.misc.MSMLocator):
				print(f"Avid media from {comp.descriptor.locator.last_known_volume_utf8}, MobID: {comp.descriptor.locator.mob_id}")

			elif isinstance(comp.descriptor.locator, avb.misc.FileLocator):
				print(f"Source file name: {comp.name}")
				print(f"Source file path: {comp.descriptor.locator.path_utf8}")

			elif isinstance(comp.descriptor.locator, avb.misc.URLLocator):
				raise NotImplementedError("Don't know what to do with avb.misc.URLLocator")
			
			else:
				print("**UNKNOWN**")
				print(f"Descriptor: {comp.descriptor.property_data}")
				print(f"Locator: {comp.descriptor.locator}")



# ############ #
# End of tests #
# ############ #

def print_timecode_track(track:avb.trackgroups.Track):

	import timecode

	if isinstance(track.component, avb.components.Sequence):

		components = [c for c in track.component.components]
	else:
		components = [track.component]
	
	for tc in components:
		
		if isinstance(tc, avb.components.Timecode):
			tc_parsed = timecode.TimecodeRange(start=timecode.Timecode(tc.start, rate=round(tc.edit_rate)), duration=tc.length)
			print("  - ", f"{tc_parsed.start} - {tc_parsed.end} ({tc_parsed.duration}) @ {tc_parsed.rate}")

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
	return avbutils.composition_is_masterclip(bin_item.mob) #and "/" in bin_item.mob.name


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

		inspect_comp_stack(comps)

		#for comp in comps:
		#	print(comp.essence)