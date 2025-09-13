import sys
import avb, avbutils

class StopMatchback(StopIteration):
	"""Track cannot be resolved further"""

class FillerDuringMatchback(ValueError):
	"""Encountered unexpected Filler while matching back"""


def comp_is_essence_mob(comp:avb.trackgroups.Composition):
	"""Mob contains an essence descriptor"""

	return "descriptor" in comp.property_data and isinstance(comp.descriptor, avb.essence.MediaDescriptor)

def get_mob_from_track_at_offset(track:avb.trackgroups.Track, offset:int) -> tuple[avb.trackgroups.Composition, avb.trackgroups.Track, int]:

	# Track contains a component that points to another mob
	# For a master/source mob, typically resolves to a Sequence -> SourceClip
	# Source clip references track_id and start_time, len from the mob it points to
	
	component = track.component

	if isinstance(component, avb.trackgroups.Selector):
		#print(component)
		component = next(t for t in avbutils.get_tracks_from_composition(component, avbutils.TrackTypes.PICTURE, component.selected)).component

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

	#offset += component.start_time

	print("Offset: ", offset)


	#print("Resolved", component)
	#print(component.start_time)
	#print(component.property_data)

	resolved_mob = track.root.content.find_by_mob_id(component.mob_id)
	resolved_track = next(t for t in resolved_mob.tracks if t.media_kind == track.media_kind and t.index == component.track_id)

	#try:
	#	print(resolved_mob.descriptor)
	#except:
	#	pass

	# NOTE: Need to think about offset
	return resolved_mob, resolved_track, component.start_time





def inspect_comp_stack(comps:list[avb.trackgroups.Composition]):

	for comp in comps:

		print("\n---\n")
		print(comp)
		
		#tracks_tc = [t for t in comp.tracks if t.media_kind == "timecode"]
		#if tracks_tc:
		#	print(f"Has {len(tracks_tc)} timecode tracks:")
		#	for track in tracks_tc:
		#		print_timecode_track(track)
		#		print("-")
		
		print("Has tracks: ", avbutils.format_track_labels(comp.tracks))
		
		if not comp.descriptor:
			print("Master Mob:", comp.name)
			continue
		
		# NOTE:
		# AMA'd essence mobs seem to contain MultiDescriptor, which in turn has one essence descriptor (CDCI, PCMA, etc) per media track
		# Each of those essence descriptors contain an MSMLocator which I thought was exclusively for Avid Media, but the difference 
		# Is that the locator will have a `physical_media` ref, with a locator in THERE that points to a MacFileLocator or something
		# Compared to traditional avid media which has no physical media ref in its MSMLocator
		#
		# So from what I can tell:
		#
		#     Hard-imported files:  Essence descriptor has generic MSMLocator
		#                           Source descriptor is generic MediaDescriptor with mac file locators
		#
		#             AMA'd files:  Essence descriptor has MultiDescriptor per essence; each essence is MSMLocator BUT with physical media locator
		#                           Source descriptor is generic MediaDescritptor with mac file locators (same as hard-import)
		#
		#       Traditional media:  Essence descriptor has generic MSMLocator
		#                           Source descriptor is TapeDescriptor
		
		descriptors = comp.descriptor.descriptors if isinstance(comp.descriptor, avb.essence.MultiDescriptor) else [comp.descriptor]

		for descriptor in descriptors:
			print("")
			print(descriptor, descriptor.mob_kind)
 
			# TAPE MOB
			if isinstance(descriptor, avb.essence.TapeDescriptor):
				print(f"TAPE MOB: {comp.name}")

			# Soundroll Mob
			elif isinstance(descriptor, avb.essence. NagraDescriptor):
				print(f"SOUNDROLL MOB: {comp.name}")

			# Essence Mob
			elif isinstance(descriptor, avb.essence.MediaFileDescriptor):

				if isinstance(descriptor.locator, avb.misc.MSMLocator):
					print(f"ESSENCE MOB: Avid media from {descriptor.locator.last_known_volume_utf8}, MobID: {descriptor.locator.mob_id}")

					if "physical_media" in descriptor.property_data and descriptor.physical_media:
						print("* physical_media: ", descriptor.physical_media.property_data)
						print("**loc:", descriptor.physical_media.locator.property_data)

				elif isinstance(descriptor.locator, avb.misc.FileLocator):
					print(f"ESSENCE MOB: Source file name: {comp.name}")
					print(f"ESSENCE MOB: Source file path: {descriptor.locator.path_utf8}")

				elif isinstance(descriptor.locator, avb.misc.URLLocator):
					raise NotImplementedError("Don't know what to do with avb.misc.URLLocator")
				
				else:
					print("**UNKNOWN**")
					print(f"Descriptor: {descriptor.property_data}")
					print(f"Locator: {descriptor.locator}")
					for track in comp.tracks:
						print(avbutils.format_track_label(track), track.component, f"({[c.property_data for c in track.component.components]})")
			
			# Other
			# NOTE: File-based (AMA'd or hard imported) tend to terminate with a generic essence.MediaDescriptor, mob_kind==5, with a Locator to the file
			else:
				print("GENERIC MOB DESCRIPTOR:", descriptor)
				print("property_data:", descriptor.property_data)
				print("locator:", descriptor.locator.property_data)



def resolve_from_comp_stack(comps:list[avb.trackgroups.Composition]):
	"""Resolve clip attributes from all the comps resolved"""

	tapes = []
	files = []



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

	last_component_offset = 0

	while True:
		comps.append(composition)
		try:
			#print(frame_offset)
			print(f"Looking up new offset {frame_offset + last_component_offset}")
			composition, track, last_component_offset = get_mob_from_track_at_offset(track, frame_offset + last_component_offset+1) # NOTE: WHY THE +1 NEEDED ARGH
		except StopMatchback:
			break
		except FillerDuringMatchback:
			break
	
	return comps

		
	
def is_valid_test_track(track:avb.trackgroups.Track) -> bool:
	return True
	#return avbutils.TrackTypes.from_track(track) in (avbutils.TrackTypes.PICTURE, avbutils.TrackTypes.SOUND)

def is_valid_test_item(bin_item:avb.bin.BinItem) -> bool:
	"""Filter for valid testing item"""
	return not avbutils.composition_is_timeline(bin_item.mob)
	#return bin_item.user_placed and not avbutils.composition_is_timeline(bin_item.mob)
	#return avbutils.composition_is_subclip(bin_item.mob) #and "/" in bin_item.mob.name
	#return avbutils.composition_is_groupclip(bin_item.mob) #and "/" in bin_item.mob.name


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
		test_clip  = random.choice(list(filter(is_valid_test_item, bin_handle.content.items)))

	#	for test_clip in filter(is_valid_test_item, bin_handle.content.items):
		test_clip = test_clip.mob
		if isinstance(test_clip, avb.trackgroups.Selector):
			test_track = next(t for t in test_clip.tracks if t.media_kind == "picture" and t.index == test_clip.selected)
		else:
			test_track = random.choice(list(filter(is_valid_test_track, test_clip.tracks)))
		
		#comps = trace_clip(test_clip, test_track, frame_offset=min(2400, test_clip.length-1))
		comps = trace_clip(test_clip, test_track, frame_offset=0)

		inspect_comp_stack(comps)

		

		#for comp in comps:
		#	print(comp.essence)