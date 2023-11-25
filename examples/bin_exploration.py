import sys, enum, pprint
import avb, avbutils

class BinSortDirection(enum.IntEnum):
	"""Direction the BinSortMethod will sort"""

	# TODO: Add this to `avbutils.sorting` or `.bin` or something
	
	ASCENDING  = 0
	"""0-9; A-Z"""

	DESCENDING = 1
	"""Z-A; 9-0"""

class BinSiftMethod(enum.IntEnum):
	"""Methods for sifting"""

	# NOTE: SiftItems are listed in reverse order

	CONTAINS = 1
	"""Column contains a given string"""

	BEGINS_WITH = 2
	"""Column begins with a given string"""

	MATCHES_EXACTLY = 3
	"""Column matches exactly a given string"""

	@classmethod
	def from_sift_item(cls, sift_item:avb.bin.SiftItem) -> "BinSiftMethod":
		"""Lookup the sift method based on the method `int`"""
		return cls(sift_item.method)
	
	@classmethod
	def from_bin(cls, bin:avb.bin.Bin) -> list["BinSiftMethod"]:
		# NOTE: Does this make sense to do?
		return [cls.from_sift_item(item) for item in bin.sifted_settings]



def show_bin_info(bin:avb.bin.Bin):
	"""Print info from an `avb.bin.Bin`"""

	print("Large bin?:  ", bin.large_bin)
	print("Was iconic?: ", bin.was_iconic)
	
	print("\n-------\n")
	
	print("Display Mode:", avbutils.BinDisplayModes.get_mode_from_bin(bin).name)
	print("Display Mask:", avbutils.BinDisplayOptions.get_options_from_bin(bin).name)
	print(f"Mac font:     {bin.mac_font=} {bin.mac_font_size=}")
	print(f"Colors (16b?):{bin.background_color=} {bin.forground_color=}")
	print(f"Image Scale:  Frame Mode Size (4-14): {bin.mac_image_scale=} Script Mode Size (3-8): {bin.ql_image_scale=}")
	print(f"Home rect:    (top-left, bottom-right) {bin.home_rect=}  ({bin.home_rect[3]-bin.home_rect[1]}x{bin.home_rect[2]-bin.home_rect[0]})")
	
	print("\n-------\n")
	
	print("Sort Columns:", [f"{c} ({BinSortDirection(d).name.title()})" for d,c in bin.sort_columns])

	# Sifted items
	# Listed in reverse order.
	# Only contains "Sift Bin Contents..." settings -- not "Sift Selected Items", it seems
	print("Sifted?:     ", bin.sifted)
	print("Sift Params: ")
	for idx, param in enumerate(bin.sifted_settings[::-1]):
		if idx == 3:
			print("Also...")
		print(f" - Column \"{param.column}\" {BinSiftMethod.from_sift_item(param).name.replace('_',' ').lower()} the string \"{param.string}\"")

	print("\n-------\n")

	print("View Setting:", bin.view_setting.name, bin.view_setting.kind)
	print("Kind:        ", bin.view_setting.kind) # TODO: Always "Bin View" or...?
	
	print("# Attributes:", bin.view_setting.attr_count)
	print("Attr Type:   ", bin.view_setting.attr_type)
	print("Attributes:  ", bin.view_setting.attributes.items())
	print(f"Format Descriptors: ({len(bin.view_setting.format_descriptors)})")
	for desc in bin.view_setting.format_descriptors:
		pprint.pprint(desc)
		print("-")
	print("Columns:     ")
	for col in bin.view_setting.columns:
		print(" -", col)


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