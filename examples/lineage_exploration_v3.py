"""
It took me three versions to finally read "The MXF Book" as well as documentation for the AAF data model.
What I learned re-enforced what I was doing, and clarified some things.

SourceMobs reflect the lineage from "physical" (source tape, source soundroll, source file) 
to "file" (ingested into the system and now managed internally) source mobs.

Top-down, looks like this

- Groupclip Sub
- Group clip
- Subclip

- Masterclip(vs master mob?)
- Master Mob (composition of source mobs)

- File mob (Current MXF/UME media)
- Past file mobs (perhaps frame conversions, etc. Do not usually see these in Avid)

- Source mob (Source ingested/imported from, like the Tape or the Source File)
- Past source mobs (Maybe Film Source, Soundroll)

Final (root) source mob references 0 supposedly

"""

import sys, pathlib, typing
from os import PathLike
import avb, avbutils

def get_component_from_track(trackgroup:avb.trackgroups.TrackGroup, track:avb.trackgroups.Track, offset:int=0) -> avb.components.Component:
	"""Resolve the component"""


	if track not in trackgroup.tracks:
		raise ValueError(f"Track {avbutils.format_track_label(track)} not in composition")
	
	component = track.component
	
	# Unwind component until we get to the actual thing
	while not isinstance(component, avb.components.Clip):
	
		# Sequence? Find component at time
		if isinstance(component, avb.components.Sequence):
			component,_ = component.nearest_component_at_time(offset)
		
		# Trackgrounp (TrackEffect, etc)?  Get relevant track from inner trackgroup
		elif isinstance(component, avb.trackgroups.TrackGroup):

			for t in component.tracks:
				try:
					component = get_component_from_track(component, t, offset)
				except ValueError:
					continue

	#		raise ValueError(f"Track not found: {avbutils.format_track_label(track)} not in {component}")
	
	return component



def resolve_mob(composition:avb.trackgroups.Composition, track:avb.trackgroups.Track, offset:int=0) -> tuple[avb.trackgroups.Composition, int]:
	"""Get next mob in the chain, and the frame offset in that mob's edit rate"""

	if not offset < composition.length:
		pass
		#raise ValueError(f"Offset ({offset}) cannot be greater than the composition length ({composition.length})")
	
	try:
		component = get_component_from_track(composition, track, offset)
	except Exception as e:
		print("JRG",e)
		exit()

	if not isinstance(component, avb.components.SourceClip):
		print("Got", component)
		raise StopIteration
	elif component.mob_id.Data1 == 0:
		#print("Component references", component.mob_id.Data1)
		raise StopIteration
	
	resolved_mob = composition.root.content.find_by_mob_id(component.mob_id)

	resolved_track = None
	for t in resolved_mob.tracks:
		if t.media_kind == track.media_kind and t.index == component.track_id:
			resolved_track = t
	if resolved_track is None:
		raise ValueError("No corresponding track")
		

	# SourceClip.start_time refers to the "parent" mob edit units (the one from which we're resolving).
	# Once a mob is resolved from the SourceClip, convert everything to the resolved mob's edit units
	# NOTE: Verify rounding is the way to go here
	#offset = offset + component.start_time
	offset = round((offset + component.start_time) * (resolved_mob.edit_rate / composition.edit_rate))

	return resolved_mob, resolved_track, offset
	
	




###########
###########
###########

import dataclasses


@dataclasses.dataclass(frozen=True)
class MobStack:
	stack: list[avb.trackgroups.Composition]

@dataclasses.dataclass(frozen=True)
class MasterclipStack:

	mastermob:avb.trackgroups.Composition
	tracks:dict[avb.trackgroups.Track, MobStack]


	
def process_bin(bin_path:PathLike):
	
	with avb.open(bin_path) as bin_handle:

		mob_stack:list[MasterclipStack] = []

		for bin_item in filter(bin_item_is_masterclip, bin_handle.content.items):
		#	print(bin_item.mob.usage_code, avbutils.format_track_labels(bin_item.mob.tracks), "\t", bin_item.mob.name))
			test_mob = bin_item.mob
			offset = 0
#			track=next(iter(mob.tracks))

			mobs_per_track:dict[avb.trackgroups.Track, MobStack] = dict()

			print(test_mob.name, f"({avbutils.format_track_labels(test_mob.tracks)})")

			for test_track in test_mob.tracks:
				new_mob = test_mob
				new_track = test_track
				resolved_mobs = list()
				while True:
					print("  - ", avbutils.format_track_label(new_track),new_mob, offset, new_mob.edit_rate, f"({avbutils.format_track_labels(new_mob.tracks)})")
					try:
						new_mob, new_track,offset = resolve_mob(new_mob, new_track, offset)
					except StopIteration:
						break
					else:
						resolved_mobs.append(new_mob)
				
				if resolved_mobs:
					mobs_per_track[test_track]=MobStack(resolved_mobs)
				
			if mobs_per_track:
				mob_stack.append(MasterclipStack(
					mastermob=test_mob,
					tracks=mobs_per_track
				))
				

				print("")
			
			print(mob_stack)
			#exit()




def bin_item_is_masterclip(bin_item:avb.bin.BinItem) -> bool:
	"""Bin item is a masterclip"""

	return avbutils.composition_is_masterclip(bin_item.mob)

def get_bin_paths(user_paths:list[PathLike]) -> typing.Generator[pathlib.Path, None, None]:
	"""Get bin paths from a list of file or folder paths"""

	for user_path in {pathlib.Path(u) for u in user_paths}:
		
		if user_path.is_dir():
			yield from (p for p in user_path.rglob("*.avb") if not p.name.startswith("."))
		elif user_path.is_file():
			yield user_path

	
if __name__ == "__main__":

	if not len(sys.argv) > 1:
		sys.exit(f"Usage: {pathlib.Path(__file__).name} bin_path.avb")
	
	for bin_path in get_bin_paths(sys.argv[1:]):
		process_bin(bin_path)
	
