import typing
import avb, avbutils


def resolve_root_component(component:avb.components.Component, offset:int=0) -> avb.components.Component:
	"""Given a component, crawl through track effects or sequences to access the root component, such as a `avb.components.SourceClip`"""

	while isinstance(component, avb.components.Sequence) or isinstance(component, avb.trackgroups.TrackGroup) or isinstance(component, avb.trackgroups.Track):

		# Sequence? Find component at time
		if isinstance(component, avb.components.Sequence):
			component,_ = component.nearest_component_at_time(offset)

		elif isinstance(component, avb.trackgroups.Track):

			# NOTE: Precompute Mobs end with, like, some kind of track that has no component
			if "component" not in component.property_data:
				break

			component = resolve_root_component(component.component, offset)
		
		# Trackgrounp (TrackEffect, etc)?  Get relevant track from inner trackgroup
		elif isinstance(component, avb.trackgroups.TrackGroup):

			# NOTE: I don't believe in this
			#exit()
			for t in component.tracks:

				try:
					component = resolve_root_component(t, offset)
					break
				except ValueError:
					continue
	
	return component

def source_references_for_component(component:avb.components.Component) -> typing.Generator[avb.components.SourceClip,None,None]:

	# Get to the root SourceClip or whatever
	component = resolve_root_component(component)
	
	# If that root was indeed a SourceClip and has a mob, return it
	if isinstance(component, avb.components.SourceClip) and component.mob:
		yield component.track.component
	
	else:
		raise avbutils.IsAsMatchedBackAsCanBe




def show_composition_info(composition:avb.trackgroups.Composition):

	print(f"{composition.name} ({avbutils.format_track_labels(composition.tracks)})")

	for track in composition.tracks:

		# Resolve root component of track component
		# That gives us our next SourceClip with mob OR another component type

		
		# Start by resolving the SrcClip of the desired track
		# And then get the next SrcClip in line.
		#root_component = resolve_root_component(track.component)
		#while isinstance(root_component, avb.components.SourceClip) and root_component.mob:
		#	referenced_clips.append(root_component)
		#	root_component = resolve_root_component(
		#		root_component.track.component,
		#		offset=root_component.start_time #?
		#	)

		referenced_clips = list(source_references_for_component(track.component))
		
		#mobs.append(root_component)

		reference_clip_info:list[str] = []
		for clip in referenced_clips:
			reference_clip_info.append(
				f"[{avbutils.SourceMobRole.from_composition(clip.mob)}: {clip.mob.name} ({clip.mob.descriptor, clip.mob.descriptor.locator})]"
			)

		print(f"{avbutils.format_track_label(track).rjust(3)} : {' '.join(reference_clip_info)}")









if __name__ == "__main__":

	import pathlib, sys
	from os import PathLike

	fail = 0
	succ = 0

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
		
		print(f"{succ=} {fail=}", file=sys.stderr, end="\r")

