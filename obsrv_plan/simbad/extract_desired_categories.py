from obsrv_plan.general.params import RESULT_DIR

from os.path import join, exists
from os import listdir, makedirs
import json

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
	allCategories: dict
	with open(filePath, "r") as jsonFile:
		allCategories = json.load(jsonFile)
	if not includeCategories:
		return allCategories

	desiredCategories = {}
	for cat in includeCategories:
		desiredCategories[cat] = allCategories.get(cat, [])
	return desiredCategories

def __isValidFile(f: str):
	return f != "categories.json" and f != "categoriesHistogram.json" and f.endswith('.json')

def __checkSimbadCategoriesSeen(desiredCategories: set[str] | None):
	categoriesSeen = {}
	for f in listdir(RESULT_DIR):
		if __isValidFile(f):
			fileCategories = __extractCategories(join(RESULT_DIR, f), desiredCategories)
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
		"CataclyV*_Candidate"
	]
	__exportCategoryResults(__checkSimbadCategoriesSeen(desiredCategories))

if __name__ == '__main__':
	retrieveDesiredCategories()
	simbadCategoriesHistogram()