import sys
import avb, avbutils

def show_bin_info(bin:avb.bin.Bin):
	"""Print info from an `avb.bin.Bin`"""

	print("View Setting:", bin.view_setting.name, bin.view_setting.kind)
	print("Display Mode:", avbutils.BinDisplayModes.get_mode_from_bin(bin).name)
	print("Display Mask:", avbutils.BinDisplayOptions.get_options_from_bin(bin).name)
	print("Sort Columns:", [c + ": " + (f"Descending ({d})" if d else f"Ascending ({d})") for d,c in bin.sort_columns])

def show_bin_info_from_file(bin_path:str):
	"""Given a file path to a bin, print bin info"""

	print("In", bin_path, "...")

	with avb.open(bin_path) as bin_handle:
		show_bin_info(bin_handle.content)

if __name__ == "__main__":
	if len(sys.argv) < 2:
		sys.exit(f"Usage: {__file__} bin.avb")
	
	for bin_path in sys.argv[1:]:
		show_bin_info_from_file(bin_path)