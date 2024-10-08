import enum
import avb

# TODO: Maybe .sorting.BinSorting goes here? Probably.

# Thumbnail grid is 278x174 at largest scale  (vs 224x126 thumbnail)
#                   68 x 74 at smallest scale (vs 64x36 thumbnail)

THUMB_FRAME_MODE_RANGE  = range(4, 14) # Multiplier of 16x9
"""Size multiplier for thumbnails in Frame Mode"""

THUMB_SCRIPT_MODE_RANGE = range(3, 8) # Multiplier of 16x9
"""Size multiplier for thumbnails in Script Mode"""

THUMB_UNIT_SIZE = (16, 9)
"""Width and height of a thumbnail, to be multiplied by a scalar in `THUMB_FRAME_MODE_RANGE` or `THUMB_SCRIPT_MODE_RANGE`"""

FONT_SIZE_RANGE = range(8,100)
FONT_INDEX_OFFSET = 142+12+7
""" wat """

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

	# NOTE: Marry these to `.compositions.MobUsage`?

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
	
	def __str__(self) -> str:
		"""Show name with nicer formatting"""
		return self.name.replace("_"," ").title()
	
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
	
class BinColumnFormat(enum.IntEnum):
	"""Display format of a bin column"""

	ICON = 0
	"""Graphical icon indicators"""

	PERF = 1
	# TODO: Unknown, belongs to "Perf" column at least

	USER_TEXT = 2
	"""User-editable text field"""

	WHAT = 20

	TIMECODE = 100
	# TODO: Slip column appears to be integer

	FRAME_COUNT = 101
	# TODO: VFX Column appears to be formatted text

	DATE_TIME = 102

	FRAME_RATE = 103
	# TODO: Alt: Decimal or fractional?

	STRICT = 105
	# TODO: Seems to be an option from one of several choices?

	FRAME = 106
	"""Thumbnail"""

	CODEC_INFO = 109
	# Perhaps references to other flavors?

	def __str__(self) -> str:
		"""Show name with nicer formatting"""
		return self.name.replace("_"," ").title()