import sys, dataclasses
import avb, avbutils
from timecode import TimecodeRange

@dataclasses.dataclass
class MasterclipInfo:
	clip_name:str
	tape_name:str
	timecode:TimecodeRange

def get_masterclips_from_bin(bin:avb.bin.Bin) -> avb.trackgroups.Composition:
	"""Get a masterclip from the bin"""
	
	yield bin.mastermobs()

def get_materclip_info(masterclip:avb.trackgroups.Composition):
	"""Get info from a masterclip"""

	sourcemob = avbutils.matchback_to_sourcemob(masterclip)
	
	masterclip_tc = TimecodeRange(start=avbutils.get_timecode_range_for_composition(sourcemob).start, duration=masterclip.length)

	return MasterclipInfo(
		clip_name = masterclip.name,
		tape_name = sourcemob.name,
		timecode  = masterclip_tc
	)


def show_masterclip_info_from_file(bin_path:str):
	"""Given a file path to a bin, print materclip info"""

	print("In", bin_path, "...")

	with avb.open(bin_path) as bin_handle:
		for masterclip in  bin_handle.content.mastermobs():
			try:
				info = get_materclip_info(masterclip)
			except Exception as e:
				print(f"Skipping {masterclip.name}: {e}")
				continue
			print(f"{info.clip_name.ljust(24)}{info.tape_name.ljust(24)}{info.timecode.start} - {info.timecode.end} ({str(info.timecode.duration).lstrip('0:')})")
	
	print("")


if __name__ == "__main__":
	if len(sys.argv) < 2:
		sys.exit(f"Usage: {__file__} bin.avb")
	
	for bin_path in sys.argv[1:]:
		show_masterclip_info_from_file(bin_path)