from obsrv_plan.general.params import SIMBAD_VOT_RESULTS, SIMBAD_CATEGORIES
from obsrv_plan.general.log import printToLog

import os, json, io, csv
from os.path import join

from astropy.io.votable import parse_single_table

def __cleanLine(line):
	return line.replace("b'", "").replace("\\n'", "").replace("\\n", "\n")

def __processDirTables(simbadVotDir: str):
	# categoriesSeen = {}
	categoriesSeen = []

	if not os.path.exists(join(simbadVotDir, ".done")):
		print(f"Cannot process {simbadVotDir} until SIMBAD cross check is finished.")
		return
	for votFile in os.listdir(simbadVotDir):
		try:
			if votFile.endswith(".done"):
				continue
			
			vot: None
			sourceId = votFile.split('_')[0]
			with io.BytesIO() as resultStream:
				with open(join(simbadVotDir, votFile), "r") as votFileContents:
					line = __cleanLine(votFileContents.readline())
					if line.find("No astronomical object found") != -1:
						print(f"Skipping {join(simbadVotDir, votFile)}. No results found in SIMBAD.")
						continue
					resultStream.write(bytes(line, "utf-8"))
				vot = parse_single_table(resultStream)
			for starCandidate in vot.array:
				starId = starCandidate[2]
				starType = starCandidate[3]
				# sameTypeSeen = categoriesSeen.get(starType, [])
				starRecord = {
					"ra"	: starCandidate[4],
					"dec"	: starCandidate[5],
					"id"	: starId,
					"gaia_sourceId": sourceId,
					"type": starType
				}
				categoriesSeen.append(starRecord)
				# sameTypeSeen.append(starRecord)
				# categoriesSeen[starType] = sameTypeSeen
		except Exception as e:
			printToLog(f"Error in {join(simbadVotDir, votFile)}: {str(e)}")
	return categoriesSeen
		
def groupBySimbadCategories():
	if not os.path.exists(SIMBAD_CATEGORIES):
		os.makedirs(SIMBAD_CATEGORIES)

	for d in os.listdir(SIMBAD_VOT_RESULTS):
		resultFileName = join(SIMBAD_CATEGORIES, f"{d}.csv")
		if os.path.exists(resultFileName):
			print(f"Results already gathered in {resultFileName}")
			continue
		if not os.path.exists(join(SIMBAD_VOT_RESULTS, d, ".done")):
			print(f"Results not yet finished for {d}")
			continue

		categoriesSeen = __processDirTables(join(SIMBAD_VOT_RESULTS, d))
		CSV_COLS = ["ra", "dec", "id", "gaia_sourceId", "type"]
		with open(resultFileName, 'w+') as csvFile:
			writer = csv.DictWriter(csvFile, fieldnames=CSV_COLS)
			writer.writeheader()
			for data in categoriesSeen:
				writer.writerow(data)

		# with open(resultFileName, "w+") as jsonFile:
		# 	json.dump(categoriesSeen, jsonFile)

if __name__ == "__main__":
	groupBySimbadCategories()