import enum
import avb
from . import compositions, timeline

class StopMatchback(StopIteration):
	"""Track cannot be resolved further"""

class FillerDuringMatchback(ValueError):
	"""Encountered unexpected Filler while matching back"""

class SourceMobRole(enum.Enum):
	"""
	Kinds of descriptors, maps to the integer values from `avb.essence.MediaDescrirptor.mob_kind`
	I might call this a "role" but whatever
	"""

	ESSENCE  = 1
	"""Traditional, managed OP-Atom MXF media essence"""
	TAPE        = 2
	"""Tape source"""
	FILM        = 3
	"""Film source"""
	SOUNDROLL   = 4
	"""Traditional soundroll source"""
	SOURCE_FILE = 5
	"""Imported file source"""

	@classmethod
	def from_composition(cls, comp: avb.trackgroups.Composition) -> "SourceMobRole":
		
		if compositions.MobTypes.from_composition(comp) != compositions.MobTypes.SOURCE_MOB or comp.descriptor is None:
			raise ValueError("Composition does not appear to be a source mob")
		
		return cls.from_descriptor(comp.descriptor)
	
	@classmethod
	def from_descriptor(cls, descriptor:avb.essence.MediaDescriptor) -> "SourceMobRole":
		return cls(descriptor.mob_kind)
	
	def __str__(self) -> str:
		return self.name.replace("_"," ").title()
	

class MobStack:
	"""Stack of resolved mobs"""

	def __init__(self, mob_stack:list[avb.trackgroups.Composition]):

		self._stack = mob_stack
	
	@classmethod
	def from_composition(cls, composition:avb.trackgroups.Composition, track:avb.trackgroups.Track, frame_offset:int):

		comps = []

		last_component_offset = 0

		while True:
			comps.append(composition)
			try:
				composition, track, last_component_offset = cls._get_mob_from_track_at_offset(track, frame_offset + last_component_offset+1) # NOTE: WHY THE +1 NEEDED ARGH
			except StopMatchback:
				break
			except FillerDuringMatchback:
				break
		
		return cls(comps)
	

	@classmethod
	def _get_mob_from_track_at_offset(cls, track:avb.trackgroups.Track, offset:int) -> tuple[avb.trackgroups.Composition, avb.trackgroups.Track, int]:

		# Track contains a component that points to another mob
		# For a master/source mob, typically resolves to a Sequence -> SourceClip
		# Source clip references track_id and start_time, len from the mob it points to
		
		component = track.component

		while isinstance(component, avb.trackgroups.Selector):
			component = next(t for t in timeline.get_tracks_from_composition(component, timeline.TrackTypes.PICTURE, component.selected)).component

		while isinstance(component, avb.trackgroups.TrackEffect) or isinstance(component, avb.trackgroups.TimeWarp) or isinstance(component, avb.trackgroups.TransitionEffect):
			
			# Unwrap TrackEffect
			# track = next(filter(lambda t: t.media_kind == track.media_kind and t.index == track.index, component.tracks))
			# NOTE:  ^^^ I Feel like this up here is the way to go, but PVOL, for example, has a child track that's always index=1
			track = next(filter(lambda t: t.media_kind == track.media_kind, component.tracks))
			
			component = track.component
		
		if isinstance(component, avb.components.Sequence):
			component, component_offset = component.nearest_component_at_time(offset)
			# NOTE: What to do about component_offset? ...add to offset or something?

		if isinstance(component, avb.components.Filler):
			raise FillerDuringMatchback

		if isinstance(component, avb.components.SourceClip) and component.track_id == 0:
			raise StopMatchback
		
		if isinstance(component, avb.components.Timecode):
			raise StopMatchback

		resolved_mob = track.root.content.find_by_mob_id(component.mob_id)
		resolved_track = next(t for t in resolved_mob.tracks if t.media_kind == track.media_kind and t.index == component.track_id)

		# NOTE: Need to think about offset
		return resolved_mob, resolved_track, component.start_time

	@property
	def source_mobs(self) -> list[avb.trackgroups.Composition]:
		return list(filter(compositions.composition_is_source_mob, self._stack))
	
	@property
	def source_name(self):
		"""Identify"""
		
		# Traditional media
		return self.source_mobs[-1].name
	
	@property
	def has_managed_media(self) -> bool:
		"""Does this mob reference managed media"""

		desc = self.essence_descriptor

		if isinstance(desc, avb.essence.MultiDescriptor):
			desc = desc.descriptors
		else:
			desc = [desc]
		
		for d in desc:
			if isinstance(d.locator, avb.misc.MSMLocator) and (d.physical_media is None or isinstance(d.physical_media.locator, avb.misc.URLLocator)):
				return True
		
		return False
			
	@property
	def has_linked_media(self) -> bool:
		"""Does this mob reference UME-linked media"""

		desc = self.essence_descriptor

		if isinstance(desc, avb.essence.MultiDescriptor):
			desc = desc.descriptors
		else:
			desc = [desc]
		
		for d in desc:
			if isinstance(d.locator, avb.misc.MSMLocator) and d.physical_media and isinstance(d.physical_media.locator, avb.misc.FileLocator):
				return True
		
		return False
	
	@property
	def essence_descriptor(self) -> avb.essence.MediaDescriptor:

		desc = self.source_mobs[0].descriptor

		if not isinstance(desc, avb.essence.MediaFileDescriptor):
			raise ValueError("Did not find expected essence descriptor")
		
		return desc

	@property
	def link_type(self):

		essence_mob = self.source_mobs[0]
		mob_role = SourceMobRole.from_composition(essence_mob)

		if not mob_role == SourceMobRole.ESSENCE:
			raise ValueError(f"Not an essence mob")
		
		essence_has_file_reference = self._descriptor_has_file_reference(essence_mob.descriptor)

		source_has_file_reference  = (SourceMobRole.from_composition(self.source_mobs[1]) == SourceMobRole.SOURCE_FILE) and \
		  self._descriptor_has_file_reference(self.source_mobs[1].descriptor)

		if essence_has_file_reference and source_has_file_reference:
			return "UME Linked"
		
		elif source_has_file_reference:
			return "Hard Imported"
		
		elif essence_has_file_reference:
			raise ValueError("Essence references file but source does not")
		
		else:
			return "Physical Media Referred"

	@staticmethod
	def _descriptor_has_file_reference(descriptor: avb.essence.MediaDescriptor) -> bool:
		"""A given descriptor references an external file"""

		if isinstance(descriptor, avb.essence.MultiDescriptor):
			descriptors = descriptor.descriptors
		
		else:
			descriptors = [descriptor]

		for d in descriptors:
			
			if isinstance(d.locator, avb.misc.FileLocator):
				return True
			
			elif d.physical_media and isinstance(d.physical_media.locator, avb.misc.FileLocator):
				return True
			
		return False
