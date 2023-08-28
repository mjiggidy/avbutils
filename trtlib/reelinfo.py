import dataclasses, datetime
import avb
from timecode import Timecode

@dataclasses.dataclass(frozen=True)
class ReelInfo:
	"""Representation of a Sequence from an Avid bin"""

	sequence_name:str = str()
	"""The name of the sequence"""

	duration_total:Timecode = Timecode(0)
	"""The total duration of the sequence"""

	date_modified:datetime.datetime = datetime.datetime.now()
	"""The date the sequence was last modified in the bin"""

	reel_number:int|None = None
	"""The number of the reel in the feature"""

	duration_head_leader:Timecode|None = None
	"""The duration of the head leader"""

	duration_tail_leader:Timecode|None = None
	"""The duration of the tail leader"""

	@property
	def duration_adjusted(self) -> Timecode:
		"""Duration of active picture, without head or tail leaders"""
		return self.duration_total - self.duration_head_leader - self.duration_tail_leader
	
	@property
	def lfoa(self) -> str:
		"""Last frame of action at 35mm 4-perf"""
		frame_number = (self.duration_total - self.duration_tail_leader).frame_number - 1
		return f"{frame_number//16}+{(frame_number%16):02}"