import sys, os, typing
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



if __name__ == "__main__":

	import pathlib,dataclasses

	@dataclasses.dataclass(frozen=True)
	class MobInfo:
		mob_type: avbutils.MobTypes
		mob_usage: avbutils.MobUsage
		is_user_placed : bool
		identified_as: avbutils.BinDisplayItemTypes

	if not len(sys.argv) > 1:
		sys.exit(f"Usage: {pathlib.Path(__file__).name} folder/fulla/bins/")
	
	infos = set()

	print("")
	print(str().join([
		str(x).ljust(40) for x in ("Mob Type", "Mob Usage", "Mob Identification", "User Placed", "First Comp Name", "First Bin Path", )
	]))

	for bin_path in pathlib.Path(sys.argv[1]).rglob("*.avb", case_sensitive=False):
		
		if bin_path.name.startswith("."):
			continue

		with avb.open(bin_path) as bin_handle:

			for item in bin_handle.content.items:

				mob_info = MobInfo(
					mob_type  = avbutils.MobTypes.from_composition(item.mob),
					mob_usage = avbutils.MobUsage.from_composition(item.mob),
					is_user_placed = item.user_placed,
					identified_as = avbutils.BinDisplayItemTypes.from_bin_item(item)
				)

				if mob_info not in infos:
					infos.add(mob_info)
					print(str().join([
						str(x).ljust(40) for x in (mob_info.mob_type, mob_info.mob_usage, mob_info.identified_as, "*" if mob_info.is_user_placed else "", item.mob.name, bin_path)
					]))