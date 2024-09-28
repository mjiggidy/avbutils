print("In it")
import sys
import avb, avbutils
from PySide6 import QtSql, QtWidgets

# Database Idea:
# Table: Bin Items
# Table: Mobs

app = QtWidgets.QApplication()
con = QtSql.QSqlDatabase.addDatabase("QSQLITE")
con.setDatabaseName("hey.sql")
if not con.open():
	sys.exit("Yeah I dunno bout open")

sql_query = QtSql.QSqlQuery()

sql_query.exec(
	"""
	CREATE TABLE mobs (
		mob_id TEXT PRIMARY KEY UNIQUE NOT NULL,
		name VARCHAR(128),
		mob_usage_id INT,
		mob_type_id INT
	)
	"""
)

sql_query.exec(
	"""
	CREATE TABLE bin_items(
		mob_id TEXT PRIMARY KEY UNIQUE NOT NULL,
		pos_x INT,
		pos_y INT,
		keyframe INT,
		user_placed BOOL,
		FOREIGN KEY (mob_id) REFERENCES mobs(mob_id)
	)
	"""
)

#sql_query.finish()

def catalog_mobs(bin:avb.bin.Bin):
	"""Catalog dem mobs"""

	sql_query = QtSql.QSqlQuery()
	sql_query.prepare(
		"""
		INSERT INTO mobs (mob_id, name, mob_usage_id, mob_type_id) VALUES(?,?,?,?)
		"""
	)

	for mob in bin.mobs:
		
		sql_query.addBindValue(str(mob.mob_id))
		sql_query.addBindValue(mob.name)
		sql_query.addBindValue(mob.usage_code)
		sql_query.addBindValue(mob.mob_type_id)
		
		if not sql_query.exec():
			print("Not mobbin:", sql_query.lastError().databaseText(), "Mob Id:", mob.mob_id)

def catalog_items(bin:avb.bin.Bin):
	"""Catalog bin items"""

	sql_query = QtSql.QSqlQuery()
	sql_query.prepare(
		"""
		INSERT INTO bin_items(mob_id, pos_x, pos_y, keyframe, user_placed) VALUES (?, ?, ?, ?, ?)
		"""
	)

	for item in bin.items:

		print(item.x, item.y)

		sql_query.addBindValue(str(item.mob.mob_id))
		sql_query.addBindValue(int(item.x))
		sql_query.addBindValue(int(item.y))
		sql_query.addBindValue(int(item.keyframe))
		sql_query.addBindValue(int(item.user_placed))

		if not sql_query.exec():
			print("Not iteming:", sql_query.lastError().databaseText(), "Mob Id:", item.mob.mob_id)

def print_mobs_from_db():

	sql_query = QtSql.QSqlQuery()
	sql_query.prepare(
		"""
		SELECT * FROM mobs
		"""
	)


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

			#list_bin(ref_bin.content)
			catalog_mobs(ref_bin.content)
			catalog_items(ref_bin.content)

	#print_mobs_from_db()

if __name__ == "__main__":

	if len (sys.argv) < 2:
		sys.exit("Usage: {__file__} bin.avb")
	
	main(sys.argv[1:])