"""
Source Reference Chain
"""

import typing, enum
import timecode, avb
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
			raise ValueError("Composition does not appear to be a source mob:", comp)
		
		return cls.from_descriptor(comp.descriptor)
	
	@classmethod
	def from_descriptor(cls, descriptor:avb.essence.MediaDescriptor) -> "SourceMobRole":
		return cls(descriptor.mob_kind)
	
	def __str__(self) -> str:
		return self.name.replace("_"," ").title()

def resolve_base_component_from_component(component:avb.components.Component, offset:timecode.Timecode|int=0) -> tuple[avb.components.Component, timecode.Timecode]:
	"""Given a component, resolve base components from any "compound" components such as trackeffects or sequences"""

	if not isinstance(offset, timecode.Timecode):
		offset = offset = timecode.Timecode(offset, rate=round(component.edit_rate))

	# First ensure we're in the right rate
	if not offset.rate == round(component.edit_rate):
		#raise ValueError(f"{offset.rate=} does not equal {component.edit_rate=}")
		offset = offset.resample(rate=round(component.edit_rate))
	
	if isinstance(component, avb.components.Sequence):

		component, from_sequence_start = component.nearest_component_at_time(offset.frame_number)
		offset -= from_sequence_start

		if round(component.edit_rate) != offset.rate:

			offset.resample(round(component.edit_rate))

	elif isinstance(component, avb.trackgroups.EssenceGroup) or isinstance(component, avb.trackgroups.TrackEffect):
		if len(component.tracks) == 1:
			component, offset = resolve_base_component_from_component(component.tracks[0].component, offset)
		else:
			pass #??
#			print(f"LOOK: For {component}, Got {len(component.tracks)}  {avbutils.format_track_labels(component.tracks)}")
	
	elif isinstance(component, avb.trackgroups.Track) and "component" in component.property_data:
		component, offset = resolve_base_component_from_component(component.component, offset)
		# print("LOOK: Just an empty track on this fella")
	
#	else:
#		print(component)
	return component, offset


def source_references_for_component(component:avb.components.Component, offset:timecode.Timecode|int=0) -> typing.Generator[tuple[avb.components.SourceClip, timecode.Timecode], None, None]:
	"""Given a composition, resolve its source reference clips and relative offsets"""

	# -  Dig in and resolve the base component from any heirarchy goin' on (sequences, track effects, etc),
	#    adjusting for relative offsets/rates
	# -  Return the resolved component & adjusted offset if it points to a source mob

	if isinstance(offset, timecode.Timecode) and not offset.rate == round(component.edit_rate):
		offset = offset.resample(rate=round(component.edit_rate))
	else:
		offset = timecode.Timecode(offset, rate=round(component.edit_rate))

	component, offset = resolve_base_component_from_component(component, offset)
	
	while isinstance(component, avb.components.SourceClip) and component.track:
		
		yield component, offset
		component, offset = resolve_base_component_from_component(component.track.component, component.start_time + offset)

def file_references_for_component(component:avb.components.Component) -> typing.Generator[tuple[avb.components.SourceClip, timecode.Timecode], None, None]:
	"""Get the active file source mobs since the most recent physical source mob"""

	yield from filter(lambda source_clip: compositions.MobTypes.from_composition(source_clip[0].mob) == compositions.MobTypes.SOURCE_MOB and SourceMobRole.from_composition(source_clip[0].mob) == SourceMobRole.ESSENCE, source_references_for_component(component))

def physical_references_for_component(component:avb.components.Component) -> typing.Generator[tuple[avb.components.SourceClip, timecode.Timecode], None, None]:
	"""Get the active physical source mobs"""
	
	yield from filter(lambda source_clip: compositions.MobTypes.from_composition(source_clip[0].mob) == compositions.MobTypes.SOURCE_MOB and SourceMobRole.from_composition(source_clip[0].mob) != SourceMobRole.ESSENCE, source_references_for_component(component))

def physical_source_name_for_composition(composition:avb.trackgroups.Composition) -> str|None:

	track = primary_track_for_composition(composition)

	try:
		source_clip, _ = next(physical_references_for_component(track.component))
		return source_clip.mob.name
	except StopIteration:
		raise ValueError("No physical source")

def physical_source_type_for_composition(composition:avb.trackgroups.Composition) -> SourceMobRole:
	
	track = primary_track_for_composition(composition)

	try:
		source_clip, _ = next(physical_references_for_component(track.component))
		return SourceMobRole.from_composition(source_clip.mob)
	except StopIteration:
		raise ValueError("No physical source")
	

def primary_track_for_composition(composition:avb.trackgroups.Composition) -> avb.trackgroups.Track:
	"""Return the foremost track, for which to be used for source/codec info"""

	for track in composition.tracks:
		if timeline.TrackTypes.from_track(track) in (timeline.TrackTypes.PICTURE, timeline.TrackTypes.SOUND):
			return track
	
	raise ValueError("No primary tracks")

def composition_has_physical_source(composition:avb.trackgroups.Composition) -> bool:

	track = primary_track_for_composition(composition)
	
	try:
		next(physical_references_for_component(track.component))
	except StopIteration:
		return False
	else:
		return True