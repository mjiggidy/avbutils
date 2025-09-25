import typing
import avb, avbutils, timecode

def resolve_base_component_from_component(component:avb.components.Component, offset:timecode.Timecode|int=0) -> tuple[avb.components.Component, timecode.Timecode]:
	"""Given a component, resolve base components from any "compound" components such as trackeffects or sequences"""

	if not isinstance(offset, timecode.Timecode):
		offset = offset = timecode.Timecode(offset, rate=round(component.edit_rate))

	# First ensure we're in the right rate
	if not offset.rate == round(component.edit_rate):
		#raise ValueError(f"{offset.rate=} does not equal {component.edit_rate=}")
#		input(f"{__name__}: Now converting offset from {offset.rate} to {round(component.edit_rate)}")
		offset = offset.resample(rate=round(component.edit_rate))
	
	if isinstance(component, avb.components.Sequence):

		component, from_sequence_start = component.nearest_component_at_time(offset.frame_number)
		offset -= from_sequence_start

		if round(component.edit_rate) != offset.rate:
#			input(f"Now converting new offset from {offset.rate} to {round(component.edit_rate)}")
			offset.resample(round(component.edit_rate))

	elif isinstance(component, avb.trackgroups.EssenceGroup) or isinstance(component, avb.trackgroups.TrackEffect):
		if len(component.tracks) == 1:
			component, offset = resolve_base_component_from_component(component.tracks[0].component, offset)
#			print(f"LOOK: HAHA OKAY JUST THE ONE")
		else:
			pass #??
#			print(f"LOOK: For {component}, Got {len(component.tracks)}  {avbutils.format_track_labels(component.tracks)}")
	
	elif isinstance(component, avb.trackgroups.Track) and "component" in component.property_data:
		component, offset = resolve_base_component_from_component(component.component, offset)
		#input("Just resolved")
	
#	else:
#		print(component)
	return component, offset


def source_references_for_component(component:avb.components.Component, offset:timecode.Timecode|int=0) -> typing.Generator[tuple[avb.components.SourceClip, timecode.Timecode], None, None]:
	"""Given a composition, resolve its source reference clips and relative offsets"""

	# -  Dig in and resolve the base component from any heirarchy goin' on (sequences, track effects, etc),
	#    adjusting for relative offsets/rates
	# -  Return the resolved component & adjusted offset if it points to a source mob

	if isinstance(offset, timecode.Timecode) and not offset.rate == round(component.edit_rate):
		#raise ValueError(f"{offset.rate=} does not equal {component.edit_rate=}")
#		input(f"{__name__}: Now converting offset from {offset.rate} to {round(component.edit_rate)}")
		offset = offset.resample(rate=round(component.edit_rate))
	else:
		offset = timecode.Timecode(offset, rate=round(component.edit_rate))

	component, offset = resolve_base_component_from_component(component, offset)
	
	while isinstance(component, avb.components.SourceClip) and component.track:
		
		yield component, offset
		component, offset = resolve_base_component_from_component(component.track.component, component.start_time + offset)



	


def show_composition_info(comp:avb.trackgroups.Composition):
	"""Display info and see how I failed next"""
	
	print(f"{comp.name} ({avbutils.format_track_labels(comp.tracks)}) - {comp.edit_rate} fps")

	for track in comp.tracks:
		track_info = []
		for clip, offset in source_references_for_component(track.component):
			track_info.append(
				f"[{avbutils.SourceMobRole.from_composition(clip.mob)}: {clip.mob.name} " \
				f"({avbutils.format_track_labels(clip.mob.tracks)}) " \
				f"({type(clip.mob.descriptor).__name__} @ {type(clip.mob.descriptor.locator).__name__}) " \
				f"start_time={clip.start_time} rate={clip.edit_rate}]"
			)
		
		print("|".join(track_info))



	

###
###

if __name__ == "__main__":

	import pathlib, sys
	from os import PathLike

	fail = 0
	succ = 0

	invalid = list()

	def is_valid_test_item(bin_item:avb.bin.BinItem) -> bool:
		"""Use this item as a test item"""

		return avbutils.MobTypes.from_composition(bin_item.mob) == avbutils.MobTypes.MASTER_MOB

	def get_bin_paths(user_paths:list[PathLike]) -> typing.Generator[pathlib.Path, None, None]:
		"""Get bin paths from a list of file or folder paths"""

		for user_path in {pathlib.Path(u) for u in user_paths}:
			
			if user_path.is_dir():
				yield from (p for p in user_path.rglob("*.avb") if not p.name.startswith("."))
			elif user_path.is_file():
				yield user_path
	
	def do_bin(bin_path:PathLike):

		global succ
		global fail

		with avb.open(bin_path) as bin_handle:

			for bin_item in filter(is_valid_test_item, bin_handle.content.items):
				
				try:
					print("---")
					do_bin_item(bin_item)
					succ += 1
				except Exception as e:
					fail += 1
					raise Exception from e
	
	def do_bin_item(bin_item:avb.bin.BinItem):
		show_composition_info(bin_item.mob)


	for bin_path in get_bin_paths(sys.argv[1:]):
		
		print(bin_path)
		do_bin(bin_path)
		
		print(f"{succ=} {fail=} {len(invalid)=}", file=sys.stderr, end="\r")
	
	print(f"")
