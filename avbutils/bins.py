import enum, dataclasses
import avb
from . import compositions, matchback

# TODO: Maybe .sorting.BinSorting goes here? Probably.

# Thumbnail grid is 278x174 at largest scale  (vs 224x126 thumbnail)
#                   68 x 74 at smallest scale (vs 64x36 thumbnail)

THUMB_FRAME_MODE_RANGE  = range(4, 14) # Multiplier of `THUMB_UNIT_SIZE`
"""Size multiplier for thumbnails in Frame Mode"""

THUMB_SCRIPT_MODE_RANGE = range(3, 8) # Multiplier of `THUMB_UNIT_SIZE`
"""Size multiplier for thumbnails in Script Mode"""

THUMB_UNIT_SIZE = (16, 9)
"""Width and height of a thumbnail, to be multiplied by a scalar in `THUMB_FRAME_MODE_RANGE` or `THUMB_SCRIPT_MODE_RANGE`"""

FONT_SIZE_RANGE = range(8,100)
"""Range of allowed font sizes (px?)"""

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

class BinDisplayItemTypes(enum.Flag):
	"""Types of data to display in the bin (from "Set Bin Display" dialog)"""

	# NOTE: Data originates from `avb.bin.Bin.display_mask` property

	# NOTE: Once flags have been set, they can be retrieved individually
	# by calling the instance's `IntFlag.flag_members()` or converting the instance to a list

	# NOTE: Marry these to `.compositions.MobUsage`?

	MASTER_CLIP               = 0b00000000000000001
	"""Show Master Clips"""
	SUBCLIP                   = 0b00000000000000010
	"""Show Subclips"""
	SEQUENCE                  = 0b00000000000000100
	"""Show Sequences"""
	SOURCE                    = 0b00000000000001000
	"""Show Sources"""
	EFFECT                    = 0b00000000000010000
	"""Show Effects"""
	GROUP                     = 0b00000000000100000
	"""Show Groups"""
	PRECOMP_RENDERED_EFFECT   = 0b00000000001000000
	"""Show Precompute Clips - Rendered Effects"""
	MOTION_EFFECT             = 0b00000000010000000
	"""Show Motion Effects"""

	#UNKNOWN_00                = 0b00000000100000000

	USER_CLIP                 = 0b00000001000000000
	"""Show Clips Created By User"""
	REFERENCE_CLIP            = 0b00000010000000000
	"""Show Reference Clips"""
	PRECOMP_TITLE_MATTEKEY   = 0b00000100000000000
	"""Show Precompute Clips - Titles and Matte Keys"""

	#UNKNOWN_01                = 0b00001000000000000
	#UNKNOWN_02                = 0b00010000000000000
	#UNKNOWN_03                = 0b00100000000000000

	STEREOSCOPIC_CLIP         = 0b01000000000000000
	"""Show Stereoscopic Clips"""
	LINKED_MASTER_CLIP        = 0b10000000000000000
	"""Show Linked Master Clips"""

	@classmethod
	def get_options_from_bin(cls, bin:avb.bin.Bin) -> "BinDisplayItemTypes":
		"""Return the `BinDisplayModes` value for a given bin"""
		return cls(bin.display_mask)
	
	@classmethod
	def default_items(cls) -> "BinDisplayItemTypes":
		"""Get the default BinDisplay modes"""

		return \
			cls.MASTER_CLIP | \
			cls.LINKED_MASTER_CLIP | \
			cls.SUBCLIP | \
			cls.SEQUENCE | \
			cls.EFFECT | \
			cls.MOTION_EFFECT | \
			cls.GROUP | \
			cls.STEREOSCOPIC_CLIP | \
			cls.USER_CLIP
	
	@classmethod
	def from_bin_item(cls, bin_item:avb.bin.BinItem) -> "BinDisplayItemTypes":

		flags = cls(0)
		flags |= cls.USER_CLIP if bin_item.user_placed else cls.REFERENCE_CLIP

		comp:avb.trackgroups.Composition = bin_item.mob

		#print(comp)

		if compositions.composition_is_timeline(comp):
			flags |= cls.SEQUENCE
		elif compositions.composition_is_masterclip(comp):
			flags |= cls.MASTER_CLIP
		elif compositions.composition_is_subclip(comp):
			flags |= cls.SUBCLIP
		elif compositions.composition_is_effect_mob(comp):
			flags |=  cls.EFFECT
		elif compositions.composition_is_groupclip(comp):
			flags |= cls.GROUP
		elif compositions.composition_is_groupoofter(comp):
			flags |= cls.GROUP
		elif compositions.composition_is_motioneffect_mob(comp):
			flags |= cls.MOTION_EFFECT
		elif compositions.composition_is_precompute_clip(comp):
			flags |= cls.PRECOMP_TITLE_MATTEKEY
		elif compositions.composition_is_precompute_mob(comp):
			flags |= cls.PRECOMP_RENDERED_EFFECT
		elif compositions.composition_is_source_mob(comp):
			flags |= cls.SOURCE
		elif compositions.composition_is_master_mob(comp):
			flags |= cls.MASTER_CLIP
		else:
			raise ValueError(f"Unable to identify mob role ({compositions.MobTypes.from_composition(comp)=}) ({compositions.MobUsage.from_composition(comp)}=)")
		
		return flags
	
	def __str__(self) -> str:
		"""Show name with nicer formatting"""
		if self.name:
			return self.name.replace("_"," ").title()
		return ""
	
class BinSortDirection(enum.IntEnum):
	"""Direction the BinSortMethod will sort.  Note: Corresponds to QtCore.Qt.SortOrder enum"""
	
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
	
