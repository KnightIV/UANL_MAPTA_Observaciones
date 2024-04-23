from obsrv_plan.general.params import SIMBAD_VOT_RESULTS, SIMBAD_CATEGORIES
from obsrv_plan.general.log import printToLog

import os, io, csv

from astropy.io.votable import parse_single_table

def __cleanLine(line):
	return line.replace("b'", "").replace("\\n'", "").replace("\\n", "\n")

def __processDirTables(simbadVotDir: str):
	categoriesSeen = []

	if not os.path.exists(os.path.join(simbadVotDir, ".done")):
		print(f"Cannot process {simbadVotDir} until SIMBAD cross check is finished.")
		return
	for votFile in os.listdir(simbadVotDir):
		try:
			if votFile.endswith(".done"):
				continue
			
			vot: None
			sourceId = votFile.split('_')[0]
			with io.BytesIO() as resultStream:
				with open(os.path.join(simbadVotDir, votFile), "r") as votFileContents:
					line = __cleanLine(votFileContents.readline())
					if line.find("No astronomical object found") != -1:
						print(f"Skipping {os.path.join(simbadVotDir, votFile)}. No results found in SIMBAD.")
						continue
					resultStream.write(bytes(line, "utf-8"))
				vot = parse_single_table(resultStream)
			for starCandidate in vot.array:
				starId = starCandidate[2]
				starType = starCandidate[3]
				starRecord = {
					"ra"	: starCandidate[4],
					"dec"	: starCandidate[5],
					"id"	: starId,
					"gaia_sourceId": sourceId,
					"type": starType,
					"v_mag": starCandidate['FLUX_V'],
					"gaia_g_mag": starCandidate['FLUX_G']
				}
				categoriesSeen.append(starRecord)
		except Exception as e:
			printToLog(f"Error in {os.path.join(simbadVotDir, votFile)}: {str(e)}", print_console=False)
	return categoriesSeen
		
def groupBySimbadCategories():
	if not os.path.exists(SIMBAD_CATEGORIES):
		os.makedirs(SIMBAD_CATEGORIES)

	for d in os.listdir(SIMBAD_VOT_RESULTS):
		resultFileName = os.path.join(SIMBAD_CATEGORIES, f"{d}.csv")
		if os.path.exists(resultFileName):
			print(f"Results already gathered in {resultFileName}")
			continue
		if not os.path.exists(os.path.join(SIMBAD_VOT_RESULTS, d, ".done")):
			print(f"Results not yet finished for {d}")
			continue

		categoriesSeen = __processDirTables(os.path.join(SIMBAD_VOT_RESULTS, d))
		CSV_COLS = ["ra", "dec", "id", "gaia_sourceId", "type", "v_mag", "gaia_g_mag"]
		with open(resultFileName, 'w+') as csvFile:
			writer = csv.DictWriter(csvFile, fieldnames=CSV_COLS)
			writer.writeheader()
			for data in categoriesSeen:
				writer.writerow(data)

if __name__ == "__main__":
	groupBySimbadCategories()