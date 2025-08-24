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
	
class BinColumnFormat(enum.Enum):
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
	
BIN_COLUMN_ROLES:dict[int, str] = {
    1 : "Tracks",
    2 : "Start",
    3 : "End",
    4 : "Duration",
    5 : "Mark IN",
    6 : "Mark OUT",
    7 : "IN-OUT",
    8 : "Tape",
    9 : "FPS",
   10 : "CFPS",
   11 : "Audio SR",
   12 : "Creation Date",
   13 : "Video",
   14 : "Drive",
   15 : "KN Start",
   16 : "KN End",
   17 : "KN Dur",
   18 : "KN Mark IN",
   19 : "KN Mark OUT",
   20 : "KN IN-OUT",
   21 : "Pullin",
   22 : "Pullout",
   23 : "Film TC",
   24 : "Sound TC",
   25 : "Auxiliary TC1",
   26 : "Auxiliary TC2",
   27 : "Auxiliary TC3",
   28 : "Auxiliary TC4",
   29 : "Auxiliary TC5",
   30 : "Ink Number",
   31 : "VITC",
   32 : "Color Framing",
   33 : "Auxiliary EC1",
   35 : "Offline",
   36 : "Frame",
   37 : "Auxiliary Ink",
   38 : "Reel #",
   39 : "Scene",
   41 : "Take",
   42 : "Soundroll",
   43 : "Camroll",
   44 : "Shoot Date",
   45 : "Labroll",
   46 : "Camera",
   47 : "Slip",
   48 : "Lock",
   49 : "Perf",
   50 : "TapeID",
   51 : "Color",
   52 : "Film",
   53 : "Media File",
   54 : "Modified Date",
   55 : "Audio Format",
   56 : "TC 24",
   57 : "TC 25PD",
   58 : "TC 25",
   59 : "TC 30",
   61 : "Audio Bit Depth",
   62 : "Cadence",
   63 : "Aux TC 24",
   64 : "Video File Format",
   65 : "Format",
   66 : "AuxInk Dur",
   67 : "AuxInk Edge",
   68 : "AuxInk End",
   69 : "AuxInk Film",
   70 : "DPX",
   71 : "VFX",
   72 : "VFX Reel",
   73 : "Ink Dur",
   74 : "Ink Edge",
   75 : "Ink End",
   76 : "Ink Film",
   78 : "KN Film",
   79 : "LUT",
   80 : "Master Dur",
   81 : "Master Edge",
   82 : "Master End",
   83 : "Master Film",
   84 : "Master Start",
   85 : "Transfer",
   86 : "UNC Path",
   87 : "TC 30NP",
   88 : "TC 60",
   89 : "Disk Label",
   90 : "Journalist",
   91 : "Production",
   92 : "IDataLink",
   93 : "ASC_SOP",
   94 : "ASC_SAT",
   95 : "Field Motion",
   96 : "Track Formats",
   97 : "Color Space",
   98 : "Image Aspect Ratio",
   99 : "Pixel Aspect Ratio",
  100 : "Reformat",
  101 : "Source File",
  102 : "Ancillary Data",
  103 : "Color Transformation",
  104 : "S3D Clip Name",
  105 : "Source Path",
  106 : "S3D Contributors",
  107 : "S3D Leading Eye",
  108 : "S3D Channel",
  109 : "S3D Group Name",
  110 : "S3D Inversion",
  111 : "S3D InversionR",
  112 : "S3D Eye Order",
  113 : "Vendor Name",
  114 : "Vendor URL",
  115 : "Vendor Asset ID",
  116 : "Vendor Asset Name",
  117 : "Vendor Asset Rights",
  118 : "Vendor Asset Price",
  119 : "Vendor Original Master",
  120 : "Vendor Asset Description",
  121 : "Vendor Asset Keywords",
  122 : "Vendor Asset Status",
  123 : "Vendor Invoice ID",
  124 : "Vendor Download Master",
  125 : "S3D Alignment",
  127 : "Image Framing",
  128 : "Raster Dimension",
  129 : "Image Size",
  130 : "Media Status",
  131 : "AFD",
  132 : "Marker",
  133 : "Plug-in",
  134 : "Reel",
  135 : "Frame Count Start",
  136 : "Frame Count End",
  137 : "Frame Count Duration",
  139 : "Video Data Rate",
  141 : "BIN Start",
  142 : "BIN End",
  143 : "BIN Tracks",
  144 : "Chroma Subsampling",
  145 : "Media File Path",
  146 : "Proxy Offline",
  147 : "Proxy Audio",
  148 : "Proxy Video",
  149 : "Proxy Path",
  150 : "Invert Alpha",
  151 : "Ignore Alpha",
  152 : "Premult Alpha",
  153 : "Alpha Channel",
  154 : "Alpha Mode",
  155 : "Alpha Mode",
  156 : "Transcription",
  200 : "",
  201 : "Name",
  204 : "Project",
10075 : "10:1 (NTSC)",
10076 : "2:1 (NTSC)",
10077 : "3:1 (NTSC)",
10078 : "15:1s (NTSC)",
10079 : "4:1s (NTSC)",
10080 : "2:1s (NTSC)",
10082 : "20:1 (NTSC)",
10097 : "3:1 (NTSC)",
10098 : "2:1 (NTSC)",
10102 : "35:1 (NTSC)",
10103 : "14:1 (NTSC)",
10104 : "28:1 (NTSC)",
10110 : "10:1m (NTSC)",
10111 : "4:1m (NTSC)",
10112 : "8:1m (NTSC)",
10113 : "3:1m (NTSC)",
10140 : "DV 25 411 (NTSC)",
10141 : "DV 25 420 i(PAL)",
10142 : "DV 50 (NTSC)",
10143 : "DV25P 411 (NTSC)",
10144 : "DV 25P 420 (PAL)",
10147 : "DV50P (NTSC)",
10151 : "1:1 (NTSC)",
10152 : "1:1 (NTSC)",
10160 : "MPEG 50 (NTSC)",
10161 : "MPEG 40 (NTSC)",
10162 : "MPEG 30 (NTSC)",
10170 : "1:1 (NTSC)",
10171 : "1:1 (NTSC)",
10550 : "J2K 1080i 59.94 (HD1080i)",
10551 : "J2K 1080p 23.976 (HD1080p)",
10552 : "J2K 720p 59.94 (HD720p)",
10553 : "J2K NTSCi 29.97 (NTSC)",
10554 : "J2K NTSCp 23.976 (NTSC)",
10555 : "J2K PALi 25 i(PAL)",
10556 : "J2K PALp 25 (PAL)",
10557 : "J2K 1080i 50 (HD1080i)",
10558 : "J2K 1080p 29.97 (HD1080p)",
10559 : "J2K 1080p 25 (HD1080p)",
10560 : "J2K 1080p 24 (HD1080p)",
10562 : "J2K 720p 29.97 (HD720p)",
10563 : "J2K 720p 25 (HD720p)",
10564 : "J2K 720p 23.976 (HD720p)",
10565 : "J2K NTSCp 24 (NTSC)",
10566 : "J2K PALp 24 (PAL)",
11235 : "DNxHD 175 X (HD1080p)",
11237 : "DNxHD 115 (HD1080p)",
11238 : "DNxHD 175 (HD1080p)",
11241 : "DNxHD 175 X (HD1080i)",
11242 : "DNxHD 115 (HD1080i)",
11243 : "DNxHD 175 (HD1080i)",
11244 : "DNxHD-TR 115 (HD1080i)",
11250 : "DNxHD 90 X (HD720p)",
11251 : "DNxHD 90 (HD720p)",
11252 : "DNxHD 60 (HD720p)",
11253 : "DNxHD 36 (HD1080p)",
11256 : "DNxHD 444 350 X (HD1080p)",
11258 : "DNxHD 50 (HD720p)",
11259 : "DNxHD 80 (HD1080p)",
11260 : "DNxHD 80 (HD1080i)",
11500 : "MPEG-4 525",
11501 : "MPEG-4 625",
11502 : "MPEG-4 (NTSC)",
11503 : "MPEG-4 (PAL)",
11505 : "MPEG-4 525 750 60 (NTSC)",
11507 : "MPEG-4 525p 23.976 750 (NTSC)",
11509 : "MPEG-4 525 500 60 (NTSC)",
11510 : "MPEG-4 625 500 50 i(PAL)",
11511 : "MPEG-4 525p 23.976 500 (NTSC)",
12000 : "1:1 10b (HD1080i)",
12003 : "1:1p 10b (HD1080p)",
12004 : "1:1p 10b (HD720p)",
12021 : "1:1 10b (NTSC)",
12022 : "1:1 10b i(PAL)",
12023 : "1:1 10b (NTSC)",
12024 : "1:1 10b (PAL)",
12125 : "1:1 (HD1080i)",
12126 : "1:1 (HD1080p)",
12127 : "1:1 (HD720p)",
12400 : "DVCPro HD (1080i/50)",
12401 : "DVCPro HD (1080i/60)",
12402 : "DVCPro HD (720p/60)",
12403 : "DVCPro HD (720p/50)",
12500 : "1:1 10b RGB (HD1080i)",
12503 : "1:1 10b RGB (HD1080p)",
13402 : "AVC-Intra 50 (HD720p)",
13403 : "AVC-Intra 50 (HD720p)",
13404 : "AVC-Intra 50 (HD720p)",
13405 : "AVC-Intra 50 (HD1080i)",
13406 : "AVC-Intra 50 (HD1080i)",
13409 : "AVC-Intra 50 (HD1080p)",
13411 : "AVC-Intra 100 (HD720p)",
13412 : "AVC-Intra 100 (HD720p)",
13413 : "AVC-Intra 100 (HD720p)",
13414 : "AVC-Intra 100 (HD720p)",
13415 : "AVC-Intra 100 (HD1080i)",
13416 : "AVC-Intra 100 (HD1080i)",
13417 : "AVC-Intra 100 (HD1080p)",
13418 : "AVC-Intra 100 (HD1080p)",
13419 : "AVC-Intra 100 (HD1080p)",
13420 : "XAVC Intra 50 (HD1080i)",
13421 : "XAVC Intra 50 (HD1080i)",
13422 : "XAVC Intra 50 (HD1080p)",
13425 : "XAVC Intra 100 (HD1080i)",
13426 : "XAVC Intra 100 (HD1080i)",
13427 : "XAVC Intra 100 (HD1080p)",
13428 : "XAVC Intra 100 (HD1080p)",
13429 : "XAVC Intra 100 (HD1080p)",
13450 : "AVCIBP-BLL2.0 (NTSC)",
13451 : "AVCIBP-BLL2.0 i(PAL)",
13457 : "AVCIBP-BLL3.0 (HD720p)",
13470 : "H.264 800Kbps Proxy (NTSC)",
13471 : "H.264 800Kbps Proxy i(PAL)",
13472 : "H.264 800Kbps Proxy (HD1080i)",
13473 : "H.264 800Kbps Proxy (HD1080i)",
13474 : "H.264 800Kbps Proxy (HD720p)",
13476 : "H.264 2.0Mbps Proxy (HD1080i)",
13477 : "H.264 2.0Mbps Proxy (HD1080i)",
13478 : "H.264 2.0Mbps Proxy (HD720p)",
13480 : "H.264 800Kbps Proxy (NTSC)",
13481 : "H.264 800Kbps Proxy (NTSC)",
13482 : "H.264 800Kbps Proxy (PAL)",
13483 : "H.264 800Kbps Proxy (PAL)",
13484 : "H.264 800Kbps Proxy (HD1080p)",
13485 : "H.264 800Kbps Proxy (HD1080p)",
13486 : "H.264 800Kbps Proxy (HD1080p)",
13487 : "H.264 800Kbps Proxy (HD1080p)",
13488 : "H.264 800Kbps Proxy (HD720p)",
13489 : "H.264 800Kbps Proxy (HD720p)",
13490 : "H.264 800Kbps Proxy (HD720p)",
13491 : "H.264 1500Kbps Proxy (NTSC)",
13492 : "H.264 1500Kbps Proxy i(PAL)",
13700 : "Apple ProRes HQ (NTSC)",
13702 : "Apple ProRes HQ i(PAL)",
13703 : "Apple ProRes HQ (PAL)",
13705 : "Apple ProRes HQ (HD720p)",
13709 : "Apple ProRes HQ (NTSC)",
13710 : "Apple ProRes HQ (HD1080p)",
13712 : "Apple ProRes HQ (HD1080i)",
13721 : "Apple ProRes LT (HD720p)",
13723 : "Apple ProRes LT (HD1080p)",
13725 : "Apple ProRes LT (HD1080i)",
13726 : "Apple ProRes LT (NTSC)",
13727 : "Apple ProRes LT (PAL)",
13728 : "Apple ProRes LT i(PAL)",
13729 : "Apple ProRes LT (NTSC)",
13740 : "Apple ProRes (NTSC)",
13743 : "Apple ProRes (NTSC)",
13745 : "Apple ProRes i(PAL)",
13746 : "Apple ProRes (PAL)",
13748 : "Apple ProRes (HD720p)",
13750 : "Apple ProRes (HD1080p)",
13752 : "Apple ProRes (HD1080i)",
13784 : "Apple ProRes 4444 (NTSC)",
13790 : "Apple ProRes 4444 (HD1080p)",
13802 : "Apple ProRes Proxy (NTSC)",
13803 : "Apple ProRes Proxy (NTSC)",
13804 : "Apple ProRes Proxy i(PAL)",
13805 : "Apple ProRes Proxy (PAL)",
13807 : "Apple ProRes Proxy (HD720p)",
13809 : "Apple ProRes Proxy (HD1080p)",
13811 : "Apple ProRes Proxy (HD1080i)",
14000 : "MPEG2-MPML (NTSC)",
14001 : "MPEG2-422ML (NTSC)",
14002 : "HDV 720P (720p/30)",
14003 : "HDV 1080i (1080i/50)",
14004 : "HDV 1080i (1080i/60)",
14005 : "MPEG1 (NTSC)",
14007 : "MPEG2 352_25I i(PAL)",
14008 : "MPEG2 352_30I (NTSC)",
14009 : "MPEG2-MPML (NTSC)",
14011 : "MPEG2-MPHi1440 (NTSC)",
14013 : "MPEG2-MPHL (NTSC)",
14015 : "MPEG2-HPML (NTSC)",
14017 : "MPEG2-HPHi1440 (NTSC)",
14019 : "MPEG2-HPHL (NTSC)",
14021 : "MPEG2-422PML (NTSC)",
14023 : "MPEG2-HPHL (NTSC)",
14027 : "HDV 1080p (1080p/23.976)",
14028 : "HDV 720P (720p/23.976)",
14029 : "HDV 720P (720p/60)",
14043 : "XDCAM HD 35Mbits (1080i/50)",
14044 : "XDCAM HD 35Mbits (1080i/60)",
14045 : "XDCAM HD 35Mbits (1080p/23.976)",
14046 : "XDCAM HD 25Mbits (HD1080i)",
14047 : "XDCAM HD 25Mbits (HD1080i)",
14049 : "XDCAM HD 17.5Mbits (1080i/50)",
14050 : "XDCAM HD 17.5Mbits (1080i/60)",
14051 : "XDCAM HD 17.5Mbits (1080p/23.97",
14052 : "XDCAM HD 25Mbits (1080p/23.976)",
14062 : "HDV 720P (720p/25)",
14073 : "XDCAM HD 50Mbits (1080i/60)",
14074 : "XDCAM HD 50Mbits (1080i/50)",
14075 : "XDCAM HD 50Mbits (1080p/29.97)",
14076 : "XDCAM HD 50Mbits (1080p/25)",
14077 : "XDCAM HD 50Mbits (1080p/23.976)",
14078 : "XDCAM HD 50Mbits (720p/60)",
14080 : "XDCAM EX 35Mbits (1080i/60)",
14081 : "XDCAM EX 35Mbits (1080i/50)",
14082 : "XDCAM EX 35Mbits (1080p/29.97)",
14083 : "XDCAM EX 35Mbits (1080p/25)",
14084 : "XDCAM EX 35Mbits (1080p/23.976)",
14085 : "XDCAM EX 35Mbits (720p/60)",
14087 : "XDCAM EX 35Mbits (720p/23.976)",
14088 : "XDCAM EX 35Mbits (720p/29.97)",
14089 : "XDCAM EX 35Mbits (720p/25)",
14091 : "XDCAM HD 50Mbits (720p/25)",
14092 : "XDCAM HD 50Mbits (720p/29.97)",
14105 : "XDCAM HD 25Mbits (1080p/29.97)",
14500 : "Unsupported (HD1080p)",
14503 : "Unsupported (HD1080p)",
14505 : "Unsupported (HD1080p)",
14508 : "Unsupported (HD1080p)",
14510 : "Unsupported (HD1080p)",
14514 : "Unsupported (HD1080p)",
14516 : "Unsupported (HD1080p)",
14520 : "Unsupported (HD1080p)",
20032 : "32 kHz/16 Bit",
20033 : "32 kHz/24 Bit",
20082 : "32 kHz/16 Bit",
20083 : "32 kHz/24 Bit",
20132 : "44.1 kHz/16 Bit",
20133 : "44.1 kHz/24 Bit",
20182 : "48 kHz/16 Bit",
20183 : "48 kHz/24 Bit",
20232 : "88.2 kHz/16 Bit",
20233 : "88.2 kHz/24 Bit",
20282 : "96 kHz/16 Bit",
20283 : "96 kHz/24 Bit",
20322 : "32 kHz/16 Bit",
20323 : "32 kHz/24 Bit",
20392 : "44.1 kHz/16 Bit",
20393 : "44.1 kHz/24 Bit",
20462 : "48 kHz/16 Bit",
20463 : "48 kHz/24 Bit",
20532 : "88.2 kHz/16 Bit",
20533 : "88.2 kHz/24 Bit",
20602 : "96 kHz/16 Bit",
20603 : "96 kHz/24 Bit",
27636 : "DNxHD HQ (HD1080i)",
27637 : "DNxUncompressed 4:2:2 32bit flo",
27638 : "DNxHD SQ (HD1080i)",
27639 : "DNxHD SQ (HD1080p)",
27640 : "DNxHD LB (HD1080p)",
27641 : "DNxHD SQ (HD1080p)",
27642 : "DNxUncompressed 4:2:2 32bit flo",
27643 : "DNxUncompressed 4:2:2 10bit",
27644 : "DNxUncompressed 4:2:2 12bit",
27645 : "DNxUncompressed 4:2:2 8bit",
27646 : "DNxUncompressed 4:2:2 16(2.14)b",
27647 : "DNxHD LB (HD1080p)",
27648 : "DNxUncompressed 4:2:2 8bit (HD1",
27649 : "DNxUncompressed 4:2:2 32bit flo",
27650 : "DNxUncompressed 4:2:2 10bit",
27651 : "DNxUncompressed 4:2:2 12bit",
27652 : "DNxUncompressed 4:2:2 8bit",
27653 : "DNxUncompressed 4:2:2 16(2.14)b",
27654 : "DNxUncompressed 4:2:2 16(2.14)b",
27655 : "J2K HD (HD1080p)",
27656 : "Apple ProRes 422 Proxy (HD1080p",
27657 : "Apple ProRes 422 LT (HD1080p)",
27658 : "Apple ProRes 422 (HD1080p)",
27659 : "Apple ProRes 422 HQ (HD1080p)",
27660 : "J2K IMF YCrCb (HD1080p)",
27661 : "J2K IMF YCrCb (HD1080p)",
27662 : "DNxUncompressed 4:2:2 32bit flo",
27663 : "DNxUncompressed 4:2:2 16(2.14)b",
27664 : "J2K HD (HD1080p)",
27665 : "Apple ProRes 422 Proxy (HD1080p",
27666 : "Apple ProRes 422 LT (HD1080p)",
27667 : "Apple ProRes 422 (HD1080p)",
27668 : "Apple ProRes 422 HQ (HD1080p)",
27669 : "J2K IMF YCrCb (HD1080p)",
27670 : "AVC Long GOP 35 (HD1080p)",
27671 : "XAVC HD Intra CBG Class 200 (HD",
27672 : "XAVC HD Intra CBG Class 100 (HD",
27673 : "XAVC HD Intra CBG Class 200 (HD",
27675 : "Apple ProRes 422 Proxy (HD720p)",
27676 : "Apple ProRes 422 LT (HD720p)",
27677 : "Apple ProRes 422 (HD720p)",
27678 : "Apple ProRes 422 HQ (HD720p)",
27679 : "J2K HD (HD720p)",
27680 : "DNxHD LB (HD1080p)",
27681 : "DNxHD SQ (HD1080p)",
27682 : "DNxHD HQ (HD1080p)",
27683 : "DNxUncompressed 4:2:2 8bit (HD1",
27684 : "DNxUncompressed 4:2:2 10bit (HD",
27685 : "DNxUncompressed 4:2:2 12bit (HD",
27686 : "DNxUncompressed 4:2:2 32bit flo",
27687 : "DNxUncompressed 4:2:2 8bit (HD1",
27688 : "DNxUncompressed 4:2:2 10bit (HD",
27689 : "DNxUncompressed 4:2:2 12bit (HD",
27690 : "DNxUncompressed 4:2:2 32bit flo",
27691 : "H.264 800Kbps Proxy (HD1080p)",
27692 : "Apple ProRes 422 Proxy (HD1080p",
27693 : "DNxUncompressed 4:2:2 16(2.14)b",
27694 : "Apple ProRes 422 (HD1080p)",
27695 : "Apple ProRes 422 HQ (HD1080p)",
27696 : "J2K IMF YCrCb (HD1080p)",
27697 : "AVC Long GOP 50 (HD1080p)",
27698 : "Apple ProRes 422 LT (HD1080p)",
27699 : "DNxHD SQ (HD720p)",
27700 : "DNxHD HQ (HD720p)",
27701 : "DNxHD HQX (HD720p)",
27702 : "DNxHD TR (HD720p)",
27703 : "DNxHD TR (HD1080p)",
27704 : "DNxUncompressed 4:2:2 32bit flo",
27705 : "DNxHD SQ (HD1080p)",
27706 : "DNxUncompressed 4:2:2 8bit (HD7",
27707 : "DNxUncompressed 4:2:2 10bit (HD",
27708 : "DNxUncompressed 4:2:2 12bit (HD",
27709 : "DNxUncompressed 4:2:2 32bit flo",
27710 : "DNxHD HQX (HD720p)",
27711 : "DNxUncompressed 4:2:2 8bit (HD1",
27712 : "DNxUncompressed 4:2:2 16(2.14)b",
27713 : "J2K HD (HD720p)",
27714 : "Apple ProRes 422 Proxy (HD720p)",
27715 : "Apple ProRes 422 LT (HD720p)",
27716 : "Apple ProRes 422 (HD720p)",
27717 : "Apple ProRes 422 HQ (HD720p)",
27718 : "DNxHD HQX (HD1080i)",
27719 : "J2K HD (HD1080p)",
27720 : "H.264 800Kbps Proxy (HD1080p)",
27721 : "DNxUncompressed 4:2:2 16(2.14)b",
27722 : "DNxHD TR (HD720p)",
27723 : "Apple ProRes 422 (HD1080p)",
27724 : "XAVC HD Intra CBG Class 100 (HD",
27725 : "AVC Long GOP 6 (HD1080i)",
27726 : "AVC Long GOP 12 (HD1080i)",
27727 : "AVC Long GOP 25 (HD1080i)",
27728 : "AVC Long GOP 50 (HD1080i)",
27729 : "AVC Long GOP 50 (HD1080p)",
27731 : "AVC Long GOP 35 (HD1080p)",
27732 : "DNxUncompressed 4:2:2 8bit (HD1",
27733 : "DNxUncompressed 4:2:2 10bit (HD",
27734 : "DNxUncompressed 4:2:2 12bit (HD",
27735 : "DNxUncompressed 4:2:2 32bit flo",
27736 : "DNxUncompressed 4:2:2 32bit flo",
27737 : "DNxUncompressed 4:2:2 10bit",
27738 : "DNxUncompressed 4:2:2 16(2.14)b",
27739 : "J2K HD (HD1080i)",
27740 : "Apple ProRes 422 Proxy (HD1080i",
27741 : "Apple ProRes 422 LT (HD1080i)",
27742 : "Apple ProRes 422 (HD1080i)",
27743 : "Apple ProRes 422 HQ (HD1080i)",
27744 : "AVC Long GOP 35 (HD1080i)",
27745 : "XAVC HD Intra CBG Class 200 (HD",
27746 : "XAVC HD Intra CBG Class 100 (HD",
27747 : "DNxHD TR (HD1080i)",
27748 : "DNxHD TR+ (HD1080i)",
27750 : "DNxUncompressed 4:2:2 16(2.14)b",
27751 : "J2K HD (HD1080p)",
27752 : "Apple ProRes 422 Proxy (HD1080p",
27753 : "Apple ProRes 422 LT (HD1080p)",
27754 : "Apple ProRes 422 (HD1080p)",
27755 : "Apple ProRes 422 HQ (HD1080p)",
27756 : "J2K HD (HD1080p)",
27757 : "J2K IMF YCrCb (HD1080p)",
27758 : "DNxHD SQ (HD1080p)",
27759 : "DNxUncompressed 4:2:2 8bit (HD7",
27760 : "DNxUncompressed 4:2:2 10bit (HD",
27761 : "XDCAM EX 35 (HD1080p)",
27762 : "XDCAM HD 50 (HD1080p)",
27763 : "DNxUncompressed 4:2:2 8bit (HD1",
27764 : "DNxUncompressed 4:2:2 10bit (HD",
27765 : "XAVC HD Intra CBG Class 50 (HD1",
27766 : "XAVC HD Intra CBG Class 50 (HD1",
27767 : "Apple ProRes 422 Proxy (HD720p)",
27768 : "Apple ProRes 422 LT (HD720p)",
27769 : "DNxHD LB (HD1080p)",
27770 : "DNxHD SQ (HD1080p)",
27771 : "DNxHD HQ (HD1080p)",
27772 : "DNxHD HQX (HD1080p)",
27773 : "Apple ProRes 422 (HD1080p)",
27774 : "Apple ProRes 422 HQ (HD1080p)",
27775 : "DNxUncompressed 4:2:2 16(2.14)b",
27776 : "J2K HD (HD1080p)",
27777 : "DNxUncompressed 4:2:2 8bit (HD1",
27778 : "DNxUncompressed 4:2:2 10bit (HD",
27779 : "DNxUncompressed 4:2:2 12bit (HD",
27780 : "DNxUncompressed 4:2:2 32bit flo",
27781 : "AVC Long GOP 50 (HD1080i)",
27782 : "AVC Long GOP 6 (HD1080p)",
27783 : "DNxUncompressed 4:2:2 16(2.14)b",
27784 : "AVC Long GOP 25 (HD1080p)",
27785 : "AVC Long GOP 50 (HD1080p)",
27786 : "DNxUncompressed 4:2:2 10bit (HD",
27787 : "DNxUncompressed 4:2:2 12bit (HD",
27788 : "DNxUncompressed 4:2:2 32bit flo",
27789 : "DNxUncompressed 4:2:2 10bit (HD",
27790 : "XDCAM EX 35 (HD1080p)",
27791 : "DNxUncompressed 4:2:2 16(2.14)b",
27792 : "J2K HD (HD1080i)",
27793 : "Apple ProRes 422 Proxy (HD1080i",
27794 : "Apple ProRes 422 LT (HD1080i)",
27795 : "Apple ProRes 422 (HD1080i)",
27796 : "Apple ProRes 422 HQ (HD1080i)",
27797 : "AVC Long GOP 35 (HD1080i)",
27798 : "XAVC HD Intra CBG Class 200 (HD",
27799 : "XAVC HD Intra CBG Class 100 (HD",
27800 : "DNxHD TR (HD1080i)",
27801 : "DNxHD TR+ (HD1080i)",
27802 : "Apple ProRes 422 (HD1080p)",
27803 : "AVC Long GOP 35 (HD1080p)",
27804 : "XAVC HD Intra CBG Class 200 (HD",
27805 : "XAVC HD Intra CBG Class 100 (HD",
27806 : "DNxHD TR (HD1080p)",
27807 : "DNxHD TR+ (HD1080p)",
27808 : "Apple ProRes 422 HQ (HD1080p)",
27810 : "DNxHD SQ (HD720p)",
27811 : "DNxHD HQ (HD720p)",
27812 : "DNxHD HQX (HD720p)",
27813 : "XDCAM HD 35 (HD1080p)",
27814 : "XDCAM HD 25 (HD1080p)",
27815 : "XDCAM HD 17.5 (HD1080p)",
27816 : "AVC Long GOP 6 (HD1080p)",
27817 : "DNxUncompressed 4:2:2 8bit (HD7",
27818 : "XAVC HD Intra CBG Class 50 (HD1",
27819 : "DNxUncompressed 4:2:2 12bit (HD",
27820 : "DNxUncompressed 4:2:2 32bit flo",
27821 : "XDCAM HD 35 (HD1080p)",
27822 : "XDCAM HD 25 (HD1080p)",
27823 : "DNxUncompressed 4:2:2 16(2.14)b",
27824 : "J2K HD (HD720p)",
27825 : "Apple ProRes 422 Proxy (HD720p)",
27826 : "Apple ProRes 422 LT (HD720p)",
27827 : "XAVC HD Intra CBG Class 50 (HD1",
27828 : "Apple ProRes 422 HQ (HD720p)",
27829 : "DNxHD HQX (HD1080i)",
27830 : "DNxUncompressed 4:2:2 10bit (HD",
27831 : "DNxUncompressed 4:2:2 12bit (HD",
27832 : "DNxUncompressed 4:2:2 32bit flo",
27833 : "XAVC HD Intra CBG Class 200 (HD",
27834 : "XAVC HD Intra CBG Class 100 (HD",
27835 : "XAVC HD Intra CBG Class 50 (HD1",
27836 : "AVC Long GOP 6 (HD1080i)",
27837 : "AVC Long GOP 12 (HD1080i)",
27838 : "AVC Long GOP 25 (HD1080i)",
27839 : "AVC Long GOP 50 (HD1080i)",
27840 : "Apple ProRes 422 HQ (HD1080i)",
27841 : "AVC Long GOP 35 (HD1080i)",
27842 : "XAVC HD Intra CBG Class 200 (HD",
27843 : "DNxUncompressed 4:2:2 8bit (HD1",
27844 : "DNxUncompressed 4:2:2 10bit (HD",
27845 : "DNxUncompressed 4:2:2 12bit (HD",
27846 : "DNxUncompressed 4:2:2 32bit flo",
27847 : "XDCAM HD 17.5 (HD1080p)",
27848 : "DNxUncompressed 4:2:2 32bit flo",
27849 : "DNxUncompressed 4:2:2 16(2.14)b",
27850 : "J2K HD (HD1080i)",
27851 : "Apple ProRes 422 Proxy (HD1080i",
27852 : "Apple ProRes 422 LT (HD1080i)",
27853 : "Apple ProRes 422 (HD1080i)",
27854 : "Apple ProRes 422 HQ (HD1080i)",
27855 : "AVC Long GOP 35 (HD1080i)",
27856 : "XAVC HD Intra CBG Class 200 (HD",
27857 : "XAVC HD Intra CBG Class 100 (HD",
27858 : "DNxHD TR (HD1080i)",
27859 : "DNxHD TR+ (HD1080i)",
27860 : "XAVC HD Intra CBG Class 50 (HD1",
27861 : "DNxHD TR+ (HD1080i)",
27862 : "DNxUncompressed 4:2:2 12bit (HD",
27863 : "DNxUncompressed 4:2:2 32bit flo",
27864 : "DNxUncompressed 4:2:2 32bit flo",
27866 : "DNxUncompressed 4:2:2 16(2.14)b",
27867 : "J2K HD (HD1080i)",
27868 : "Apple ProRes 422 Proxy (HD1080i",
27869 : "DNxHD TR (HD1080i)",
27870 : "DNxHD TR+ (HD1080i)",
27871 : "Apple ProRes 422 HQ (HD1080i)",
27872 : "AVC Long GOP 35 (HD1080i)",
27873 : "XAVC HD Intra CBG Class 200 (HD",
27874 : "XAVC HD Intra CBG Class 100 (HD",
27875 : "DNxHD TR (HD1080i)",
27876 : "XAVC HD Intra CBG Class 50 (HD1",
27877 : "XDCAM HD 25 (HD1080i)",
27878 : "XAVC HD Intra CBG Class 50 (HD1",
27879 : "XAVC HD Intra CBG Class 100 (HD",
27880 : "DNxHD TR (HD1080p)",
27881 : "DNxHD TR+ (HD1080p)",
27882 : "AVC Long GOP 50 (HD1080i)",
27886 : "DNxUncompressed 4:2:2 8bit (HD1",
27887 : "XDCAM HD 35 (HD1080p)",
27888 : "XDCAM HD 25 (HD1080p)",
27889 : "XDCAM HD 17.5 (HD1080p)",
27890 : "XAVC HD Intra CBG Class 50 (HD1",
27892 : "DNxUncompressed 4:2:2 16(2.14)b",
27893 : "XAVC HD Intra CBG Class 50 (HD1",
27894 : "Apple ProRes 422 Proxy (HD1080i",
27895 : "Apple ProRes 422 LT (HD1080i)",
27896 : "Apple ProRes 422 (HD1080i)",
27897 : "Apple ProRes 422 HQ (HD1080i)",
27898 : "AVC Long GOP 35 (HD1080i)",
27899 : "XAVC HD Intra CBG Class 200 (HD",
27900 : "XAVC HD Intra CBG Class 100 (HD",
27901 : "XAVC HD Intra CBG Class 50 (HD1",
27917 : "XAVC HD Intra CBG Class 50 (HD1",
27926 : "DNxHD LB (HD1080p)",
27927 : "DNxHD SQ (HD1080p)",
27928 : "DNxHD HQ (HD1080p)",
27929 : "DNxHD HQX (HD1080p)",
27934 : "DNxUncompressed 4:2:2 8bit (HD1",
27935 : "DNxUncompressed 4:2:2 10bit (HD",
27936 : "DNxUncompressed 4:2:2 12bit (HD",
27937 : "DNxUncompressed 4:2:2 32bit flo",
27940 : "DNxUncompressed 4:2:2 16(2.14)b",
27941 : "J2K HD (HD1080p)",
27942 : "Apple ProRes 422 Proxy (HD1080p",
27943 : "Apple ProRes 422 LT (HD1080p)",
27944 : "Apple ProRes 422 (HD1080p)",
27945 : "Apple ProRes 422 HQ (HD1080p)",
27946 : "J2K IMF YCrCb (HD1080p)",
30001 : "Data",
}
"""Known values from bin view column `type` property"""