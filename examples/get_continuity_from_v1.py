import sys, pathlib
import avb
import avbutils
from timecode import Timecode, TimecodeRange

USAGE = f"Usage: {__file__} path/to/bins"

"""

Notes:

Groupclip?  Selected Track -> Component

Trackgroup? Track (media_kind=picture) -> Component

SourceClip? Lookup MobID

Composition? GOTO Trackgroup, or usagecode is masterclip?

Sequence?  Get the list of components (may contain filler, source clips, or something else)

"""

def matchback_groupclip(group:avb.trackgroups.Selector, selected_track_index:int|None=None) -> avb.components.Component:
	"""Matchback a groupclip"""

	# Groupclip seems to be a TrackGroup with a `selected` property pointing to the active camera
	selected_track = group.tracks[selected_track_index if selected_track_index is not None else group.selected]
	return matchback_track(selected_track)

def matchback_trackgroup(track_group:avb.trackgroups.TrackGroup, media_kind:str="picture") -> avb.components.Component:

	filtered_tracks = [t for t in track_group.tracks if t.media_kind == media_kind]

	if len(filtered_tracks) != 1:
		return f"{track_group}: Got {filtered_tracks}"

	return matchback_track(filtered_tracks[0])

def matchback_track(track:avb.trackgroups.Track) -> avb.components.Component:
	"""Get the component of a Track"""

	return track.component

def matchback_sequence(sequence:avb.components.Sequence) -> avb.components.Component:
	"""Get components from a sequence"""
	
	# Sequences start and end with filler
	# Probably want to do a "get component at location" thing here

	if len(sequence.components) > 3:
		return f"Sequence has {len(sequence.components)} components: {sequence.components}"

	#print(f" Returning {sequence.components[1]}")
	return sequence.components[1]

def matchback_sourceclip(source_clip:avb.components.SourceClip, bin_handle:avb.file.AVBFile) -> avb.components.Component:
	"""Resolve MOB for a given `SourceClip`"""

	return bin_handle.content.find_by_mob_id(source_clip.mob_id)

def get_video_track_from_composition(composition:avb.trackgroups.Composition, media_kind:str="picture", track_index:int=1) -> avb.components.Sequence:
	"""Get V1 by default"""

	for track in composition.tracks:
		if track.index == track_index and track.media_kind == media_kind:
			return track.component
	
	raise IndexError(f"No V{track_index} found in sequence")


def is_masterclip(component:avb.components.Component) -> bool:
	"""Is a component a masterclip?"""
	
	return isinstance(component, avb.trackgroups.Composition) and component.mob_type == "MasterMob"


def print_masterclip_info(masterclip:avb.trackgroups.Composition, duration:TimecodeRange, kind:str):
	"""Display info (temp?)"""

	scene_number = masterclip.attributes.get("_USER").get("Scene")
	take_number  = masterclip.attributes.get("_USER").get("Take")
	tape_name    = masterclip.attributes.get("_USER").get("TapeID")
	clip_name    = masterclip.name
	
	#sys.exit(daily_video_track_component_mob.name)
	print(f"{kind}:\t{duration.start}\tName: {str(clip_name).ljust(24)} Sc: {str(scene_number).ljust(16)} Tk: {str(take_number).ljust(8)} Tape: {str(tape_name).ljust(24)} Dur: {duration.duration}")



def do_bin_good_and_nice(bin_path:str):

	with avb.open(bin_path) as bin_handle:
		latest_sequence:avb.trackgroups.Composition = sorted(avbutils.get_sequences_from_bin(bin_handle.content), key=lambda x: avbutils.human_sort(x.name))[-1]
		
		print(f"{latest_sequence.name} has {len(latest_sequence.tracks)} track(s)")

		# "Avid Sequence" is a Composition which contains tracks, each with a sequence component
		# So V1 would be the Sequence component of Track 1 Picture
		track_v1 = get_video_track_from_composition(latest_sequence)

		tc_current = Timecode("02:00:00:00", rate=round(track_v1.edit_rate))

		for component in track_v1.components:

			# Get the length of the most-parent-y component as it lives in the timeline
			og_class  = component.class_id.decode()
			og_rate   = component.edit_rate
			og_length = component.length

			if og_length == 0:
				#print(f"skip {component}")
				continue

			# Match back until we have the masterclip
			while not is_masterclip(component):

				if isinstance(component, avb.trackgroups.Composition):
					component = get_video_track_from_composition(component)

				if isinstance(component, avb.trackgroups.Selector):
					component = matchback_groupclip(component)

				elif isinstance(component, avb.trackgroups.TrackGroup):
					component = matchback_trackgroup(component)
				
				# Oooohh.... you know whaaaat.....
				elif isinstance(component, avb.trackgroups.Track):
					component = matchback_track(component)
				
				elif isinstance(component, avb.components.SourceClip):
					component = matchback_sourceclip(component, bin_handle)

				elif isinstance(component, avb.components.Sequence):
					component = matchback_sequence(component)

				elif isinstance(component, avb.components.Filler):
					break
				
				else:
					break

				#print(component)
				#input()
			
			#print(f"!!! GOT MASTERCLIP {component}")

			tc_subclip = TimecodeRange(
				start=tc_current,
				duration=Timecode(og_length, rate=round(og_rate))
			)

			if isinstance(component, avb.components.Filler):
				print(f"Filler {component.length}")
				tc_current += og_length
				continue

			elif not isinstance(component, avb.trackgroups.Composition):
				print(f"**SKIP: {tc_subclip.start}\t{component} ]]")
				tc_current += og_length
				continue
			
			print_masterclip_info(component, duration=tc_subclip, kind=og_class)
			tc_current += tc_subclip.duration

			

		
if __name__ == "__main__":
    
	if not len(sys.argv):
		sys.exit(USAGE)
	
	for bin_path in sys.argv[1:]:
		do_bin_good_and_nice(bin_path)