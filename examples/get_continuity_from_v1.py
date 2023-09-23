import sys, pathlib
import avb
import avbutils
from timecode import Timecode, TimecodeRange

USAGE = f"Usage: {__file__} path/to/bins"

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
		latest_timeline:avb.trackgroups.Composition = sorted(avbutils.get_timelines_from_bin(bin_handle.content), key=lambda x: avbutils.human_sort(x.name))[-1]
		
		print(f"{latest_timeline.name} has {len(latest_timeline.tracks)} track(s)")

		# "Avid Sequence" is a Composition which contains tracks, each with a sequence component
		# So V1 would be the Sequence component of Track 1 Picture

		try:
			track_v1:avb.trackgroups.Track = list(avbutils.get_tracks_from_composition(latest_timeline, type=avbutils.TrackTypes.PICTURE, index=1))[0]
		except IndexError:
			raise RuntimeError(f"{latest_timeline.name}: Track V1 was expected, but not found.", file=sys.stderr)
		
		# With the desired track, get the track's *component*, which should be a linear avb.components.Sequence of all the clips in the track
		sequence_v1 = track_v1.component
		if not isinstance(sequence_v1, avb.components.Sequence):
			raise ValueError(f"{track_v1}: Expected a sequence, but got {sequence_v1}")
		
		tc_current = Timecode("02:00:00:00", rate=round(sequence_v1.edit_rate))

		for subclip in sequence_v1.components:

			# Sequences always start and end with zero-length filler we can ignore
			if subclip.length == 0:
				#print(f"skip {component}")
				continue

			# Here's the "record TC" based on how far along we are in the sequence, and the subclip's length
			tc_record = TimecodeRange(
				start=tc_current,
				duration=Timecode(subclip.length, rate=round(subclip.edit_rate))
			)

			# SKIPS BEFORE MATCHBACK

			# Transitions
			# Transitions overlap the *previous* clip in the sequence, indicating we move back (to the left in the timeline) the duration of the sequence and begin the *next* clip *there*
			# So, also worth knowing, the NEXT subclip will have a duration of it's "usual" in/out points, *plus* the transition on the beginning of it
			# ...if that makes any sense.
			if isinstance(subclip, avb.trackgroups.TransitionEffect):
				print(f"{subclip.class_id.decode()}:\tTransition Effect ({tc_record.duration} {subclip.left_length=}\t {subclip.right_length=} {subclip.cutpoint=})")
				# TODO: CHECK ALL THIS REAL GOOD
				tc_current -= tc_record.duration
				continue
			
			# Filler
			# Can't matchback this fella anyway
			# TODO: Maybe pass this through in `avbutils.matchback_to_masterclip()`
			elif isinstance(subclip, avb.components.Filler):
				print(f"{subclip.class_id.decode()}:\t{tc_record.start}   ({tc_record.duration})")
				tc_current += tc_record.duration
				continue

			# NOTE: For now, handling things that `avbutils.matchback_to_masterclip()` gave up on
			if isinstance(subclip, avb.trackgroups.TrackEffect):
				print(f"{subclip.class_id.decode()}:\t{tc_record.start} ({tc_record.duration})\t{subclip}")
				tc_current += tc_record.duration
				continue
			

			# Match back until we have the masterclip
			masterclip = avbutils.matchback_to_masterclip(subclip)
			try:
				print_masterclip_info(masterclip, duration=tc_record, kind=subclip.class_id.decode())
			except Exception as e:
				print(f"{masterclip}: {e}")

			# Print the info
			tc_current += tc_record.duration

	print(f"End of reel: {tc_current}")
			

		
if __name__ == "__main__":

	if not len(sys.argv):
		sys.exit(USAGE)
	
	for bin_path in sys.argv[1:]:
		do_bin_good_and_nice(bin_path)