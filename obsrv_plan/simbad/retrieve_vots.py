"""
SIMBAD HTTP query. Stores VOTable retrieved in individual file in the declination folder it corresponds to.
"""

from obsrv_plan.general.params import RESULT_DIR, MAX_PARALLEL, SIMBAD_VOT_RESULTS

from os import listdir, makedirs, getpid
from os.path import join, exists, isdir
from time import sleep
import csv, requests

from multiprocessing import Pool, Lock

VOT_FILES_LOCK = Lock()

def __genSimbadVotFilePath(simbadResultDir, sourceId, ra, dec):
	return join(simbadResultDir, f"{sourceId}_{ra} {dec}.vot")

def __querySimbad(simbadResultDir, sourceId, ra, dec):
	SIMBAD_QUERY_URL_TEMPLATE = "http://simbad.u-strasbg.fr/simbad/sim-coo"
	
	coordParam = f"{ra} {dec}"
	params = {
		'Coord': coordParam,
		'Radius': 2,
		'Radius.unit': "arcmin",
		'output.format': "VOTable"
	}
	result = requests.get(url=SIMBAD_QUERY_URL_TEMPLATE, params=params)
	# print(f"Queried {result.url}")
	with open(__genSimbadVotFilePath(simbadResultDir, sourceId, ra, dec), "w+") as simbadResultFile:
		simbadResultFile.write(str(result.content))
		# print(f"Wrote intermediate SIMBAD table to {simbadResultFile}")

def __processSources(simbadResultDir, starRows):
	pid = getpid()

	RA_PROP = "j2000_ra_prop"
	DEC_PROP = "j2000_dec_prop"
	SOURCE_ID_PROP = "source_id"

	RA_COL_POS 	= -1
	DEC_COL_POS	= -1
	SOURCE_ID_COL_POS = -1
	fileObjCount = 0
	for star in starRows:
		if fileObjCount == 0:
			RA_COL_POS = star.index(RA_PROP)
			DEC_COL_POS = star.index(DEC_PROP)
			SOURCE_ID_COL_POS = star.index(SOURCE_ID_PROP)
		else:
			if fileObjCount % 100 == 0:
				print(f"[{pid}] processed {fileObjCount} objects")

			ra = star[RA_COL_POS]
			dec = star[DEC_COL_POS]
			sourceId = star[SOURCE_ID_COL_POS]

			if not exists(__genSimbadVotFilePath(simbadResultDir, sourceId, ra, dec)):
				triesRemaining = 3
				while True:
					triesRemaining -= 1
					try:
						__querySimbad(simbadResultDir, sourceId, ra, dec)
						break
					except: 
						print(f"[{pid}] Error querying for ({ra}, {dec}). Retrying {triesRemaining} more times.")
						if triesRemaining == 0:
							print(f"[{pid}] Out of tries for ({ra}, {dec}). Skipping.")
							break
						sleep(2)
			else:
				print(f"[{pid}] Skipping SIMBAD query for ({ra} {dec}) coordinate.")
		fileObjCount += 1
	return fileObjCount

def __retrieveSimbadVot(f: str):
	if f.endswith(".json") or f == ".log" or isdir(join(RESULT_DIR, f)):
		return
	
	pid = getpid()
	processObjCount = 0

	print(f"[{pid}] Cross-checking '{f}' objects in SIMBAD.")
	fileNameComponents = f.split("_")
	curProcessing = f"{fileNameComponents[1]}_{fileNameComponents[2].replace('.csv', '')}"
	simbadResultDir = join(SIMBAD_VOT_RESULTS, curProcessing)

	with VOT_FILES_LOCK:
		if not exists(simbadResultDir):
			makedirs(simbadResultDir)
		elif exists(join(simbadResultDir, ".done")):
			print(f"[{pid}] Skipping querying for {curProcessing}")
			return 0

	with open(join(RESULT_DIR, f), "r") as csvFile:
		starRows = csv.reader(csvFile)
		processObjCount += __processSources(simbadResultDir, starRows)
	with open(join(simbadResultDir, ".done"), "a") : pass # Only used to create file to signal process finished

	return processObjCount

def retrieveSimbadVots():
	totalObjCount = 0
	with Pool(MAX_PARALLEL) as p:
		totalObjCount = sum(filter(lambda item: item is not None,  p.map(__retrieveSimbadVot, listdir(RESULT_DIR))))

	print(f"Cross-matched {totalObjCount} objects with SIMBAD.")

if __name__ == "__main__":
	retrieveSimbadVots()