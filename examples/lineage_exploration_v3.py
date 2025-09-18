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

	# TODO: Do I really need to be passing the trackgroup and doing this check?  What was that for?  Was it important?  Why did I do this?  Why do I do anything?  Is what I'm doing worth it?  What am I even trying to do?  What else can I do besides assistant editing?  I don't like working with tech people so I don't want to be an engineer again, but I'm not creative.  And I'm not good enoguh of a coder to code.  Unreal Engine is fun but I hear the game industry is no better than the film industry...
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
#		print("JRG",e)
		exit()

	if not isinstance(component, avb.components.SourceClip):
#		print("Got", component)
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
		raise ValueError(f"No corresponding track ({composition.media_kind=} {component.track_id=} {component=} {composition=}) (resolved_tracks={avbutils.format_track_labels(resolved_mob.tracks)})")
		

	# SourceClip.start_time refers to the "parent" mob edit units (the one from which we're resolving).
	# Once a mob is resolved from the SourceClip, convert everything to the resolved mob's edit units
	# NOTE: Verify rounding is the way to go here
	#offset = offset + component.start_time
	offset = round((offset + component.start_time) * (resolved_mob.edit_rate / composition.edit_rate))

	return resolved_mob, resolved_track, offset
	
	

###########
###########
###########

def analyze_masterclip_stack(stack:"MasterclipStack"):
	"""Okay"""

	
	print(stack.mastermob.name, "is a", type(stack.mastermob).__name__, "with tracks", avbutils.format_track_labels(stack.mastermob.tracks))

	track, track_stack = next(iter(stack.tracks.items()))
	link_type = track_stack.link_type()
	source_type = track_stack.source_type()
	source_name = track_stack.source_name()
	source_tc   = stack.get_timecode_range_for_track(track)

	print(f"{avbutils.format_track_label(track)} is {link_type} media from {source_type} {source_name}")

	latest_file_mob = next(track_stack.file_source_mobs())

	if isinstance(latest_file_mob.descriptor.locator, avb.misc.MSMLocator):
		
		last_volume = None
		
		for prop in ("last_known_volume_utf8", "last_known_volume"):
			last_volume = latest_file_mob.descriptor.locator.property_data.get(prop, None)
		
		if last_volume:
			print(f"It is imported to {last_volume}")
	
	print(f"Timecode is {source_tc}")
	

	

	#if link_type == "UME-linked":
	#	exit()

	#print(f"File mobs for {avbutils.format_track_label(track)}:")
	#for fm in track_stack.file_source_mobs():
#		print(" -", fm)
	
	#print(f"Physical mobs for {avbutils.format_track_label(track)}:")
	#for sm in track_stack.physical_source_mobs():
	#	print(" -", sm)






###########
###########
###########
	

def composition_is_file_source_mob(comp:avb.trackgroups.Composition) -> bool:

	return avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.SOURCE_MOB and \
	  isinstance(comp.descriptor, avb.essence.MediaFileDescriptor)

def composition_is_physical_source_mob(comp:avb.trackgroups.Composition) -> bool:
	
	return avbutils.MobTypes.from_composition(comp) == avbutils.MobTypes.SOURCE_MOB and \
	  not isinstance(comp.descriptor, avb.essence.MediaFileDescriptor)

import dataclasses


