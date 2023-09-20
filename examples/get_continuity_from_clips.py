import sys, pathlib, dataclasses
import avb
import avbutils
from timecode import Timecode, TimecodeRange

USAGE = f"Usage: {__file__} path/to/bins"

@dataclasses.dataclass
class ContinuitySceneInfo:
	"""Continuity info for an individual scene"""

	scene_number:str
	"""The scene numbeer (eg `Sc 032`)"""

	duration:Timecode
	"""Duration of the scene"""

	description:str
	"""Description of the scene"""

	location:str=""
	"""Location in which the scene takes place"""

def timecode_as_duration(timecode:Timecode) -> str:
	"""Format the timecode as a string without leading zeroes"""

	return "-" if timecode.is_negative else "" + str(timecode).lstrip("0:")

def is_masterclip(component:avb.components.Component) -> bool:
	"""Is a component a masterclip?"""
	
	return isinstance(component, avb.trackgroups.Composition) and component.mob_type == "MasterMob"

def is_continuity_sequence(comp:avb.trackgroups.Composition) -> bool:
	"""Determine if we're interested in this or not"""

	return comp.name.lower().endswith("continuity")

def is_intended_for_continuity(comp:avb.components.Component) -> bool:
	"""Determine if this continuity clip is meant to be included or not (so we can exclude things like head/tail leaders)"""

	# Look for text in bin column "Ignore In List"
	return not bool(comp.attributes.get("_USER").get("Ignore In List", "").strip())

def get_continuity_tracks_from_timeline(sequence:avb.trackgroups.Composition) -> list[avb.trackgroups.Track]:
	"""Choose the appropriate track in which the continuity clips reside"""

	# Looking for a video track (media_kind="picture") with the custom name "Continuity" (track.attributes.get("_COMMENT") == "Continuity")

	return [t for t in sequence.tracks if t.media_kind == "picture" and hasattr(t,"attributes") and t.attributes.get("_COMMENT","").lower() == "continuity"]

	# ALT: Return top-most video track
	return sorted([t for t in sequence.tracks if t.media_kind == "picture"], key=lambda t: t.index)[-1]

def get_continuity_subclips_from_sequence(sequence:avb.components.Sequence) -> list[avb.components.Component]:

	# NOTE: sequence.components[1:-1]  uhhh... doesn't work
	return list(sequence.components)[1:-1]

def matchback_sourceclip(source_clip:avb.components.SourceClip, bin_handle:avb.file.AVBFile) -> avb.components.Component:

	return bin_handle.content.find_by_mob_id(source_clip.mob_id)

def get_continuity_for_timeline(timeline:avb.trackgroups.Composition, bin_handle) -> list[ContinuitySceneInfo]:

	continuity_tracks = get_continuity_tracks_from_timeline(timeline)
	if len(continuity_tracks) != 1:
		raise ValueError(f"Found {len(continuity_tracks)} continuity tracks")
	continuity_track = continuity_tracks[0]

	continuity_sequence = continuity_track.component
	continuity_subclips = get_continuity_subclips_from_sequence(continuity_sequence)

	timeline_continuity:list[ContinuitySceneInfo] = list()

	for continuity_subclip in continuity_subclips:

		continuity_masterclip = matchback_sourceclip(continuity_subclip, bin_handle)
		
		# Need to do a recursive matchback thing, but for now we know there won't be a big heirarchy
		if not is_masterclip(continuity_masterclip):
			print(f"** Skipping {continuity_masterclip}")
			continue

		if not is_intended_for_continuity(continuity_masterclip):
			continue

		timeline_continuity.append(ContinuitySceneInfo(
			scene_number=continuity_masterclip.name or "Sc ???",
			duration=Timecode(continuity_subclip.length, rate=round(continuity_subclip.edit_rate)),
			description=continuity_masterclip.attributes.get("_USER").get("Comments","-"),
			location=continuity_masterclip.attributes.get("_USER").get("Location","-")
		))
	
	return timeline_continuity

def print_timeline_pretty(timeline:avb.trackgroups.Composition, continuity_scenes:list[ContinuitySceneInfo]):

	print(f"{timeline.name}:")
	
	timeline_trt = Timecode(0, rate=round(timeline.edit_rate))

	for continuity_scene in continuity_scenes:
		print(f" - {continuity_scene.scene_number.ljust(20)}{timecode_as_duration(continuity_scene.duration).rjust(11)}      {continuity_scene.description}")
		timeline_trt += continuity_scene.duration
	
	print(f"Reel TRT: {timecode_as_duration(timeline_trt)}")

def print_timeline_tsv(timeline:avb.trackgroups.Composition, continuity_scenes:list[ContinuitySceneInfo]):

	print(f"{timeline.name}:")
	
	timeline_trt = Timecode(0, rate=round(timeline.edit_rate))

	for continuity_scene in continuity_scenes:

		print('\t'.join([
			continuity_scene.scene_number,
			timecode_as_duration(continuity_scene.duration),
			continuity_scene.description
		]))

		timeline_trt += continuity_scene.duration
	
	print(f"Reel TRT: {timecode_as_duration(timeline_trt)}")


def get_continuity_for_all_reels_in_bin(bin_path:str):

	print(f"Opening bin {pathlib.Path(bin_path).name}...")

	master_trt = Timecode(0, rate=24)

	with avb.open(bin_path) as bin_handle:

		print("Finding continuity sequences...")

		timelines = sorted([seq for seq in avbutils.get_sequences_from_bin(bin_handle.content) if is_continuity_sequence(seq)],key=lambda x: avbutils.human_sort(x.name))

		for timeline in timelines:
			
			continuity_scenes = get_continuity_for_timeline(timeline, bin_handle)
			
			print("")
			#print_timeline_pretty(timeline, continuity_scenes)
			print_timeline_tsv(timeline, continuity_scenes)
			print("")
			
			master_trt += sum(c.duration for c in continuity_scenes)

	print(f"Total Feature Runtime: {timecode_as_duration(master_trt)}")
	print("")

if __name__ == "__main__":
	
	if not len(sys.argv):
		sys.exit(USAGE)
	
	get_continuity_for_all_reels_in_bin(sys.argv[1])