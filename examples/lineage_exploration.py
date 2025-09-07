"""
For a given frame in a given track in a clip:

- Determine its timecode
- Determine its tape
- Resolve its metdata
"""

import sys
import avb, avbutils, timecode


def get_track_component_at_time(track, offset) -> tuple[avb.components.Component, int]:

	if isinstance(track.component, avb.components.Sequence):
		return track.component.nearest_component_at_time(offset)
	
	else:
		return track.component, 0


if __name__ == "__main__":

	if len(sys.argv) < 2:
		sys.exit("")
	
	with avb.open(sys.argv[1]) as bin_handle:

		bin_content = bin_handle.content
		
		offset_from_source = 0
		
		# Start with user-placed mob (GroupClip, SubClip, Masterclip, whathaveyou)
		user_comp = next(iter(i.mob for i in bin_content.items if i.user_placed))
		user_track = next(iter(avbutils.get_tracks_from_composition(user_comp)))
#		print(user_comp.name, avbutils.format_track_label(user_track))


		
		
		
		# Get SourceClip Reference
		src_clip, src_clip_offset = get_track_component_at_time(user_track,offset_from_source)
		offset_from_source += src_clip_offset # I thtink
		
#		print(src_clip)

		# Dereference SourceClip to get the SourceMob Composition of the clip
		# Note: source_mob.descriptor for video is a CDCIDescriptor (Codec Compression Info)
		source_mob = bin_content.find_by_mob_id(src_clip.mob_id)
		source_mob_track = next(avbutils.get_tracks_from_composition(source_mob, type=avbutils.TrackTypes(src_clip.media_kind), index=src_clip.track_id))
		source_mob_descriptor = source_mob.descriptor
#		print(source_mob.name, avbutils.format_track_label(source_mob_track))


		
		
		
		# From SourceClip, use start_time and track_index to get the appropriate tape mob reference
		tape_mob_clip, tape_mob_offset = get_track_component_at_time(source_mob_track, src_clip.start_time)
		offset_from_source += tape_mob_offset # I think

#		print(tape_mob_clip)

		# Dereference SourceClip to get the Tape Mob Composition of the source
		# Note: tape_mob.descriptor for tape is a TapeDescriptor
		tape_mob = bin_content.find_by_mob_id(tape_mob_clip.mob_id)
		tape_mob_track = next(avbutils.get_tracks_from_composition(tape_mob, type=avbutils.TrackTypes(tape_mob_clip.media_kind), index=tape_mob_clip.track_id))
		tape_descriptor = tape_mob.descriptor
		print(tape_mob.name, avbutils.format_track_label(tape_mob_track))
		print(tape_mob.property_data)
		
		# Here the tape mob composition, I think basically we get sound a picture laid out for anyhting belonging to this tape
		# Video SourceClips reference null mobs at this point, but sound seems to continue.  Did not see timecode here...?


		# Need to continue matchback to soundroll info tho, for audio
		#print(list(tape_mob_track.component.positions()))
		#print("Start at ", tape_mob_clip.start_time)
#		soundroll_mob_clip, soundroll_mob_offset = get_track_component_at_time(tape_mob_track, tape_mob_clip.start_time+1) #...?
#		offset_from_source += soundroll_mob_offset
#
#		soundroll_mob = bin_content.find_by_mob_id(soundroll_mob_clip.mob_id)
#		soundroll_mob_track = next(avbutils.get_tracks_from_composition(soundroll_mob, type=avbutils.TrackTypes(soundroll_mob_clip.media_kind), index=soundroll_mob_clip.track_id))
#		soundroll_descriptor = soundroll_mob.descriptor
#
#		tc, soundroll_mob_tc_offset = get_track_component_at_time(soundroll_mob.tracks[0], soundroll_mob_clip.start_time)
#		print(tc.property_data)

		
		
		try:
			tape_mob_timecode_track, offset = get_track_component_at_time(next(avbutils.get_tracks_from_composition(tape_mob, type=avbutils.TrackTypes.TIMECODE, index=1)), tape_mob_clip.start_time)
		except StopIteration:
			print("No timecode track")


		# Print summary

		timecode_range = timecode.TimecodeRange(
			start = timecode.Timecode(tape_mob_timecode_track.start + src_clip_offset, rate=round(src_clip.edit_rate)),
			duration=src_clip.length
		)
		
		print(f"Clip {user_comp.name} comes from tape {tape_mob.name}, {timecode_range} frames")
		print(f"Last online from {source_mob_descriptor.locator.last_known_volume_utf8}")

		print("")
