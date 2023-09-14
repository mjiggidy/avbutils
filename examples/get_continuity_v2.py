import sys, pathlib
import avb
import avbutils
from timecode import Timecode, TimecodeRange

USAGE = f"Usage: {__file__} path/to/bins"

def is_masterclip(component:avb.components.Component) -> bool:
	"""Is a component a masterclip?"""
	
	return isinstance(component, avb.trackgroups.Composition) and component.mob_type == "MasterMob"

def is_continuity_sequence(comp:avb.trackgroups.Composition) -> bool:
	"""Determine if we're interested in this or not"""

	return comp.name.lower().endswith("continuity")

def get_continuity_track_from_timeline(sequence:avb.trackgroups.Composition) -> avb.trackgroups.Track:

	# Track indices start at 1
	return sorted([t for t in sequence.tracks if t.media_kind == "picture"], key=lambda t: t.index)[-1]

def get_continuity_subclips_from_sequence(sequence:avb.components.Sequence) -> list[avb.components.Component]:

	# NOTE: sequence.components[1:-1]  uhhh... doesn't work
	return list(sequence.components)[1:-1]

def matchback_sourceclip(source_clip:avb.components.SourceClip, bin_handle:avb.file.AVBFile) -> avb.components.Component:

	return bin_handle.content.find_by_mob_id(source_clip.mob_id)

def get_continuity_for_timeline(timeline:avb.trackgroups.Composition, bin_handle):

	continuity_track = get_continuity_track_from_timeline(timeline)
	continuity_sequence = continuity_track.component
	continuity_subclips = get_continuity_subclips_from_sequence(continuity_sequence)

	for continuity_subclip in continuity_subclips:

		continuity_masterclip = matchback_sourceclip(continuity_subclip, bin_handle)
		
		# Need to do a recursive matchback thing, but for now we know there won't be a big heirarchy
		if not is_masterclip(continuity_masterclip):
			print(f"** Skipping {continuity_masterclip}")
			continue

		print(f"{continuity_masterclip.name.ljust(20)}{Timecode(continuity_subclip.length)}{' ' * 6}{continuity_masterclip.attributes.get('_USER').get('Comments','-')}")






def get_continuity_for_all_reels_in_bin(bin_path:str):

	print(f"Opening bin {pathlib.Path(bin_path).name}...")

	with avb.open(bin_path) as bin_handle:

		print("Finding continuity sequences...")

		timelines = sorted([seq for seq in avbutils.get_sequences_from_bin(bin_handle.content) if is_continuity_sequence(seq)],key=lambda x: avbutils.human_sort(x.name))

		for timeline in timelines:
			continuity_info = get_continuity_for_timeline(timeline, bin_handle)



		exit()

if __name__ == "__main__":
	
	if not len(sys.argv):
		sys.exit(USAGE)
	
	get_continuity_for_all_reels_in_bin(sys.argv[1])