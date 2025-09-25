"""
From v9's success, moving to avbutils and figuring out common usage
"""

import typing, timecode
import avb, avbutils


def show_composition_info(composition:avb.trackgroups.Composition):

	comp_name = composition.name
	comp_tracks = avbutils.format_track_labels(composition.tracks)
	comp_rate   = composition.edit_rate

	
	# NOTE: Juuuuuuuust in case anybody is reading this --
	# First: hello.  Second: All of this code is a total mess, I know.  I'm just... you know...
	# I... I'm just working through some stuff.
	
	primary_track = avbutils.format_track_label(avbutils.sourcerefs.primary_track_for_composition(composition))
	
	if avbutils.sourcerefs.composition_has_physical_source(composition):
		source_name = avbutils.sourcerefs.physical_source_name_for_composition(composition)
		source_type = avbutils.sourcerefs.physical_source_type_for_composition(composition)
	else:
		source_type = None
		source_name = None

	tc_track = None
	tc_component = None
	tc_range = None

	for source, offset in avbutils.source_references_for_component(avbutils.sourcerefs.primary_track_for_composition(composition).component):
		try:
			tc_track = next(avbutils.get_tracks_from_composition(source.mob, type=avbutils.TrackTypes.TIMECODE, index=1))
		except:
			continue
		else:
			tc_component, offset = avbutils.resolve_base_component_from_component(tc_track.component, offset + source.start_time)
			
			if not isinstance(tc_component, avb.components.Timecode):
				tc_range = f"Got {tc_component} instead"
				print("Hmm")
				continue
			
			tc_range = timecode.TimecodeRange(
				start = timecode.Timecode(tc_component.start + offset.frame_number, rate=offset.rate),
				duration=composition.length
			)

			tc_range = "\t".join(str(x) for x in [tc_range.start, tc_range.end, str(tc_range.duration).lstrip("00:"), tc_range.rate])
			break
	
	


		


	print("\t".join(str(x) for x in [
		comp_name,
		comp_tracks,
		comp_rate,
		primary_track,
		source_type,
		source_name,
		tc_range
	]))





###

if __name__ == "__main__":

	import pathlib, sys
	from os import PathLike


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

		with avb.open(bin_path) as bin_handle:

			for bin_item in filter(is_valid_test_item, bin_handle.content.items):
				
				try:

					#print("---")
					do_bin_item(bin_item)

				except Exception as e:
					raise Exception from e
	
	def do_bin_item(bin_item:avb.bin.BinItem):
		show_composition_info(bin_item.mob)


	for bin_path in get_bin_paths(sys.argv[1:]):
		
		print(bin_path)
		do_bin(bin_path)
	
	print(f"")
