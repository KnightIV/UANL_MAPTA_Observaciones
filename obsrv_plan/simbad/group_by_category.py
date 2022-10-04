from obsrv_plan.general.params import RESULT_DIR, SIMBAD_VOT_RESULTS
from astropy.io.votable import parse_single_table
from os.path import join
import os, json, io, datetime

def __cleanLine(line):
	return line.replace("b'", "").replace("\\n'", "").replace("\\n", "\n")

def __processDirTables(simbadVotDir: str):
	categoriesSeen = {}

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
				sameTypeSeen = categoriesSeen.get(starType, [])
				starRecord = {
					"ra"	: starCandidate[4],
					"dec"	: starCandidate[5],
					"id"	: starId,
					"gaia_sourceId": sourceId
				}
				sameTypeSeen.append(starRecord)
				categoriesSeen[starType] = sameTypeSeen
		except Exception as e:
			with open(".log", "a+") as logFile:
				logFile.write(f"[{datetime.datetime.now()}] Error in {join(simbadVotDir, votFile)}: {str(e)}\n")
	return categoriesSeen
		
def groupBySimbadCategories():
	for d in os.listdir(SIMBAD_VOT_RESULTS):
		jsonResultFileName = join(RESULT_DIR, f"{d}.json")
		if os.path.exists(jsonResultFileName):
			print(f"Results already gathered in {jsonResultFileName}")
			continue
		if not os.path.exists(join(SIMBAD_VOT_RESULTS, d, ".done")):
			print(f"Results not yet finished for {d}")
			continue

		categoriesSeen = __processDirTables(join(SIMBAD_VOT_RESULTS, d))
		with open(jsonResultFileName, "w+") as jsonFile:
			json.dump(categoriesSeen, jsonFile)

if __name__ == "__main__":
	groupBySimbadCategories()