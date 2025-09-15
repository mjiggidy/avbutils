import sys
import avb
from avbutils import mobstack, timeline

def get_test_clip_from_bin(bin_content:avb.bin.Bin) -> avb.trackgroups.Composition:

	import random

	return random.choice(list(bin_content.mastermobs()))

def get_test_track_from_clip(comp:avb.trackgroups.Composition) -> avb.trackgroups.Track:

	import random

	return next(t for t in comp.tracks)

if __name__ == "__main__":

	if not len(sys.argv) > 1:
		import pathlib
		sys.exit(f"Usage: {pathlib.Path(__file__).name} bin.avb")
	
	with avb.open(sys.argv[1]) as bin_handle:

		for clip in bin_handle.content.mastermobs():
			
			try:
				track = get_test_track_from_clip(clip)
				print(clip, timeline.format_track_label(track))
				stack = mobstack.MobStack.from_composition(clip, track, 0)

				print(clip.name, stack.link_type, stack.source_name)
			except Exception as e:
				print("*** ", e)