import enum
import avb

# TODO: Maybe .sorting.BinSorting goes here? Probably.

class BinDisplayModes(enum.IntEnum):
	"""Avid Bin View Modes"""

	# NOTE: Data originates from `avb.bin.Bin.display_mode` property
	
	LIST   = 0
	"""List View Mode"""
	FRAME  = 1
	"""Frame View Mode"""
	SCRIPT = 2
	"""Script View Mode"""

	@classmethod
	def get_mode_from_bin(cls, bin:avb.bin.Bin) -> "BinDisplayModes":
		"""Return the `BinDisplayModes` value for a given bin"""
		return cls(bin.display_mode)

class BinDisplayOptions(enum.IntFlag):
	"""Types of data to display in the bin (from "Set Bin Display" dialog)"""

	# NOTE: Data originates from `avb.bin.Bin.display_mask` property

	# NOTE: Once flags have been set, they can be retrieved individually
	# by calling the instance's `IntFlag.flag_members()` or converting the instance to a list

	MASTER_CLIPS               = 0b00000000000000001
	"""Show Master Clips"""
	SUBCLIPS                   = 0b00000000000000010
	"""Show Subclips"""
	SEQUENCES                  = 0b00000000000000100
	"""Show Sequences"""
	SOURCES                    = 0b00000000000001000
	"""Show Sources"""
	EFFECTS                    = 0b00000000000010000
	"""Show Effects"""
	GROUPS                     = 0b00000000000100000
	"""Show Groups"""
	PRECOMP_RENDERED_EFFECTS   = 0b00000000001000000
	"""Show Precompute Clips - Rendered Effects"""
	MOTION_EFFECTS             = 0b00000000010000000
	"""Show Motion Effects"""

	#UNKNOWN_00                = 0b00000000100000000

	SHOW_CLIPS_CREATED_BY_USER = 0b00000001000000000
	"""Show Clips Created By User"""
	SHOW_REFERENCE_CLIPS       = 0b00000010000000000
	"""Show Reference Clips"""
	PRECOMP_TITLES_MATTEKEYS   = 0b00000100000000000
	"""Show Precompute Clips - Titles and Matte Keys"""

	#UNKNOWN_01                = 0b00001000000000000
	#UNKNOWN_02                = 0b00010000000000000
	#UNKNOWN_03                = 0b00100000000000000

	STEREOSCOPIC_CLIPS         = 0b01000000000000000
	"""Show Stereoscopic Clips"""
	LINKED_MASTER_CLIPS        = 0b10000000000000000
	"""Show Linked Master Clips"""

	@classmethod
	def get_options_from_bin(cls, bin:avb.bin.Bin) -> "BinDisplayOptions":
		"""Return the `BinDisplayModes` value for a given bin"""
		return cls(bin.display_mask)
	
class BinSortDirection(enum.IntEnum):
	"""Direction the BinSortMethod will sort"""
	
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