import sys, pathlib
import avb
import trtlib
from timecode import Timecode

USAGE = f"Usage: {__file__} path/to/bins"

def get_video_track_from_sequence(seq:avb.trackgroups.Composition, track_index:int=1) -> avb.components.Sequence:
	"""Get V1 by default"""

	for track in seq.tracks:
		if track.index == 1 and track.media_kind == "picture":
			return track.component
	
	raise IndexError(f"No V{track_index} found in sequence")


def do_bin_good_and_nice(bin_path:str):

	with avb.open(bin_path) as bin_handle:
		latest_sequence:avb.trackgroups.Composition = sorted(trtlib.get_sequences_from_bin(bin_handle.content), key=lambda x: trtlib.human_sort(x.name))[0]
		
		print(f"{latest_sequence.name} has {len(latest_sequence.tracks)} track(s)")

		track_v1 = get_video_track_from_sequence(latest_sequence)

		# For Now: Just need Selectors (group clips)?
		groupclips = [x for x in track_v1.components if isinstance(x, avb.trackgroups.Selector)]
		print(f"V1 has {len(groupclips)} groupclips")

		for groupclip in groupclips:

			length = groupclip.length
			edit_rate = groupclip.edit_rate

			# Group clip contains multiple Tracks and a "Selected" index for the one in use
			# Each track contains a component with a Mob ID that references subclips of the component masterclips
			# We look up the mob ID using the bin's find_by_mob_id() which gives us the Composition (master clip?? or maybe this is a subclip of a group_subclip... that might be what's going on)

			# Get the selected group track (camera A, camera B)
			group_selected_track:avb.trackgroups.Track = groupclip.tracks[groupclip.selected]

			# Get the component of that track, which is a `SourceClip` which will point to a subclip of a masterclip and any filler
			group_selected_sourceclip:avb.components.SourceClip = group_selected_track.component

			# Look up the `mob_id`` to get a reference to the actual subclip composition
			try:
				group_subclip_composition:avb.trackgroups.Composition = bin_handle.content.find_by_mob_id(group_selected_sourceclip.mob_id)
			except Exception as e:
				print(f"** Skip {groupclip}: {e}")
				continue
			
			# group_subclip Composition contains tracks
			# Picture tracks have a component of type "Sequence".
			# Here I'm collecting the sequence from each picture track in the group_subclip
			group_subclip_composition_tracks:list[avb.trackgroups.Track] = group_subclip_composition.tracks
			
			# Going go grab just the first picture track?
			group_subclip_composition_picture_track:avb.trackgroups.Track = [t for t in group_subclip_composition_tracks if t.media_kind == "picture"][0]

			group_subclip_composition_picture_sequence:avb.components.Sequence = group_subclip_composition_picture_track.component

			# Picture track component is a Sequence.
			# The Sequence has a list of source components
			# I've seen Filler and Source Clips here
			group_subclip_composition_picture_components:list[avb.utils.AVBObjectRef] = group_subclip_composition_picture_sequence.components
			
			# Filter out the dailies footage which is a `SourceClip` (Rather than Filler)
			group_subclip_composition_picture_daily:list[avb.components.SourceClip] = [c for c in group_subclip_composition_picture_components if isinstance(c, avb.components.SourceClip)][0]
			
			# Get the MOB ID of that daily
			daily_mob_id = group_subclip_composition_picture_daily.mob_id

			# This is the Master Clip (autosync of video and audio), I believe
			daily_mob:avb.trackgroups.Composition = bin_handle.content.find_by_mob_id(daily_mob_id)

			# Get the video of the sync clip
			daily_video_track = [t for t in daily_mob.tracks if t.media_kind == "picture"][0]
			
			# Get the source clip component of the video
			daily_video_track_component:avb.components.SourceClip = daily_video_track.component

			# This is the master mob!!!!!!!
			daily_video_track_component_mob:avb.trackgroups.Composition = bin_handle.content.find_by_mob_id(daily_video_track_component.mob_id)

			# Get the Scene!
			scene_number = daily_video_track_component_mob.attributes.get("_USER").get("Scene")
			take_number  = daily_video_track_component_mob.attributes.get("_USER").get("Take")
			tape_name    = daily_video_track_component_mob.attributes.get("_USER").get("TapeID")
			
			#sys.exit(daily_video_track_component_mob.name)
			print(f"Scn {scene_number}, Tk {take_number} ({tape_name})    -   {Timecode(length, rate=int(edit_rate))}")
			

		
if __name__ == "__main__":
    
	if not len(sys.argv):
		sys.exit(USAGE)
	
	for bin_path in sys.argv[1:]:
		do_bin_good_and_nice(bin_path)