@dataclasses.dataclass(frozen=True)
class TrackMobStack:
	stack: list[avb.trackgroups.Composition]

	def source_mobs(self) -> list[avb.trackgroups.Composition]:
		"""Get source mobs for a given track"""

		return self.stack
	
	def file_source_mobs(self) -> typing.Iterator[avb.trackgroups.Composition]:
		return filter(composition_is_file_source_mob, self.stack)
	
	def physical_source_mobs(self) -> typing.Iterator[avb.trackgroups.Composition]:
		return filter(composition_is_physical_source_mob, self.stack)

	def link_type(self):
		
		latest_file_mob = next(self.file_source_mobs())

		descriptors = []

		# TODO: Need to unwrap MultiDescriptor locators better/recursively
		# Fast for now
		descriptor = latest_file_mob.descriptor
		if isinstance(latest_file_mob.descriptor, avb.essence.MultiDescriptor):
			for d in descriptor.descriptors:
				descriptors.append(d)
		
		else:
			descriptors.append(descriptor)

		for d in descriptors:

			# Considering linked if ANY are linked

			if isinstance(d, avb.essence.MediaFileDescriptor) \
			  and isinstance(d.locator, avb.misc.MSMLocator) \
			  and isinstance(d.physical_media, avb.essence.MediaDescriptor) \
			  and isinstance(d.physical_media.locator, avb.misc.FileLocator):
				return "UME-linked"
		else:
			return "Managed"
		
	def get_timecode(self) -> avb.components.Timecode:

		for mob in self.stack:
			for track in mob.tracks:
				component = get_component_from_track(mob, track)
				if isinstance(component, avb.components.Timecode):
					print(f"Got timecode from {avbutils.format_track_label(track)}, source mob {self.stack.index(mob)} ({mob=}) ({avbutils.format_track_labels(mob.tracks)})")
					return component
				
		raise StopIteration
		

	
	def source_type(self):

		try:
			oldest_physical_mob = list(self.physical_source_mobs())[-1]
		except IndexError:
			return "NONE??"


		if "locator" in oldest_physical_mob.descriptor.property_data and isinstance(oldest_physical_mob.descriptor.locator, avb.misc.FileLocator):
			return "Source File"
		else:
			return type(oldest_physical_mob.descriptor).__name__
		
	def source_name(self):

		try:
			oldest_physical_mob = list(self.physical_source_mobs())[-1]
		except IndexError:
			return "NONE????"
		
		if "locator" in oldest_physical_mob.descriptor.property_data and isinstance(oldest_physical_mob.descriptor.locator, avb.misc.FileLocator):
			
			# NOTE: Seems like it could be in any of these
			for prop in ("path_utf8","path2_utf8","path_posix","path"):
				src_path = oldest_physical_mob.descriptor.locator.property_data.get(prop,None)
				if src_path:
					#print(type(src_path), src_path, prop)
					return src_path
			
			#raise ValueError("No source file")
			# NOTE: Need to figure out what to do here
			return ""
			
		else:
			return oldest_physical_mob.name


@dataclasses.dataclass(frozen=True)
class MasterclipStack:

	mastermob:avb.trackgroups.Composition
	tracks:dict[avb.trackgroups.Track, TrackMobStack]

	def get_timecode_range_for_track(self, track:avb.trackgroups.Track):

		import timecode

		tc = self.tracks[track].get_timecode()

		return timecode.TimecodeRange(
			start = timecode.Timecode(tc.start, rate=round(tc.edit_rate)),
			duration = self.mastermob.length
		)





	
def process_bin(bin_path:PathLike):
	
	with avb.open(bin_path) as bin_handle:

		mob_stack:list[MasterclipStack] = []

		for bin_item in filter(bin_item_is_masterclip, bin_handle.content.items):
		#	print(bin_item.mob.usage_code, avbutils.format_track_labels(bin_item.mob.tracks), "\t", bin_item.mob.name))
			test_mob = bin_item.mob
			offset = 0
#			track=next(iter(mob.tracks))

			mobs_per_track:dict[avb.trackgroups.Track, TrackMobStack] = dict()

#			print(test_mob.name, f"({avbutils.format_track_labels(test_mob.tracks)})")

			for test_track in test_mob.tracks:
				new_mob = test_mob
				new_track = test_track
				resolved_mobs = list()
				while True:
#					print("  - ", avbutils.format_track_label(new_track),new_mob, offset, new_mob.edit_rate, f"({avbutils.format_track_labels(new_mob.tracks)})")
					try:
						new_mob, new_track,offset = resolve_mob(new_mob, new_track, offset)
					except StopIteration:
						break
					else:
						resolved_mobs.append(new_mob)
				
				if resolved_mobs:
					mobs_per_track[test_track]=TrackMobStack(resolved_mobs)
				
			if mobs_per_track:
				mob_stack.append(MasterclipStack(
					mastermob=test_mob,
					tracks=mobs_per_track
				))
				

#				print("")
			
			analyze_masterclip_stack(mob_stack[-1])
			print("---")
	




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
		print(bin_path)
		process_bin(bin_path)
		#exit()
	
