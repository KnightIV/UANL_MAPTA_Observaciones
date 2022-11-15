from obsrv_plan.general.params import RESULT_DIR, SIMBAD_CATEGORIES

from os.path import join, exists
from os import listdir, makedirs
import json
import pandas as pd

def __categoriesResultDir():
	desiredCategoriesDir = join(RESULT_DIR, "desired-categories")
	if not exists(desiredCategoriesDir):
		makedirs(desiredCategoriesDir)
	return desiredCategoriesDir

def __exportCategoryResults(categoriesSeen: dict):
	desiredCategoriesDir = __categoriesResultDir()

	for category in categoriesSeen.keys():
		jsonResultFilePath = join(desiredCategoriesDir, f"{category.replace('*', '_star')}.json")
		with open(jsonResultFilePath, "w+") as jsonFile:
			json.dump(categoriesSeen[category], jsonFile)
			print(f"Wrote {category} results to {jsonResultFilePath}")

def __extractCategories(filePath: str, includeCategories: set[str] | None) -> dict:
	print(f"Extracting {includeCategories} from {filePath}")
	allCategories = {}
	rawData = pd.read_csv(filePath)

	for i in rawData.index:
		simbadType = rawData.loc[i, 'type']

		categoryObjs = allCategories.get(simbadType, [])
		categoryObjs.append({
			'ra': rawData.loc[i, 'ra'],
			'dec': rawData.loc[i, 'dec'],
			'gaia_sourceid': str(rawData.loc[i, 'gaia_sourceId']),
			'id': rawData.loc[i, 'id']
		})
		allCategories[simbadType] = categoryObjs

	if not includeCategories:
		return allCategories

	desiredCategories = {}
	for cat in includeCategories:
		desiredCategories[cat] = allCategories.get(cat, [])
	return desiredCategories

def __isValidFile(f: str):
	return f != "categories.json" and f != "categoriesHistogram.json" and f.endswith('.csv')

def __checkSimbadCategoriesSeen(desiredCategories: set[str] | None):
	categoriesSeen = {}
	for f in listdir(SIMBAD_CATEGORIES):
		if __isValidFile(f):
			fileCategories = __extractCategories(join(SIMBAD_CATEGORIES, f), desiredCategories)
			for cat in fileCategories:
				categoriesSeen[cat] = categoriesSeen.get(cat, []) + fileCategories[cat]
	return categoriesSeen

def simbadCategoriesHistogram():
	histogram = {key:len(cats) for (key, cats) in __checkSimbadCategoriesSeen(None).items()}
	jsonResultFilePath = join(__categoriesResultDir(), "categoriesHistogram.json")
	with open(jsonResultFilePath, "w+") as jsonFile:
		json.dump(histogram, jsonFile)

def retrieveDesiredCategories():
	desiredCategories = [
		"CataclyV*_Candidate",
		"CataclyV*",
		"EclBin",
		"EclBin_Candidate"
	]
	__exportCategoryResults(__checkSimbadCategoriesSeen(desiredCategories))

if __name__ == '__main__':
	retrieveDesiredCategories()
	simbadCategoriesHistogram()