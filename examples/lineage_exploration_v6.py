"""
v3 method proves reliable
v4 refines v3
v5 focuses on using SourceClip as the "currency" rather than Compositions.
v6 consolidates what I learned from v5 into a MatchbackInfo thing
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

class MobLineage:

	def __init__(self, stack:list[avb.components.SourceClip]):
		self._stack = stack

	@classmethod
	def from_track_component(cls, component:avb.components.Component):

		src_stack = [resolve_root_component(component)]

		while True:
			try:
				component = matchback_sourceclip(src_stack[-1])
				
				if not isinstance(component, avb.components.SourceClip) or not component.mob:
					raise avbutils.IsAsMatchedBackAsCanBe
				
				src_stack.append(component)

			except avbutils.IsAsMatchedBackAsCanBe:
				break
		
		return cls(src_stack)
	
	@property
	def sources(self) ->  list[avb.components.SourceClip]:
		return self._stack
	
	@property
	def file_source(self) -> avb.components.SourceClip|None:

		for clip in self._stack:
			if avbutils.composition_is_source_mob(clip.mob) and avbutils.SourceMobRole.from_composition(clip.mob) == avbutils.SourceMobRole.ESSENCE:
				return clip
		
		return None
			
	@property
	def physical_source(self) -> avb.components.SourceClip|None:

		for clip in self._stack:
			if avbutils.composition_is_source_mob(clip.mob) and avbutils.SourceMobRole.from_composition(clip.mob) != avbutils.SourceMobRole.ESSENCE:
				return clip
		
		# Probaby actually: raise IncompleteMatchback exception or somethin
		return None
	
	def resolve_track(self, track_type:avbutils.TrackTypes, track_index:int) -> tuple[avb.trackgroups.Track, avb.components.SourceClip]|None:
		"""Return mob"""

		for clip in self._stack:
			for track in clip.mob.tracks:
				if track.index == track_index and avbutils.TrackTypes.from_track(track) == track_type:
					return track, clip
		
		return None

class CompositionMatchbackInfo:

	def __init__(self, composition:avb.trackgroups.Composition):

		self._composition = composition
	
	@property
	def composition(self) -> avb.trackgroups.Composition:
		return self._composition
	
	@property
	def primary_track(self) -> avb.trackgroups.Track:
		return next(iter(self.tracks.keys()))
	
	@property
	def tracks(self) -> dict[avb.trackgroups.Track, MobLineage]:

		track_lineage = dict()

		for track in self._composition.tracks:
			track_lineage[track] = MobLineage.from_track_component(track.component)

		return track_lineage
	
	@property
	def source_name(self) -> str:
		return self.tracks[self.primary_track].physical_source.mob.name



#################################
######## MATCHBACK FUNCS ########
#################################


def matchback_sourceclip(source_clip:avb.components.SourceClip, offset:int=0) -> avb.components.Component:
	"""Given a `SourceClip,` follow its reference to its source"""

	if not isinstance(source_clip, avb.components.SourceClip) or not source_clip.mob:
		raise avbutils.IsAsMatchedBackAsCanBe
	
	# From the referenced mob, find the referenced track
	try:
		matched_track = next(t for t in source_clip.mob.tracks if t.media_kind == source_clip.media_kind and t.index == source_clip.track_id)
	except StopIteration as e:
		raise ValueError(f"Could not find track {source_clip.media_kind=}{source_clip.track_id=} in mob {source_clip.mob} ({avbutils.format_track_labels(source_clip.mob.tracks)})") from e
	
	# From the referenced track, recover the referenced component at the referenced start_time
	return resolve_root_component(matched_track.component, offset=source_clip.start_time+offset) # TODO: Need to do the offset conversion thing still(?)

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

			for t in component.tracks:

				try:
					component = resolve_root_component(t, offset)
				except ValueError:
					continue
	
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

			for bin_item in bin_handle.content.items:

				bin_item_roles = avbutils.BinDisplayItemTypes.from_bin_item(bin_item)

				if not any(r in bin_item_roles for r in (avbutils.BinDisplayItemTypes.MASTER_CLIPS,)):
					continue

				mastermob = bin_item.mob
				info = CompositionMatchbackInfo(mastermob)

				print(f"{bin_item_roles}: {info.composition.name} ({avbutils.format_track_labels(info.tracks)})")
				
				try:
					primary_file_mob = info.tracks[info.primary_track].file_source
					primary_phys_mob = info.tracks[info.primary_track].physical_source
				except Exception as e:
					sys.exit(e)

				if not any([primary_file_mob, primary_phys_mob]):
					for mob in info.tracks[info.primary_track].sources:
						sys.exit(mob.mob)



				
				

	
				for track in info.tracks:
					primary_source_type = avbutils.SourceMobRole.from_composition(info.tracks[track].physical_source.mob)
					primary_source_name = info.tracks[track].physical_source.mob.name
					
					found_tc = info.tracks[track].resolve_track(track_type=avbutils.TrackTypes.TIMECODE, track_index=1)

					source_attributes = dict()
					for source in reversed(info.tracks[track].sources):
						source_attributes.update(source.mob.attributes)
					source_attributes.update(info.composition.attributes)
					#print(source_attributes)


					# Get the first track just so we gots sumn
					if found_tc:
						tc_trk, tc_src_clp = found_tc
						tc_cmp = resolve_root_component(tc_trk.component)
						
						import timecode
						parsed_tc = timecode.TimecodeRange(
							start=timecode.Timecode(tc_cmp.start + tc_src_clp.start_time, rate=round(tc_cmp.edit_rate)),
							duration = info.composition.length
						)
					else:
						parsed_tc = "00"
				
					print(f"{avbutils.format_track_label(track)}: {primary_source_type}: {primary_source_name}   {parsed_tc} {'\t'.join(f'{x}: {y}' for x,y in source_attributes.get('_USER',dict()).items() if y)}")
				
				print("---")