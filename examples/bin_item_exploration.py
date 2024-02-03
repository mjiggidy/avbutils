print("In it")
import sys
import avb, avbutils
from PySide6 import QtSql, QtWidgets

# Database Idea:
# Table: Bin Items
# Table: Mobs

print("Start")
app = QtWidgets.QApplication()
con = QtSql.QSqlDatabase.addDatabase("QSQLITE")
con.setDatabaseName("hey.sql")
print("stop")
con.open()
print(con.isOpen())
sys.exit(con)

def list_bin(bin:avb.bin.Bin):
	"""List the bin contents"""

	errors = 0
	precomp_count = 0

	for idx, item in enumerate([x for x in bin.items]):

		# THOUGHTS: An "item" is its representation in the bin (position, visiblity, user-placed))
		# And its mob is the actual object

		mob = item.mob
		#print(item, mob.name, f"({item.x},{item.y})", f"Thumb Frame: {item.keyframe}   {item.user_placed=}")
		if "Precompute Source Mob" in str(mob):
			precomp_count += 1

		try:
			print("*****" if avbutils.composition_is_toplevel(mob) else "", f"{mob.media_kind_id=} {mob.mc_mode=}  {avbutils.MobTypes.from_composition(mob).name} {avbutils.MobUsage.from_composition(mob).name} {mob.name}")
		except Exception as e:
			print(f"Chokin' because {e}: {mob}")
			errors += 1

	print(f"{errors=} {precomp_count=}")

def main(path_bins):

	for path_bin in path_bins:
		with avb.open(path_bin) as ref_bin:

			list_bin(ref_bin.content)

if __name__ == "__main__":

	if len (sys.argv) < 2:
		sys.exit("Usage: {__file__} bin.avb")
	
	main(sys.argv[1:])