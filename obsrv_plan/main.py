"""
Main script to find observable candidates. Calculations based on observation datetime
defined in general.params module.
"""

from gaia.observable_targets import gaiaObservableTargets
from simbad.retrieve_vots import retrieveSimbadVots
from simbad.group_by_category import groupBySimbadCategories
from simbad.extract_desired_categories import retrieveDesiredCategories, simbadCategoriesHistogram

if __name__ == "__main__":
	gaiaObservableTargets()
	retrieveSimbadVots()
	groupBySimbadCategories()

	retrieveDesiredCategories()
	simbadCategoriesHistogram()