import sys, pathlib
import avb
import avbutils
from timecode import Timecode, TimecodeRange

USAGE = f"Usage: {__file__} path/to/bins"

def print_subclip_info(subclip:avb.trackgroups.Composition, masterclip:avb.trackgroups.Composition) -> str:
	"""Display the info of a subclip"""

	sourcemob = avbutils.matchback_to_sourcemob(masterclip)

	tc_masterclip = TimecodeRange(
		start    = Timecode(avbutils.get_timecode_range_for_composition(sourcemob).start, rate=round(sourcemob.edit_rate)),
		duration = masterclip.length
	)

	tc_subclip = TimecodeRange(
		start    = tc_masterclip.start + subclip.start_time,
		duration = subclip.length
	)

	clip_name    = masterclip.name
	tape_name    = sourcemob.name
	scene_number = masterclip.attributes.get("_USER").get("Scene")
	take_number  = masterclip.attributes.get("_USER").get("Take")

	return f"{tape_name}\t{tc_subclip.start} - {tc_subclip.end} ({str(tc_subclip.duration).lstrip('0:')})\tName: {clip_name}   Sc: {scene_number}   Tk: {take_number}"



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
		tc_current = avbutils.get_timecode_range_for_composition(latest_timeline).start

		# "Avid Sequence" is a Composition, which is a type of Track Group.  Each track in a track group has a `component` property that points to something like a Sequence (for picture or audio),
		# or a Timecode component or something like that.  So V1 would be the Sequence component of Track 1 Picture.
		try:
			track_v1:avb.trackgroups.Track = list(avbutils.get_tracks_from_composition(latest_timeline, type=avbutils.TrackTypes.PICTURE, index=1))[0]
		except IndexError:
			raise RuntimeError(f"{latest_timeline.name}: Track V1 was expected, but not found.", file=sys.stderr)
		
		# With the desired track, get the track's *component*, which should be a linear avb.components.Sequence of all the clips in the track
		sequence_v1 = track_v1.component
		if not isinstance(sequence_v1, avb.components.Sequence):
			raise ValueError(f"{track_v1}: Expected a sequence, but got {sequence_v1}")

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
				print(f"{subclip.class_id.decode().ljust(11)}Transition Effect ({tc_record.duration} {subclip.left_length=}\t {subclip.right_length=} {subclip.cutpoint=})")
				# TODO: CHECK ALL THIS REAL GOOD
				tc_current -= tc_record.duration
				continue
			
			# Filler
			# Can't matchback this fella anyway
			# TODO: Maybe pass this through in `avbutils.matchback_to_masterclip()`
			elif isinstance(subclip, avb.components.Filler):
				print(f"{subclip.class_id.decode().ljust(11)}\t{tc_record.start}   ({tc_record.duration})")
				tc_current += tc_record.duration
				continue

			# NOTE: For now, handling things that `avbutils.matchback_to_masterclip()` gave up on
			if isinstance(subclip, avb.trackgroups.TrackEffect):
				print(f"{subclip.class_id.decode().ljust(11)}{tc_record.start} ({tc_record.duration})\t{subclip}")
				tc_current += tc_record.duration
				continue

			# Let's collapse the multicam first if that's what we've got
			while isinstance(subclip, avb.trackgroups.Selector):
				subclip = avbutils.matchback_groupclip(subclip)
			

			# Match back until we have the masterclip
			masterclip = avbutils.matchback_to_masterclip(subclip)
			try:
				#print_masterclip_info(masterclip, duration=tc_record, kind=subclip.class_id.decode())
				try:
					subclip_info = print_subclip_info(subclip=subclip, masterclip=masterclip)
				except Exception as e:
					subclip_info = f"{subclip}: {e}"
				print(tc_current, "    ", subclip_info)
			except Exception as e:
				print(f"{subclip}: {e}")

			# Print the info
			tc_current += tc_record.duration

	print(f"End of reel: {tc_current}")
			

		
if __name__ == "__main__":

	if not len(sys.argv):
		sys.exit(USAGE)
	
	for bin_path in sys.argv[1:]:
		do_bin_good_and_nice(bin_path)