@dataclasses.dataclass(frozen=True)
class BinSiftOption:
	"""A single sift option"""

	sift_method:BinSiftMethod
	sift_text  :str
	sift_column:str

	@classmethod
	def from_sift_item(cls, sift_item:avb.bin.SiftItem) -> "BinSiftOption":
		return cls(
			sift_method = BinSiftMethod(sift_item.method),
			sift_text   = sift_item.string,
			sift_column = sift_item.column,
		)
	
	@classmethod
	def from_sift_items(cls, sift_items:list[avb.bin.SiftItem]) -> list["BinSiftOption"]:
		return [cls.from_sift_item(s) for s in reversed(sift_items)]
	
	@classmethod
	def from_bin(cls, bin_contents:avb.bin.Bin) -> tuple[bool, list["BinSiftOption"]]:
		"""Get sift enabled `bool` and list of `BSSiftOption`s from bin contents"""

		return (
			bin_contents.sifted,
			cls.from_sift_items(bin_contents.sifted_settings)
		)

	
class BinColumnFormat(enum.Enum):
	"""Display format of a bin column"""

	ICON = 0
	"""Graphical icon indicators"""

	PERF = 1
	# TODO: Unknown, belongs to "Perf" column at least

	USER_TEXT = 2
	"""User-editable text field"""

	WHATS_THIS = 4
	"Say what"

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
	
