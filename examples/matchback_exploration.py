import sys, os
import avb, avbutils

# Masterclip:		mob_type = MasterMob. (usage/media_kind n/a)
# Subclip:			mob_type = CompositionMob;  usage = subclip
# Timeline:			mob_type = CompositionMob; user_placed=True, usage_code=None, media_kind=None
# Source mobs:		mob_type = SourceMob; have .descriptor pointing to essence
#	MDTP: Tape descriptor
#	MDES: Media descriptor (file import?)
#	MDNG: NagraDescriptor (soundroll?)
#	PCMA: Audio essence
#	CDCI: Codec...? Something?  Corresponds to subclip?

def composition_is_masterclip(comp:avb.trackgroups.Composition) -> bool:
	return comp.mob_type == avbutils.MobTypes.MASTER_MOB

def composition_is_subclip(comp:avb.trackgroups.Composition) -> bool:
	return comp.mob_type_id == avbutils.MobTypes.COMPOSITION_MOB and comp.usage_code == avbutils.MobUsage.SUBCLIP

def composition_is_timeline(comp:avb.trackgroups.Composition) -> bool:
	return comp.mob_type_id == avbutils.MobTypes.COMPOSITION_MOB and comp.usage_code == avbutils.MobUsage.UNDEFINED



def bin_item_info(bin_content:avb.bin.Bin):

	# Item info
	for bin_item in bin_content.items:
		print(str().join(str(s).ljust(40) for s in [
			bin_item.user_placed,
			bin_item.mob.name,
			bin_item.mob.usage,
#				bin_item.mob.media_kind,
			bin_item.mob.mob_type,
			bin_item.mob.descriptor,
#				bin_item.mob
		]))

def source_essence_info(bin_content:avb.bin.Bin):

	for source_mob in [source_item.mob for source_item in bin_content.items if source_item.mob.mob_type_id == avbutils.MobTypes.SOURCE_MOB]:
		print(str(source_mob.name or "[No Name]").ljust(40), source_mob.descriptor.mob_kind)


def main(bin_path:os.PathLike):

	with avb.open(bin_path) as bin_handle:
		print(f"GOT BIN") #Binfo
		
		# File info
		print(f"Path:       {bin_handle.f.name}")
		print(f"Last Saved: {bin_handle.last_save}")
		print(f"Creator:    {bin_handle.creator_version}")
		print("\n")

		source_essence_info(bin_handle.content)


if __name__ == "__main__":

	if not len(sys.argv) > 1:
		import pathlib
		sys.exit(f"Usage: {pathlib.Path(__file__).name} bin_path.avb")
	
	main(sys.argv[1])