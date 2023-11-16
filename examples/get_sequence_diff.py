import sys, difflib, pprint
import avb, avbutils, deepdiff

def format_track_label(track:avb.trackgroups.Track) -> str:
	"""Format a track key such as V1 or A3"""

	return ("V" if track.media_kind == "picture" else "A") + str(track.index)

def compare_timelines(old_timeline:avb.trackgroups.Composition, new_timeline:avb.trackgroups.Composition):
	"""Compare and old timeline to a new one"""

	print(f"Comparing {new_timeline.name} since {old_timeline.name}...")

	# TODO: Just picture for testing
	old_tracks = {format_track_label(t): t for t in sorted(avbutils.get_tracks_from_composition(old_timeline, type=avbutils.TrackTypes.PICTURE), reverse=True, key=lambda t: t.index)}
	new_tracks = {format_track_label(t): t for t in sorted(avbutils.get_tracks_from_composition(new_timeline, type=avbutils.TrackTypes.PICTURE), reverse=True, key=lambda t: t.index)}

	print("Old tracks:")
	print([t for t in old_tracks])

	print("New tracks:")
	print([t for t in new_tracks])

	# TODO: Note added or removed tracks
	tracks_added = set(new_tracks.keys()) - set(old_tracks.keys())
	tracks_removed = set(old_tracks.keys()) - set(new_tracks.keys())

	for track_label, track_handle in new_tracks.items():

		if track_label in tracks_removed:
			print("Track removed: ", track_label)
			continue

		new_track_sequence = track_handle.component
		old_track_sequence = old_tracks.get(track_label).component
		
		if not isinstance(new_track_sequence, avb.components.Sequence):
			raise ValueError(f"Track {track_label} in {new_timeline.name} is not a Sequence as expected (it's a {type(new_track_sequence)})")
		elif not isinstance(old_track_sequence, avb.components.Sequence):
			raise ValueError(f"Track {track_label} in {old_timeline.name} is not a Sequence as expected (it's a {type(old_track_sequence)})")
		
		print(f"{track_label}:")

		#track_diff = difflib.SequenceMatcher(a=list(new_track_sequence.components), b=list(old_track_sequence.components))
		#print(list(track_diff.get_matching_blocks()))

		new_track_components = list(new_track_sequence.components)
		old_track_components = list(old_track_sequence.components)

#		print("New V7")
#		print(new_track_components)

#		print("Old V7")
#		print(old_track_components)
#		exit()

		diff = deepdiff.diff.DeepDiff(new_track_components, old_track_components)
		pprint.pprint(diff)




def compare_timelines_in_bin(avb_bin:avb.bin.Bin, sorting:avbutils.BinSorting=avbutils.BinSorting.NAME):
	"""Compare two timelines in a given bin"""

	timelines_all = sorted(avbutils.get_timelines_from_bin(avb_bin), key=avbutils.BinSorting.get_sort_lambda(sorting), reverse=True)

	if len(timelines_all) < 2:
		raise ValueError(f"Two or more timelines must be present in this bin to compare ({len(timelines_all)} found)")
	
	compare_timelines(*timelines_all[:2])

def main(paths_bins:list[str]):
	"""Compare two timelines in a given Avid bin, given one or more paths"""

	for path_bin in paths_bins:
		with avb.open(path_bin) as handle_bin:
			compare_timelines_in_bin(handle_bin.content)

if __name__ == "__main__":

	if len(sys.argv) < 2:
		sys.exit(f"Usage: {__file__} avid_bin.avb")
	
	main(sys.argv[1:])