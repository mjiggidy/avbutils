import enum, avb, collections, dataclasses

#ClipColor = collections.namedtuple("ClipColor", "R G B")

# TODO: Replace the namedtuple with this
@dataclasses.dataclass
class ClipColor:

	r:int
	"""16-bit Red Channel"""
	g:int
	"""16-bit Green Channel"""
	b:int
	"""16-bit Blue Channel"""

	def as_rgb16(self) -> tuple[int]:
		"""Original RGB 16-bit"""
		return (self.r, self.g, self.b)
	
	def as_rgba16(self) -> tuple[int]:
		"""Original RGB 16-bit values with 100% alpha"""
		return (*self.as_rgb16(), self.max_16b())
	
	def as_rgb8(self) -> tuple[int]:
		"""Dither to RGB 8-bit"""
		return tuple([round(c/self.max_16b()*self.max_8b()) for c in self.as_rgb16()])

	def as_rgba8(self) -> tuple[int]:
		"""Dither to RGB 8-bit with 100% alpha"""
		return (*self.as_rgb8(), self.max_8b())

	
	@classmethod
	def from_rgb8(cls, r:int, g:int, b:int) -> "ClipColor":
		"""ClipColor from 8-bit RGB values"""
		
		return cls(
			*[round(x * cls.max_16b() / cls.max_8b()) for x in (r,g,b)]
		)
	
	@staticmethod
	def max_8b():
		"""Maximum 8bit value"""
		return (1 << 8) - 1
	
	@staticmethod
	def max_16b():
		"""Maximum 16bit value"""
		return (1 << 16) - 1


class MobTypes(enum.IntEnum):
	"""Mob Types"""

	# NOTE: Data originates from `avb.trackgrouns.Compositon.mob_type` property
	
	COMPOSITION_MOB   = 1
	"""Composition Mob"""
	MASTER_MOB        = 2
	"""Master Clip"""
	SOURCE_MOB        = 3
	"""Tape, Source File, or Film Reel"""

	@classmethod
	def from_composition(cls, comp:avb.trackgroups.Composition):
		return cls(comp.mob_type_id)
	
	def __str__(self) -> str:
		"""Show name with nicer formatting"""
		return self.name.replace("_"," ").title()

class MobUsage(enum.IntEnum):
	"""Mob Usage"""
	
	# NOTE: From pyavb: `these usage codes seem to come from omf`
	# TODO: Marry these to `.bins.BinDisplayOptions`?

	UNDEFINED    = 0 # TODO: Investigate - Top level...?
	PRECOMPUTE   = 1
	SUBCLIP      = 2
	EFFECT       = 3
	GROUP_CLIP   = 4
	GROUP_OOFTER = 5 # wat is oofter plz advise
	MOTION       = 6
	MASTER_MOB   = 7
	PRECOMPUTE_FILE  = 9
	PRECOMPUTE_SOURCE_MOB = 14 # Need clarification

	@classmethod
	def from_composition(cls, comp:avb.trackgroups.Composition):
		return cls(comp.usage_code)

	def __str__(self) -> str:
		"""Show name with nicer formatting"""
		return self.name.replace("_"," ").title()

def composition_is_toplevel(comp:avb.trackgroups.Composition) -> bool:
	"""Determine if a given composition is a top-level timeline"""
	# NOTE: Using rules from `avb.bin.Bin.toplevel()``
	return MobTypes.from_composition(comp) == MobTypes.COMPOSITION_MOB and MobUsage.from_composition(comp) == MobUsage.UNDEFINED


def get_default_clip_colors() -> list[ClipColor]:
	"""Default clip colors for top-level compositions (16-bit RGB triads)"""	
	return [ClipColor(*x) for x in [
		[64000,	48640,	48640],
		[56832,	25600,	29696],
		[65280,	0,		29440],
		[48896,	0,		26112],
		[32256,	12544,	26880],
		[49408,	19200,	41216],
		[61440,	12800,	58880],
		[36608,	0,		45824],
		[58880,	48640,	65280],
		[22528,	17920,	58624],
		[14592,	11776,	38144],
		[15104,	25344,	37888],
		[23040,	38912,	58112],
		[16896,	54272,	62464],
		[17920,	39168,	36864],
		[43520,	65280,	49920],
		[25856,	50432,	21248],
		[16896,	32768,	13824],
		[61952,	65280,	16384],
		[32256,	32768,	14336],
		[49408,	50176,	22016],
		[56064,	55296,	47104],
		[58368,	50688,	0    ],
		[48896,	43264,	36608],
		[65280,	50176,	32768],
		[62720,	33280,	12544],
		[32256,	20992,	13568],
		[49664,	32256,	20992],
		[48896,	48896,	48896],
		[22784,	22784,	22784],
		[32768,	9216,	9216 ],
		[51200,	14592,	14592]
	]]

def composition_clip_color(comp:avb.trackgroups.Composition) -> tuple[int,int,int]|None:
	"""Return the clip color of a composition if set"""

	color_attr_fields = ("_COLOR_R", "_COLOR_G", "_COLOR_B")

	attrs = comp.attributes
	try:
		return ClipColor(*(attrs[c] for c in color_attr_fields))
	except KeyError:
		return None