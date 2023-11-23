import sys, enum
import avb, avbutils

class BinSortDirection(enum.IntEnum):
	"""Direction the BinSortMethod will sort"""

	# TODO: Add this to `avbutils.sorting` or `.bin` or something
	
	ASCENDING  = 0
	"""0-9; A-Z"""

	DESCENDING = 1
	"""Z-A; 9-0"""

def show_bin_info(bin:avb.bin.Bin):
	"""Print info from an `avb.bin.Bin`"""

	print("View Setting:", bin.view_setting.name, bin.view_setting.kind)
	print("Display Mode:", avbutils.BinDisplayModes.get_mode_from_bin(bin).name)
	print("Display Mask:", avbutils.BinDisplayOptions.get_options_from_bin(bin).name)
	print("Sort Columns:", [f"{c} ({BinSortDirection(d).name.title()})" for d,c in bin.sort_columns])
	print(f"Mac font:     {bin.mac_font=} {bin.mac_font_size=}")
	print(f"Image Scale:  {bin.mac_image_scale=} {bin.ql_image_scale=}")
	print(f"Home rect:    {bin.home_rect=}")
	print(f"Colors (16b?):{bin.background_color=} {bin.forground_color=}")
	print("Was iconic?: ", bin.was_iconic)
	print("Large bin?:  ", bin.large_bin)
	print("Sifted?:     ", bin.sifted)
	print("Sift Params: ", bin.sifted_settings)

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