BIN_COLUMN_ROLES:dict[int, str] = {
	"Tracks" : 1,
	"Start" : 2,
	"End" : 3,
	"Duration" : 4,
	"Mark IN" : 5,
	"Mark OUT" : 6,
	"IN-OUT" : 7,
	"Tape" : 8,
	"FPS" : 9,
	"CFPS" : 10,
	"Audio SR" : 11,
	"Creation Date" : 12,
	"Video" : 13,
	"Drive" : 14,
	"KN Start" : 15,
	"KN End" : 16,
	"KN Dur" : 17,
	"KN Mark IN" : 18,
	"KN Mark OUT" : 19,
	"KN IN-OUT" : 20,
	"Pullin" : 21,
	"Pullout" : 22,
	"Film TC" : 23,
	"Sound TC" : 24,
	"Auxiliary TC1" : 25,
	"Auxiliary TC2" : 26,
	"Auxiliary TC3" : 27,
	"Auxiliary TC4" : 28,
	"Auxiliary TC5" : 29,
	"Ink Number" : 30,
	"VITC" : 31,
	"Color Framing" : 32,
	"Auxiliary EC1" : 33,
	"Offline" : 35,
	"Frame" : 36,
	"Auxiliary Ink" : 37,
	"Reel #" : 38,
	"Scene" : 39,
	"Take" : 41,
	"Soundroll" : 42,
	"Camroll" : 43,
	"Shoot Date" : 44,
	"Labroll" : 45,
	"Camera" : 46,
	"Slip" : 47,
	"Lock" : 48,
	"Perf" : 49,
	"TapeID" : 50,
	"Color" : 51,
	"Film" : 52,
	"Media File" : 53,
	"Modified Date" : 54,
	"Audio Format" : 55,
	"TC 24" : 56,
	"TC 25PD" : 57,
	"TC 25" : 58,
	"TC 30" : 59,
	"Audio Bit Depth" : 61,
	"Cadence" : 62,
	"Aux TC 24" : 63,
	"Video File Format" : 64,
	"Format" : 65,
	"AuxInk Dur" : 66,
	"AuxInk Edge" : 67,
	"AuxInk End" : 68,
	"AuxInk Film" : 69,
	"DPX" : 70,
	"VFX" : 71,
	"VFX Reel" : 72,
	"Ink Dur" : 73,
	"Ink Edge" : 74,
	"Ink End" : 75,
	"Ink Film" : 76,
	"KN Film" : 78,
	"LUT" : 79,
	"Master Dur" : 80,
	"Master Edge" : 81,
	"Master End" : 82,
	"Master Film" : 83,
	"Master Start" : 84,
	"Transfer" : 85,
	"UNC Path" : 86,
	"TC 30NP" : 87,
	"TC 60" : 88,
	"Disk Label" : 89,
	"Journalist" : 90,
	"Production" : 91,
	"IDataLink" : 92,
	"ASC_SOP" : 93,
	"ASC_SAT" : 94,
	"Field Motion" : 95,
	"Track Formats" : 96,
	"Color Space" : 97,
	"Image Aspect Ratio" : 98,
	"Pixel Aspect Ratio" : 99,
	"Reformat" : 100,
	"Source File" : 101,
	"Ancillary Data" : 102,
	"Color Transformation" : 103,
	"S3D Clip Name" : 104,
	"Source Path" : 105,
	"S3D Contributors" : 106,
	"S3D Leading Eye" : 107,
	"S3D Channel" : 108,
	"S3D Group Name" : 109,
	"S3D Inversion" : 110,
	"S3D InversionR" : 111,
	"S3D Eye Order" : 112,
	"Vendor Name" : 113,
	"Vendor URL" : 114,
	"Vendor Asset ID" : 115,
	"Vendor Asset Name" : 116,
	"Vendor Asset Rights" : 117,
	"Vendor Asset Price" : 118,
	"Vendor Original Master" : 119,
	"Vendor Asset Description" : 120,
	"Vendor Asset Keywords" : 121,
	"Vendor Asset Status" : 122,
	"Vendor Invoice ID" : 123,
	"Vendor Download Master" : 124,
	"S3D Alignment" : 125,
	"Image Framing" : 127,
	"Raster Dimension" : 128,
	"Image Size" : 129,
	"Media Status" : 130,
	"AFD" : 131,
	"Marker" : 132,
	"Plug-in" : 133,
	"Reel" : 134,
	"Frame Count Start" : 135,
	"Frame Count End" : 136,
	"Frame Count Duration" : 137,
	"Video Data Rate" : 139,
	"BIN Start" : 141,
	"BIN End" : 142,
	"BIN Tracks" : 143,
	"Chroma Subsampling" : 144,
	"Media File Path" : 145,
	"Proxy Offline" : 146,
	"Proxy Audio" : 147,
	"Proxy Video" : 148,
	"Proxy Path" : 149,
	"Invert Alpha" : 150,
	"Ignore Alpha" : 151,
	"Premult Alpha" : 152,
	"Alpha Channel" : 153,
	"Alpha Mode" : 154,
	"Alpha Mode" : 155,
	"Transcription" : 156,
	"" : 200,
	"Name" : 201,
	"Project" : 204,
	"10:1 (NTSC)" : 10075,
	"2:1 (NTSC)" : 10076,
	"3:1 (NTSC)" : 10077,
	"15:1s (NTSC)" : 10078,
	"4:1s (NTSC)" : 10079,
	"2:1s (NTSC)" : 10080,
	"20:1 (NTSC)" : 10082,
	"3:1 (NTSC)" : 10097,
	"2:1 (NTSC)" : 10098,
	"35:1 (NTSC)" : 10102,
	"14:1 (NTSC)" : 10103,
	"28:1 (NTSC)" : 10104,
	"10:1m (NTSC)" : 10110,
	"4:1m (NTSC)" : 10111,
	"8:1m (NTSC)" : 10112,
	"3:1m (NTSC)" : 10113,
	"DV 25 411 (NTSC)" : 10140,
	"DV 25 420 i(PAL)" : 10141,
	"DV 50 (NTSC)" : 10142,
	"DV25P 411 (NTSC)" : 10143,
	"DV 25P 420 (PAL)" : 10144,
	"DV50P (NTSC)" : 10147,
	"1:1 (NTSC)" : 10151,
	"1:1 (NTSC)" : 10152,
	"MPEG 50 (NTSC)" : 10160,
	"MPEG 40 (NTSC)" : 10161,
	"MPEG 30 (NTSC)" : 10162,
	"1:1 (NTSC)" : 10170,
	"1:1 (NTSC)" : 10171,
	"J2K 1080i 59.94 (HD1080i)" : 10550,
	"J2K 1080p 23.976 (HD1080p)" : 10551,
	"J2K 720p 59.94 (HD720p)" : 10552,
	"J2K NTSCi 29.97 (NTSC)" : 10553,
	"J2K NTSCp 23.976 (NTSC)" : 10554,
	"J2K PALi 25 i(PAL)" : 10555,
	"J2K PALp 25 (PAL)" : 10556,
	"J2K 1080i 50 (HD1080i)" : 10557,
	"J2K 1080p 29.97 (HD1080p)" : 10558,
	"J2K 1080p 25 (HD1080p)" : 10559,
	"J2K 1080p 24 (HD1080p)" : 10560,
	"J2K 720p 29.97 (HD720p)" : 10562,
	"J2K 720p 25 (HD720p)" : 10563,
	"J2K 720p 23.976 (HD720p)" : 10564,
	"J2K NTSCp 24 (NTSC)" : 10565,
	"J2K PALp 24 (PAL)" : 10566,
	"DNxHD 175 X (HD1080p)" : 11235,
	"DNxHD 115 (HD1080p)" : 11237,
	"DNxHD 175 (HD1080p)" : 11238,
	"DNxHD 175 X (HD1080i)" : 11241,
	"DNxHD 115 (HD1080i)" : 11242,
	"DNxHD 175 (HD1080i)" : 11243,
	"DNxHD-TR 115 (HD1080i)" : 11244,
	"DNxHD 90 X (HD720p)" : 11250,
	"DNxHD 90 (HD720p)" : 11251,
	"DNxHD 60 (HD720p)" : 11252,
	"DNxHD 36 (HD1080p)" : 11253,
	"DNxHD 444 350 X (HD1080p)" : 11256,
	"DNxHD 50 (HD720p)" : 11258,
	"DNxHD 80 (HD1080p)" : 11259,
	"DNxHD 80 (HD1080i)" : 11260,
	"MPEG-4 525" : 11500,
	"MPEG-4 625" : 11501,
	"MPEG-4 (NTSC)" : 11502,
	"MPEG-4 (PAL)" : 11503,
	"MPEG-4 525 750 60 (NTSC)" : 11505,
	"MPEG-4 525p 23.976 750 (NTSC)" : 11507,
	"MPEG-4 525 500 60 (NTSC)" : 11509,
	"MPEG-4 625 500 50 i(PAL)" : 11510,
	"MPEG-4 525p 23.976 500 (NTSC)" : 11511,
	"1:1 10b (HD1080i)" : 12000,
	"1:1p 10b (HD1080p)" : 12003,
	"1:1p 10b (HD720p)" : 12004,
	"1:1 10b (NTSC)" : 12021,
	"1:1 10b i(PAL)" : 12022,
	"1:1 10b (NTSC)" : 12023,
	"1:1 10b (PAL)" : 12024,
	"1:1 (HD1080i)" : 12125,
	"1:1 (HD1080p)" : 12126,
	"1:1 (HD720p)" : 12127,
	"DVCPro HD (1080i/50)" : 12400,
	"DVCPro HD (1080i/60)" : 12401,
	"DVCPro HD (720p/60)" : 12402,
	"DVCPro HD (720p/50)" : 12403,
	"1:1 10b RGB (HD1080i)" : 12500,
	"1:1 10b RGB (HD1080p)" : 12503,
	"AVC-Intra 50 (HD720p)" : 13402,
	"AVC-Intra 50 (HD720p)" : 13403,
	"AVC-Intra 50 (HD720p)" : 13404,
	"AVC-Intra 50 (HD1080i)" : 13405,
	"AVC-Intra 50 (HD1080i)" : 13406,
	"AVC-Intra 50 (HD1080p)" : 13409,
	"AVC-Intra 100 (HD720p)" : 13411,
	"AVC-Intra 100 (HD720p)" : 13412,
	"AVC-Intra 100 (HD720p)" : 13413,
	"AVC-Intra 100 (HD720p)" : 13414,
	"AVC-Intra 100 (HD1080i)" : 13415,
	"AVC-Intra 100 (HD1080i)" : 13416,
	"AVC-Intra 100 (HD1080p)" : 13417,
	"AVC-Intra 100 (HD1080p)" : 13418,
	"AVC-Intra 100 (HD1080p)" : 13419,
	"XAVC Intra 50 (HD1080i)" : 13420,
	"XAVC Intra 50 (HD1080i)" : 13421,
	"XAVC Intra 50 (HD1080p)" : 13422,
	"XAVC Intra 100 (HD1080i)" : 13425,
	"XAVC Intra 100 (HD1080i)" : 13426,
	"XAVC Intra 100 (HD1080p)" : 13427,
	"XAVC Intra 100 (HD1080p)" : 13428,
	"XAVC Intra 100 (HD1080p)" : 13429,
	"AVCIBP-BLL2.0 (NTSC)" : 13450,
	"AVCIBP-BLL2.0 i(PAL)" : 13451,
	"AVCIBP-BLL3.0 (HD720p)" : 13457,
	"H.264 800Kbps Proxy (NTSC)" : 13470,
	"H.264 800Kbps Proxy i(PAL)" : 13471,
	"H.264 800Kbps Proxy (HD1080i)" : 13472,
	"H.264 800Kbps Proxy (HD1080i)" : 13473,
	"H.264 800Kbps Proxy (HD720p)" : 13474,
	"H.264 2.0Mbps Proxy (HD1080i)" : 13476,
	"H.264 2.0Mbps Proxy (HD1080i)" : 13477,
	"H.264 2.0Mbps Proxy (HD720p)" : 13478,
	"H.264 800Kbps Proxy (NTSC)" : 13480,
	"H.264 800Kbps Proxy (NTSC)" : 13481,
	"H.264 800Kbps Proxy (PAL)" : 13482,
	"H.264 800Kbps Proxy (PAL)" : 13483,
	"H.264 800Kbps Proxy (HD1080p)" : 13484,
	"H.264 800Kbps Proxy (HD1080p)" : 13485,
	"H.264 800Kbps Proxy (HD1080p)" : 13486,
	"H.264 800Kbps Proxy (HD1080p)" : 13487,
	"H.264 800Kbps Proxy (HD720p)" : 13488,
	"H.264 800Kbps Proxy (HD720p)" : 13489,
	"H.264 800Kbps Proxy (HD720p)" : 13490,
	"H.264 1500Kbps Proxy (NTSC)" : 13491,
	"H.264 1500Kbps Proxy i(PAL)" : 13492,
	"Apple ProRes HQ (NTSC)" : 13700,
	"Apple ProRes HQ i(PAL)" : 13702,
	"Apple ProRes HQ (PAL)" : 13703,
	"Apple ProRes HQ (HD720p)" : 13705,
	"Apple ProRes HQ (NTSC)" : 13709,
	"Apple ProRes HQ (HD1080p)" : 13710,
	"Apple ProRes HQ (HD1080i)" : 13712,
	"Apple ProRes LT (HD720p)" : 13721,
	"Apple ProRes LT (HD1080p)" : 13723,
	"Apple ProRes LT (HD1080i)" : 13725,
	"Apple ProRes LT (NTSC)" : 13726,
	"Apple ProRes LT (PAL)" : 13727,
	"Apple ProRes LT i(PAL)" : 13728,
	"Apple ProRes LT (NTSC)" : 13729,
	"Apple ProRes (NTSC)" : 13740,
	"Apple ProRes (NTSC)" : 13743,
	"Apple ProRes i(PAL)" : 13745,
	"Apple ProRes (PAL)" : 13746,
	"Apple ProRes (HD720p)" : 13748,
	"Apple ProRes (HD1080p)" : 13750,
	"Apple ProRes (HD1080i)" : 13752,
	"Apple ProRes 4444 (NTSC)" : 13784,
	"Apple ProRes 4444 (HD1080p)" : 13790,
	"Apple ProRes Proxy (NTSC)" : 13802,
	"Apple ProRes Proxy (NTSC)" : 13803,
	"Apple ProRes Proxy i(PAL)" : 13804,
	"Apple ProRes Proxy (PAL)" : 13805,
	"Apple ProRes Proxy (HD720p)" : 13807,
	"Apple ProRes Proxy (HD1080p)" : 13809,
	"Apple ProRes Proxy (HD1080i)" : 13811,
	"MPEG2-MPML (NTSC)" : 14000,
	"MPEG2-422ML (NTSC)" : 14001,
	"HDV 720P (720p/30)" : 14002,
	"HDV 1080i (1080i/50)" : 14003,
	"HDV 1080i (1080i/60)" : 14004,
	"MPEG1 (NTSC)" : 14005,
	"MPEG2 352_25I i(PAL)" : 14007,
	"MPEG2 352_30I (NTSC)" : 14008,
	"MPEG2-MPML (NTSC)" : 14009,
	"MPEG2-MPHi1440 (NTSC)" : 14011,
	"MPEG2-MPHL (NTSC)" : 14013,
	"MPEG2-HPML (NTSC)" : 14015,
	"MPEG2-HPHi1440 (NTSC)" : 14017,
	"MPEG2-HPHL (NTSC)" : 14019,
	"MPEG2-422PML (NTSC)" : 14021,
	"MPEG2-HPHL (NTSC)" : 14023,
	"HDV 1080p (1080p/23.976)" : 14027,
	"HDV 720P (720p/23.976)" : 14028,
	"HDV 720P (720p/60)" : 14029,
	"XDCAM HD 35Mbits (1080i/50)" : 14043,
	"XDCAM HD 35Mbits (1080i/60)" : 14044,
	"XDCAM HD 35Mbits (1080p/23.976)" : 14045,
	"XDCAM HD 25Mbits (HD1080i)" : 14046,
	"XDCAM HD 25Mbits (HD1080i)" : 14047,
	"XDCAM HD 17.5Mbits (1080i/50)" : 14049,
	"XDCAM HD 17.5Mbits (1080i/60)" : 14050,
	"XDCAM HD 17.5Mbits (1080p/23.97" : 14051,
	"XDCAM HD 25Mbits (1080p/23.976)" : 14052,
	"HDV 720P (720p/25)" : 14062,
	"XDCAM HD 50Mbits (1080i/60)" : 14073,
	"XDCAM HD 50Mbits (1080i/50)" : 14074,
	"XDCAM HD 50Mbits (1080p/29.97)" : 14075,
	"XDCAM HD 50Mbits (1080p/25)" : 14076,
	"XDCAM HD 50Mbits (1080p/23.976)" : 14077,
	"XDCAM HD 50Mbits (720p/60)" : 14078,
	"XDCAM EX 35Mbits (1080i/60)" : 14080,
	"XDCAM EX 35Mbits (1080i/50)" : 14081,
	"XDCAM EX 35Mbits (1080p/29.97)" : 14082,
	"XDCAM EX 35Mbits (1080p/25)" : 14083,
	"XDCAM EX 35Mbits (1080p/23.976)" : 14084,
	"XDCAM EX 35Mbits (720p/60)" : 14085,
	"XDCAM EX 35Mbits (720p/23.976)" : 14087,
	"XDCAM EX 35Mbits (720p/29.97)" : 14088,
	"XDCAM EX 35Mbits (720p/25)" : 14089,
	"XDCAM HD 50Mbits (720p/25)" : 14091,
	"XDCAM HD 50Mbits (720p/29.97)" : 14092,
	"XDCAM HD 25Mbits (1080p/29.97)" : 14105,
	"Unsupported (HD1080p)" : 14500,
	"Unsupported (HD1080p)" : 14503,
	"Unsupported (HD1080p)" : 14505,
	"Unsupported (HD1080p)" : 14508,
	"Unsupported (HD1080p)" : 14510,
	"Unsupported (HD1080p)" : 14514,
	"Unsupported (HD1080p)" : 14516,
	"Unsupported (HD1080p)" : 14520,
	"32 kHz/16 Bit" : 20032,
	"32 kHz/24 Bit" : 20033,
	"32 kHz/16 Bit" : 20082,
	"32 kHz/24 Bit" : 20083,
	"44.1 kHz/16 Bit" : 20132,
	"44.1 kHz/24 Bit" : 20133,
	"48 kHz/16 Bit" : 20182,
	"48 kHz/24 Bit" : 20183,
	"88.2 kHz/16 Bit" : 20232,
	"88.2 kHz/24 Bit" : 20233,
	"96 kHz/16 Bit" : 20282,
	"96 kHz/24 Bit" : 20283,
	"32 kHz/16 Bit" : 20322,
	"32 kHz/24 Bit" : 20323,
	"44.1 kHz/16 Bit" : 20392,
	"44.1 kHz/24 Bit" : 20393,
	"48 kHz/16 Bit" : 20462,
	"48 kHz/24 Bit" : 20463,
	"88.2 kHz/16 Bit" : 20532,
	"88.2 kHz/24 Bit" : 20533,
	"96 kHz/16 Bit" : 20602,
	"96 kHz/24 Bit" : 20603,
	"DNxHD HQ (HD1080i)" : 27636,
	"DNxUncompressed 4:2:2 32bit flo" : 27637,
	"DNxHD SQ (HD1080i)" : 27638,
	"DNxHD SQ (HD1080p)" : 27639,
	"DNxHD LB (HD1080p)" : 27640,
	"DNxHD SQ (HD1080p)" : 27641,
	"DNxUncompressed 4:2:2 32bit flo" : 27642,
	"DNxUncompressed 4:2:2 10bit" : 27643,
	"DNxUncompressed 4:2:2 12bit" : 27644,
	"DNxUncompressed 4:2:2 8bit" : 27645,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27646,
	"DNxHD LB (HD1080p)" : 27647,
	"DNxUncompressed 4:2:2 8bit (HD1" : 27648,
	"DNxUncompressed 4:2:2 32bit flo" : 27649,
	"DNxUncompressed 4:2:2 10bit" : 27650,
	"DNxUncompressed 4:2:2 12bit" : 27651,
	"DNxUncompressed 4:2:2 8bit" : 27652,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27653,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27654,
	"J2K HD (HD1080p)" : 27655,
	"Apple ProRes 422 Proxy (HD1080p" : 27656,
	"Apple ProRes 422 LT (HD1080p)" : 27657,
	"Apple ProRes 422 (HD1080p)" : 27658,
	"Apple ProRes 422 HQ (HD1080p)" : 27659,
	"J2K IMF YCrCb (HD1080p)" : 27660,
	"J2K IMF YCrCb (HD1080p)" : 27661,
	"DNxUncompressed 4:2:2 32bit flo" : 27662,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27663,
	"J2K HD (HD1080p)" : 27664,
	"Apple ProRes 422 Proxy (HD1080p" : 27665,
	"Apple ProRes 422 LT (HD1080p)" : 27666,
	"Apple ProRes 422 (HD1080p)" : 27667,
	"Apple ProRes 422 HQ (HD1080p)" : 27668,
	"J2K IMF YCrCb (HD1080p)" : 27669,
	"AVC Long GOP 35 (HD1080p)" : 27670,
	"XAVC HD Intra CBG Class 200 (HD" : 27671,
	"XAVC HD Intra CBG Class 100 (HD" : 27672,
	"XAVC HD Intra CBG Class 200 (HD" : 27673,
	"Apple ProRes 422 Proxy (HD720p)" : 27675,
	"Apple ProRes 422 LT (HD720p)" : 27676,
	"Apple ProRes 422 (HD720p)" : 27677,
	"Apple ProRes 422 HQ (HD720p)" : 27678,
	"J2K HD (HD720p)" : 27679,
	"DNxHD LB (HD1080p)" : 27680,
	"DNxHD SQ (HD1080p)" : 27681,
	"DNxHD HQ (HD1080p)" : 27682,
	"DNxUncompressed 4:2:2 8bit (HD1" : 27683,
	"DNxUncompressed 4:2:2 10bit (HD" : 27684,
	"DNxUncompressed 4:2:2 12bit (HD" : 27685,
	"DNxUncompressed 4:2:2 32bit flo" : 27686,
	"DNxUncompressed 4:2:2 8bit (HD1" : 27687,
	"DNxUncompressed 4:2:2 10bit (HD" : 27688,
	"DNxUncompressed 4:2:2 12bit (HD" : 27689,
	"DNxUncompressed 4:2:2 32bit flo" : 27690,
	"H.264 800Kbps Proxy (HD1080p)" : 27691,
	"Apple ProRes 422 Proxy (HD1080p" : 27692,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27693,
	"Apple ProRes 422 (HD1080p)" : 27694,
	"Apple ProRes 422 HQ (HD1080p)" : 27695,
	"J2K IMF YCrCb (HD1080p)" : 27696,
	"AVC Long GOP 50 (HD1080p)" : 27697,
	"Apple ProRes 422 LT (HD1080p)" : 27698,
	"DNxHD SQ (HD720p)" : 27699,
	"DNxHD HQ (HD720p)" : 27700,
	"DNxHD HQX (HD720p)" : 27701,
	"DNxHD TR (HD720p)" : 27702,
	"DNxHD TR (HD1080p)" : 27703,
	"DNxUncompressed 4:2:2 32bit flo" : 27704,
	"DNxHD SQ (HD1080p)" : 27705,
	"DNxUncompressed 4:2:2 8bit (HD7" : 27706,
	"DNxUncompressed 4:2:2 10bit (HD" : 27707,
	"DNxUncompressed 4:2:2 12bit (HD" : 27708,
	"DNxUncompressed 4:2:2 32bit flo" : 27709,
	"DNxHD HQX (HD720p)" : 27710,
	"DNxUncompressed 4:2:2 8bit (HD1" : 27711,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27712,
	"J2K HD (HD720p)" : 27713,
	"Apple ProRes 422 Proxy (HD720p)" : 27714,
	"Apple ProRes 422 LT (HD720p)" : 27715,
	"Apple ProRes 422 (HD720p)" : 27716,
	"Apple ProRes 422 HQ (HD720p)" : 27717,
	"DNxHD HQX (HD1080i)" : 27718,
	"J2K HD (HD1080p)" : 27719,
	"H.264 800Kbps Proxy (HD1080p)" : 27720,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27721,
	"DNxHD TR (HD720p)" : 27722,
	"Apple ProRes 422 (HD1080p)" : 27723,
	"XAVC HD Intra CBG Class 100 (HD" : 27724,
	"AVC Long GOP 6 (HD1080i)" : 27725,
	"AVC Long GOP 12 (HD1080i)" : 27726,
	"AVC Long GOP 25 (HD1080i)" : 27727,
	"AVC Long GOP 50 (HD1080i)" : 27728,
	"AVC Long GOP 50 (HD1080p)" : 27729,
	"AVC Long GOP 35 (HD1080p)" : 27731,
	"DNxUncompressed 4:2:2 8bit (HD1" : 27732,
	"DNxUncompressed 4:2:2 10bit (HD" : 27733,
	"DNxUncompressed 4:2:2 12bit (HD" : 27734,
	"DNxUncompressed 4:2:2 32bit flo" : 27735,
	"DNxUncompressed 4:2:2 32bit flo" : 27736,
	"DNxUncompressed 4:2:2 10bit" : 27737,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27738,
	"J2K HD (HD1080i)" : 27739,
	"Apple ProRes 422 Proxy (HD1080i" : 27740,
	"Apple ProRes 422 LT (HD1080i)" : 27741,
	"Apple ProRes 422 (HD1080i)" : 27742,
	"Apple ProRes 422 HQ (HD1080i)" : 27743,
	"AVC Long GOP 35 (HD1080i)" : 27744,
	"XAVC HD Intra CBG Class 200 (HD" : 27745,
	"XAVC HD Intra CBG Class 100 (HD" : 27746,
	"DNxHD TR (HD1080i)" : 27747,
	"DNxHD TR+ (HD1080i)" : 27748,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27750,
	"J2K HD (HD1080p)" : 27751,
	"Apple ProRes 422 Proxy (HD1080p" : 27752,
	"Apple ProRes 422 LT (HD1080p)" : 27753,
	"Apple ProRes 422 (HD1080p)" : 27754,
	"Apple ProRes 422 HQ (HD1080p)" : 27755,
	"J2K HD (HD1080p)" : 27756,
	"J2K IMF YCrCb (HD1080p)" : 27757,
	"DNxHD SQ (HD1080p)" : 27758,
	"DNxUncompressed 4:2:2 8bit (HD7" : 27759,
	"DNxUncompressed 4:2:2 10bit (HD" : 27760,
	"XDCAM EX 35 (HD1080p)" : 27761,
	"XDCAM HD 50 (HD1080p)" : 27762,
	"DNxUncompressed 4:2:2 8bit (HD1" : 27763,
	"DNxUncompressed 4:2:2 10bit (HD" : 27764,
	"XAVC HD Intra CBG Class 50 (HD1" : 27765,
	"XAVC HD Intra CBG Class 50 (HD1" : 27766,
	"Apple ProRes 422 Proxy (HD720p)" : 27767,
	"Apple ProRes 422 LT (HD720p)" : 27768,
	"DNxHD LB (HD1080p)" : 27769,
	"DNxHD SQ (HD1080p)" : 27770,
	"DNxHD HQ (HD1080p)" : 27771,
	"DNxHD HQX (HD1080p)" : 27772,
	"Apple ProRes 422 (HD1080p)" : 27773,
	"Apple ProRes 422 HQ (HD1080p)" : 27774,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27775,
	"J2K HD (HD1080p)" : 27776,
	"DNxUncompressed 4:2:2 8bit (HD1" : 27777,
	"DNxUncompressed 4:2:2 10bit (HD" : 27778,
	"DNxUncompressed 4:2:2 12bit (HD" : 27779,
	"DNxUncompressed 4:2:2 32bit flo" : 27780,
	"AVC Long GOP 50 (HD1080i)" : 27781,
	"AVC Long GOP 6 (HD1080p)" : 27782,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27783,
	"AVC Long GOP 25 (HD1080p)" : 27784,
	"AVC Long GOP 50 (HD1080p)" : 27785,
	"DNxUncompressed 4:2:2 10bit (HD" : 27786,
	"DNxUncompressed 4:2:2 12bit (HD" : 27787,
	"DNxUncompressed 4:2:2 32bit flo" : 27788,
	"DNxUncompressed 4:2:2 10bit (HD" : 27789,
	"XDCAM EX 35 (HD1080p)" : 27790,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27791,
	"J2K HD (HD1080i)" : 27792,
	"Apple ProRes 422 Proxy (HD1080i" : 27793,
	"Apple ProRes 422 LT (HD1080i)" : 27794,
	"Apple ProRes 422 (HD1080i)" : 27795,
	"Apple ProRes 422 HQ (HD1080i)" : 27796,
	"AVC Long GOP 35 (HD1080i)" : 27797,
	"XAVC HD Intra CBG Class 200 (HD" : 27798,
	"XAVC HD Intra CBG Class 100 (HD" : 27799,
	"DNxHD TR (HD1080i)" : 27800,
	"DNxHD TR+ (HD1080i)" : 27801,
	"Apple ProRes 422 (HD1080p)" : 27802,
	"AVC Long GOP 35 (HD1080p)" : 27803,
	"XAVC HD Intra CBG Class 200 (HD" : 27804,
	"XAVC HD Intra CBG Class 100 (HD" : 27805,
	"DNxHD TR (HD1080p)" : 27806,
	"DNxHD TR+ (HD1080p)" : 27807,
	"Apple ProRes 422 HQ (HD1080p)" : 27808,
	"DNxHD SQ (HD720p)" : 27810,
	"DNxHD HQ (HD720p)" : 27811,
	"DNxHD HQX (HD720p)" : 27812,
	"XDCAM HD 35 (HD1080p)" : 27813,
	"XDCAM HD 25 (HD1080p)" : 27814,
	"XDCAM HD 17.5 (HD1080p)" : 27815,
	"AVC Long GOP 6 (HD1080p)" : 27816,
	"DNxUncompressed 4:2:2 8bit (HD7" : 27817,
	"XAVC HD Intra CBG Class 50 (HD1" : 27818,
	"DNxUncompressed 4:2:2 12bit (HD" : 27819,
	"DNxUncompressed 4:2:2 32bit flo" : 27820,
	"XDCAM HD 35 (HD1080p)" : 27821,
	"XDCAM HD 25 (HD1080p)" : 27822,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27823,
	"J2K HD (HD720p)" : 27824,
	"Apple ProRes 422 Proxy (HD720p)" : 27825,
	"Apple ProRes 422 LT (HD720p)" : 27826,
	"XAVC HD Intra CBG Class 50 (HD1" : 27827,
	"Apple ProRes 422 HQ (HD720p)" : 27828,
	"DNxHD HQX (HD1080i)" : 27829,
	"DNxUncompressed 4:2:2 10bit (HD" : 27830,
	"DNxUncompressed 4:2:2 12bit (HD" : 27831,
	"DNxUncompressed 4:2:2 32bit flo" : 27832,
	"XAVC HD Intra CBG Class 200 (HD" : 27833,
	"XAVC HD Intra CBG Class 100 (HD" : 27834,
	"XAVC HD Intra CBG Class 50 (HD1" : 27835,
	"AVC Long GOP 6 (HD1080i)" : 27836,
	"AVC Long GOP 12 (HD1080i)" : 27837,
	"AVC Long GOP 25 (HD1080i)" : 27838,
	"AVC Long GOP 50 (HD1080i)" : 27839,
	"Apple ProRes 422 HQ (HD1080i)" : 27840,
	"AVC Long GOP 35 (HD1080i)" : 27841,
	"XAVC HD Intra CBG Class 200 (HD" : 27842,
	"DNxUncompressed 4:2:2 8bit (HD1" : 27843,
	"DNxUncompressed 4:2:2 10bit (HD" : 27844,
	"DNxUncompressed 4:2:2 12bit (HD" : 27845,
	"DNxUncompressed 4:2:2 32bit flo" : 27846,
	"XDCAM HD 17.5 (HD1080p)" : 27847,
	"DNxUncompressed 4:2:2 32bit flo" : 27848,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27849,
	"J2K HD (HD1080i)" : 27850,
	"Apple ProRes 422 Proxy (HD1080i" : 27851,
	"Apple ProRes 422 LT (HD1080i)" : 27852,
	"Apple ProRes 422 (HD1080i)" : 27853,
	"Apple ProRes 422 HQ (HD1080i)" : 27854,
	"AVC Long GOP 35 (HD1080i)" : 27855,
	"XAVC HD Intra CBG Class 200 (HD" : 27856,
	"XAVC HD Intra CBG Class 100 (HD" : 27857,
	"DNxHD TR (HD1080i)" : 27858,
	"DNxHD TR+ (HD1080i)" : 27859,
	"XAVC HD Intra CBG Class 50 (HD1" : 27860,
	"DNxHD TR+ (HD1080i)" : 27861,
	"DNxUncompressed 4:2:2 12bit (HD" : 27862,
	"DNxUncompressed 4:2:2 32bit flo" : 27863,
	"DNxUncompressed 4:2:2 32bit flo" : 27864,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27866,
	"J2K HD (HD1080i)" : 27867,
	"Apple ProRes 422 Proxy (HD1080i" : 27868,
	"DNxHD TR (HD1080i)" : 27869,
	"DNxHD TR+ (HD1080i)" : 27870,
	"Apple ProRes 422 HQ (HD1080i)" : 27871,
	"AVC Long GOP 35 (HD1080i)" : 27872,
	"XAVC HD Intra CBG Class 200 (HD" : 27873,
	"XAVC HD Intra CBG Class 100 (HD" : 27874,
	"DNxHD TR (HD1080i)" : 27875,
	"XAVC HD Intra CBG Class 50 (HD1" : 27876,
	"XDCAM HD 25 (HD1080i)" : 27877,
	"XAVC HD Intra CBG Class 50 (HD1" : 27878,
	"XAVC HD Intra CBG Class 100 (HD" : 27879,
	"DNxHD TR (HD1080p)" : 27880,
	"DNxHD TR+ (HD1080p)" : 27881,
	"AVC Long GOP 50 (HD1080i)" : 27882,
	"DNxUncompressed 4:2:2 8bit (HD1" : 27886,
	"XDCAM HD 35 (HD1080p)" : 27887,
	"XDCAM HD 25 (HD1080p)" : 27888,
	"XDCAM HD 17.5 (HD1080p)" : 27889,
	"XAVC HD Intra CBG Class 50 (HD1" : 27890,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27892,
	"XAVC HD Intra CBG Class 50 (HD1" : 27893,
	"Apple ProRes 422 Proxy (HD1080i" : 27894,
	"Apple ProRes 422 LT (HD1080i)" : 27895,
	"Apple ProRes 422 (HD1080i)" : 27896,
	"Apple ProRes 422 HQ (HD1080i)" : 27897,
	"AVC Long GOP 35 (HD1080i)" : 27898,
	"XAVC HD Intra CBG Class 200 (HD" : 27899,
	"XAVC HD Intra CBG Class 100 (HD" : 27900,
	"XAVC HD Intra CBG Class 50 (HD1" : 27901,
	"XAVC HD Intra CBG Class 50 (HD1" : 27917,
	"DNxHD LB (HD1080p)" : 27926,
	"DNxHD SQ (HD1080p)" : 27927,
	"DNxHD HQ (HD1080p)" : 27928,
	"DNxHD HQX (HD1080p)" : 27929,
	"DNxUncompressed 4:2:2 8bit (HD1" : 27934,
	"DNxUncompressed 4:2:2 10bit (HD" : 27935,
	"DNxUncompressed 4:2:2 12bit (HD" : 27936,
	"DNxUncompressed 4:2:2 32bit flo" : 27937,
	"DNxUncompressed 4:2:2 16(2.14)b" : 27940,
	"J2K HD (HD1080p)" : 27941,
	"Apple ProRes 422 Proxy (HD1080p" : 27942,
	"Apple ProRes 422 LT (HD1080p)" : 27943,
	"Apple ProRes 422 (HD1080p)" : 27944,
	"Apple ProRes 422 HQ (HD1080p)" : 27945,
	"J2K IMF YCrCb (HD1080p)" : 27946,
	"Data" : 30001,
}
"""Known values from bin view column `type` property"""