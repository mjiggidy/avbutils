import sys, pathlib
import avbutils, avb

def show_timeline_info_for_bin(bin:avb.bin.Bin):

		# Get timelines, sorted by date modified
		for timeline in sorted(avbutils.get_timelines_from_bin(bin), key=avbutils.BinSorting.get_sort_lambda(avbutils.BinSorting.DATE_MODIFIED), reverse=True):
			timeline_timecode = avbutils.get_timecode_range_for_composition(timeline)
			print(f"Found {timeline.name} ({timeline.edit_rate}):   {timeline_timecode.start} - {timeline_timecode.end} ({str(timeline_timecode.duration).lstrip('0:')})")
		
		print("")

if __name__ == "__main__":

	if len(sys.argv) < 2:
		sys.exit(f"{pathlib.Path(__file__).name} bin_path.avb [another_bin_path.avb ...]")
	
	for bin_path in sys.argv[1:]:
		print(f"Opening {bin_path}...")
		with avb.open(bin_path) as bin_handle:
			show_timeline_info_for_bin(bin_handle.content)