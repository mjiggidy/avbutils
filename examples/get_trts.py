import trtlib
import sys, pathlib
from collections import namedtuple
from timecode import Timecode

BinInfo = namedtuple("BinInfo","reel path lock")

USAGE = f"Usage: {__file__} path/to/avbs [--head 8:00] [--tail 3:23]"

SLATE_HEAD_DURATION = Timecode("8:00")
SLATE_TAIL_DURATION = Timecode("3:23")

def list_latest_trt_from_bins(bins_path:str):
	"""Example"""

	parsed_info = []

	bin_paths = [p for p in pathlib.Path(bins_path).glob("*.avb") if not p.stem.startswith('.')]

	if not bin_paths:
		raise FileNotFoundError(f"No bins found at {bins_path}")
	
	padding = 0

	for bin_path in bin_paths:
		#print(bin_path)
		try:
			info = trtlib.get_reelinfo_from_path(bin_path, head_duration=SLATE_HEAD_DURATION, tail_duration=SLATE_TAIL_DURATION)
		except Exception as e:
			print(f"Skipping {bin_path.name}: {e}")
			continue

		lock = trtlib.get_lockfile_for_bin(bin_path)
		parsed_info.append(BinInfo(
			reel = info,
			path = bin_path,
			lock = lock
		))
		
		padding = max(padding, len(info.sequence_name))
	
	if not len(parsed_info):
		raise Exception(f"No sequences were found in any bins.")

	print("")
	print(f"{'Reel Name'.ljust(padding)}	Reel TRT   	LFOA   	Date Modified      	Locked")
	print(f"{'=' * padding}\t{'='*len('Reel TRT  	')}\t{'='*7}\t{'='*19}\t{'='*12}")

	for info in sorted(parsed_info, key=lambda x: trtlib.human_sort(x.reel.sequence_name)):
		print('\t'.join(str(x) for x in [
			info.reel.sequence_name.ljust(padding),
			info.reel.duration_adjusted,
			info.reel.lfoa.rjust(7),
			info.reel.date_modified,
			info.lock if info.lock else '-',
		]))
	
	print("")
	print(f"* Total TRT: {sum(info.reel.duration_adjusted for info in parsed_info)}")
	print("")

def main():

	if not len(sys.argv):
		sys.exit(USAGE)

	if "--head" in sys.argv:
		try:
			SLATE_HEAD_DURATION = Timecode(sys.argv[sys.argv.index("--head")+1])
		except Exception as e:
			sys.exit(USAGE)
		
		print(f"Using custom head: {SLATE_HEAD_DURATION}")

	if "--tail" in sys.argv:
		try:
			SLATE_TAIL_DURATION = Timecode(sys.argv[sys.argv.index("--tail")+1])
		except Exception as e:
			sys.exit(USAGE)
		
		print(f"Using custom tail: {SLATE_TAIL_DURATION}")

	list_latest_trt_from_bins(sys.argv[1])

if __name__ == "__main__":

	main()