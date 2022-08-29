"""
SIMBAD HTTP query. Stores VOTable retrieved in individual file in the declination folder it corresponds to.
"""

from obsrv_plan.general.params import RESULT_DIR

from os import listdir, makedirs
from os.path import join, exists
from time import sleep
import csv, requests

def __genSimbadVotFilePath(simbadResultDir, ra, dec):
	return join(simbadResultDir, f"{ra} {dec}.vot")

def __querySimbad(simbadResultDir, ra, dec):
	SIMBAD_QUERY_URL_TEMPLATE = "http://simbad.u-strasbg.fr/simbad/sim-coo"
	
	coordParam = f"{ra} {dec}"
	params = {
		'Coord': coordParam,
		'Radius': 2,
		'Radius.unit': "arcmin",
		'output.format': "VOTable"
	}
	result = requests.get(url=SIMBAD_QUERY_URL_TEMPLATE, params=params)
	print(f"Queried {result.url}")
	with open(__genSimbadVotFilePath(simbadResultDir, ra, dec), "w+") as simbadResultFile:
		simbadResultFile.write(str(result.content))
		print(f"Wrote intermediate SIMBAD table to {simbadResultFile}")

def __processSources(simbadResultDir, starRows):
	RA_PROP = "j2000_ra_prop"
	DEC_PROP = "j2000_dec_prop"

	RA_COL_POS 	= -1
	DEC_COL_POS	= -1
	fileObjCount = 0
	for star in starRows:
		if fileObjCount == 0:
			RA_COL_POS = star.index(RA_PROP)
			DEC_COL_POS = star.index(DEC_PROP)
		else:
			ra = star[RA_COL_POS]
			dec = star[DEC_COL_POS]

			if not exists(__genSimbadVotFilePath(simbadResultDir, ra, dec)):
				__querySimbad(simbadResultDir, ra, dec)
			else:
				print(f"Skipping SIMBAD query for ({ra} {dec}) coordinate.")
		fileObjCount += 1
	return fileObjCount

def retrieveSimbadVots():
	totalObjCount = 0
	for f in listdir(RESULT_DIR):
		if f.endswith(".json") or f == "simbad":
			continue
		print(f"Cross-checking '{f}' objects in SIMBAD.")
		fileNameComponents = f.split("_")
		curProcessing = f"{fileNameComponents[1]}_{fileNameComponents[2].replace('.csv', '')}"
		simbadResultDir = join(RESULT_DIR, f"simbad/{curProcessing}")

		if not exists(simbadResultDir):
			makedirs(simbadResultDir)
		elif exists(join(simbadResultDir, ".done")):
			print(f"Skipping querying for {curProcessing}")
		with open(join(RESULT_DIR, f), "r") as csvFile:
			starRows = csv.reader(csvFile)
			totalObjCount += __processSources(simbadResultDir, starRows)
		with open(join(simbadResultDir, ".done"), "a") : pass
		sleep(2)

	print(f"Cross-matched {totalObjCount} objects with SIMBAD.")

if __name__ == "__main__":
	retrieveSimbadVots()