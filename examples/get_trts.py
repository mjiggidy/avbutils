import trtlib
import sys, pathlib, concurrent.futures
from collections import namedtuple
from timecode import Timecode

# START CONFIG

# Durations of head/tail slates, will be factored out of TRT per reel
SLATE_HEAD_DURATION = Timecode("8:00")
SLATE_TAIL_DURATION = Timecode("3:23")

# How to sort sequences to find the "most current"
BIN_SORTING_METHOD = trtlib.BinSorting.DATE_MODIFIED

# Results list setup
COLUMN_SPACING = "     "
HEADERS = {
	"Reel Name"     : 0,
	"Reel TRT"      : 11,
	"LFOA"          : 7,
	"Date Modified" : 19,
	"Bin Locked"    : 10
}

# END CONFIG

USAGE = f"Usage: {__file__} path/to/avbs [--head {SLATE_HEAD_DURATION}] [--tail {SLATE_TAIL_DURATION}]"

BinInfo = namedtuple("BinInfo","reel path lock")

def get_latest_stats_from_bins(bin_paths:list[pathlib.Path]) -> list[BinInfo]:
	"""Get stats for a list of bins"""

	parsed_info = []
	
	# Parse Bins Concurrently
	with concurrent.futures.ProcessPoolExecutor() as ex:

		# Create a dict associating a subprocess with the path of the bin it's working on
		future_info = {
			ex.submit(trtlib.get_reel_info_from_path,
				bin_path=bin_path,
				head_duration=SLATE_HEAD_DURATION,
				tail_duration=SLATE_TAIL_DURATION,
				sort_by = BIN_SORTING_METHOD): bin_path for bin_path in bin_paths
		}

		# Process each result as it becomes available
		for future_result in concurrent.futures.as_completed(future_info):
			bin_path = future_info[future_result]

			try:
				info = future_result.result()
			except Exception as e:
				print(f"Skipping {bin_path.name}: {e}")
				continue

			lock = trtlib.get_lockfile_for_bin(bin_path)

			# Combine all the info
			parsed_info.append(BinInfo(
				reel = info,
				path = bin_path,
				lock = lock
			))
			
			# While we're here: Figure out the padding for the Reel Name column
			HEADERS["Reel Name"] = max(HEADERS.get("Reel Name",0), len(info.sequence_name))
	
	return parsed_info
	

def print_trts(parsed_info:list[BinInfo]):
	"""Print the results"""

	# List the results
	# This is terrible code but you get the idea
	print("")

	print(COLUMN_SPACING.join(colname.ljust(pad) for colname, pad in HEADERS.items()))
	print(COLUMN_SPACING.join('=' * pad for _, pad in HEADERS.items()))

	for info in sorted(parsed_info, key=lambda x: trtlib.human_sort(x.reel.sequence_name)):
		print(COLUMN_SPACING.join(x for x in [
			info.reel.sequence_name.ljust(HEADERS.get("Reel Name")),
			str(info.reel.duration_adjusted).rjust(HEADERS.get("Reel TRT")),
			info.reel.lfoa.rjust(HEADERS.get("LFOA")),
			str(info.reel.date_modified).rjust(HEADERS.get("Date Modified")),
			info.lock.ljust(HEADERS.get("Bin Locked")) if info.lock else '-',
		]))
	
	print("")
	print(f"* Total TRT: {sum(info.reel.duration_adjusted for info in parsed_info)}")
	print("")

def process_args():
	"""Look for --head/--tail options"""
	# Yeah, yeah... I just don't like `argparse` okay?

	global SLATE_HEAD_DURATION
	global SLATE_TAIL_DURATION

	# Head leader duration was specified
	while "--head" in sys.argv:
		head_index = sys.argv.index("--head")
		
		SLATE_HEAD_DURATION = Timecode(sys.argv[head_index+1])
		print(f"Using custom head: {SLATE_HEAD_DURATION}")
		
		del sys.argv[head_index+1]
		del sys.argv[head_index]
		

	# Tail leader duration was specified
	while "--tail" in sys.argv:
		tail_index = sys.argv.index("--tail")

		SLATE_TAIL_DURATION = Timecode(sys.argv[tail_index+1])
		print(f"Using custom tail: {SLATE_TAIL_DURATION}")

		del sys.argv[tail_index+1]
		del sys.argv[tail_index]

def main():

	if not len(sys.argv):
		sys.exit(USAGE)

	# Process command line arguments
	try:
		process_args()
	except:
		sys.exit(USAGE)

	# Get bin paths (.avb) from the folder provided
	bin_paths = [p for p in pathlib.Path(sys.argv[1]).glob("*.avb") if not p.stem.startswith('.')]
	if not bin_paths:
		sys.exit(f"No bins found at {sys.argv[1]}")

	# Get the relevant info from each bin
	parsed_info = get_latest_stats_from_bins(bin_paths)
	if not len(parsed_info):
		sys.exit(f"No sequences were found in any bins.")

	# Print the results
	print_trts(parsed_info)

if __name__ == "__main__":

	main()