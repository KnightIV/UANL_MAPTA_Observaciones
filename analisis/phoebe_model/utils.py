import os
import gzip
import shutil

import phoebe
from phoebe import u

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from matplotlib.animation import FuncAnimation
from IPython import display
import ipywidgets

GAIA_RAW_PLOT_COLORS = {'lc_gaia_g_raw@dataset':'green', 'lc_gaia_rp_raw@dataset':'red', 'lc_gaia_bp_raw@dataset':'blue',
						'lc_gaia_g_raw@model':'darkgreen', 'lc_gaia_rp_raw@model':'darkred', 'lc_gaia_bp_raw@model':'darkblue'}
GAIA_NORM_PLOT_COLORS = {'lc_gaia_g_norm@dataset':'green', 'lc_gaia_rp_norm@dataset':'red', 'lc_gaia_bp_norm@dataset':'blue',
						'lc_gaia_g_norm@model':'darkgreen', 'lc_gaia_rp_norm@model':'darkred', 'lc_gaia_bp_norm@model':'darkblue'}

# include re-named datasets
GAIA_PLOT_COLORS = ({'lcGaiaG@dataset':'green', 'lcGaiaRP@dataset':'red', 'lcGaiaBP@dataset':'blue',
						'lcGaiaG@model':'darkgreen', 'lcGaiaRP@model':'darkred', 'lcGaiaBP@model':'darkblue'}
					| GAIA_NORM_PLOT_COLORS | GAIA_RAW_PLOT_COLORS)

ZTF_PLOT_COLORS = {'lcZtfG@dataset': 'lightgreen', 'lcZtfR@dataset': 'lightpink',
				   'lcZtfG@model': 'seagreen', 'lcZtfR@model': 'maroon'}
ZTF_TRIMMED_PLOT_COLORS = {'lcZtfGTrimmed@dataset': 'lightgreen', 'lcZtfRTrimmed@dataset': 'lightpink',
				   'lcZtfGTrimmed@model': 'seagreen', 'lcZtfRTrimmed@model': 'maroon'}

ITURBIDE_PLOT_COLORS = {'lcIturbide@dataset': 'cornflowerblue', 'lcIturbide@model': 'navy',
						'lcIturbideFull@dataset': 'cornflowerblue', 'lcIturbideFull@model': 'navy',
						'lc_iturbide_norm@dataset': 'cornflowerblue', 'lc_iturbide_norm@model': 'navy'}

def displayAnims(rows: int, cols: int, *anims: FuncAnimation):
	plt.rcParams["animation.html"] = "html5"
	plt.rcParams["figure.figsize"] = (15,8)
	
	grid = ipywidgets.GridspecLayout(n_rows=rows, n_columns=cols)
	for row in range(rows):
		for col in range(cols):
			index = (row*cols) + col
			anim = anims[index]
			grid[row, col] = ipywidgets.HTML(anim.to_html5_video())

	display.display(grid)

def displayAnim(anim: FuncAnimation):
	originalBackend = plt.rcParams['backend']
	plt.rcParams['backend'] = 'Agg'
	display.display(display.HTML(anim.to_html5_video()))
	plt.rcParams['backend'] = originalBackend

def __matchAnyTwig(twig: str, twigs_list: list[str]) -> str:
	for refTwig in twigs_list:
		refComponents = refTwig.split('@')
		twigComponents = twig.split('@')

		if len(set(refComponents) & set(twigComponents)) != 0:
			return refTwig
		
	return None

def printFittedVals(b: phoebe.Bundle, solution: str, adopt_twigs: list[str] = None, units: dict[str, u.Unit] = {}):
	for twig, value, unit in zip(b.get_value('fitted_twigs', solution=solution),
								b.get_value('fitted_values', solution=solution),
								b.get_value('fitted_units', solution=solution)):
		refTwig = __matchAnyTwig(twig, adopt_twigs) if adopt_twigs is not None else None
		unitTwig = __matchAnyTwig(twig, list(units.keys()))
		try:
			originalUnit = u.Unit(unit)
			quantity = value * originalUnit
			print(twig, f"{quantity.to(units.get(unitTwig, originalUnit)).value:.5f}", 
		 					units.get(unitTwig, originalUnit).to_string(), 
		 					"(Not adopting)" if adopt_twigs is not None and refTwig is None else "")
		except:
			print(twig, value, unit)

def printFittedTwigsConstraints(b: phoebe.Bundle, solution: str, units: dict[str, u.Unit] = {}, adopt_twigs: list[str] = None):
	for fitTwig in b.get_value('fitted_twigs', solution=solution):
		refTwig = __matchAnyTwig(fitTwig, adopt_twigs) if adopt_twigs is not None else None
		unitTwig = __matchAnyTwig(fitTwig, list(units.keys()))
		quantity = b.get_quantity(fitTwig)
		try:
			print("C" if b[fitTwig].constrained_by else " ",
					fitTwig,
					f"{quantity.to(units.get(unitTwig, quantity.unit)):.5f}",
					"(Not adopting)" if adopt_twigs is not None and refTwig is None else "")
		except:
			print("C" if b[fitTwig].constrained_by else " ",
				  fitTwig,
				  quantity,
				  "(Not adopting)" if adopt_twigs is not None and refTwig is None else "")

def saveBundle(b: phoebe.Bundle, bundleName: str, subfolder: str = None, overwrite: bool = True, compact: bool = True, compress: bool = True) -> str:
	if not os.path.exists("bundle-saves"):
		os.mkdir("bundle-saves")

	saveFolder = "bundle-saves"
	if subfolder:
		saveFolder = f"bundle-saves/{subfolder}"
		os.makedirs(saveFolder, exist_ok=True)

	if os.path.exists(os.path.join(saveFolder, bundleName)):
		if overwrite:
			print(f"CAUTION: overwriting {os.path.join(saveFolder, bundleName)}")
		else:
			print(f"NOT OVERWRITING: {os.path.join(saveFolder, bundleName)} bundle already exists.")
			return
	
	jsonFile = b.save(f"{saveFolder}/{bundleName}.json", compact=compact)
	if compress:
		with open(jsonFile, 'rb') as f_in:
			with gzip.open(f"{jsonFile}.gz", 'wb') as f_out:
				shutil.copyfileobj(f_in, f_out)
		os.remove(jsonFile)
		return f"{jsonFile}.gz"
	
	return jsonFile

def loadBundle(bundleName: str, subfolder: str = None, parentFolder: str = "") -> phoebe.Bundle:
	saveFolder = "bundle-saves"
	if parentFolder:
		saveFolder = f"{parentFolder}/bundle-saves"
	if subfolder:
		saveFolder = f"{saveFolder}/{subfolder}"

	tempJsonFile = f"{saveFolder}/{bundleName}.json"
	with gzip.open(f"{saveFolder}/{bundleName}.json.gz", 'rb') as f_in:
		with open(tempJsonFile, 'wb') as f_out:
			shutil.copyfileobj(f_in, f_out)
	
	b = phoebe.load(tempJsonFile)
	os.remove(tempJsonFile)
	return b

def avoidAtmosphereErrors(b: phoebe.Bundle):
	b.set_value_all(qualifier='ld_mode', value='manual') # original value = interp
	b.set_value_all(qualifier='ld_mode_bol', value='manual') # original value = lookup
	b.set_value_all(qualifier='atm', value='blackbody') # original value = ck2004

def resetAtmosphere(b: phoebe.Bundle):
	b.set_value_all(qualifier='ld_mode', value='interp') # original value = interp
	b.set_value_all(qualifier='ld_mode_bol', value='lookup') # original value = lookup
	b.set_value_all(qualifier='atm', value='ck2004')  # original value = ck2004

def genAnimatedMesh(b: phoebe.Bundle, logger=None, meshDataset="mesh01", fc='teffs', **plot_kwargs):
	if logger: logger.setLevel('ERROR')
	default_kwargs = {
		"draw_sidebars": True,
		"color": "inferno"
	}

	_, mplfig = b.plot(dataset=meshDataset, kind='mesh', fc=fc, ec='face', animate=True, **(default_kwargs | plot_kwargs))
	if logger: logger.setLevel('WARNING')
	return mplfig

def animateMesh(b: phoebe.Bundle, logger=None, meshDataset="mesh01", fc='teffs', **plot_kwargs):
	displayAnim(genAnimatedMesh(b, logger, meshDataset, fc, **plot_kwargs))

def getEnabledDatasets(b: phoebe.Bundle):
	enabledDatasets = []
	for c in b.computes:
		for d in b.datasets:
			if b.get_value(qualifier='enabled', compute=c, dataset=d) and d not in enabledDatasets:
				enabledDatasets.append(d)
	return enabledDatasets

def abilitateDatasets(b: phoebe.Bundle, enableDatasets: list[str], includeMesh: bool = True):
	"""
	Enables specified datasets and disables all others.
	"""
	enableDatasets = enableDatasets.copy()
	if includeMesh:
		enableDatasets.append('mesh01')
		
	for d in b.datasets:
		if d in enableDatasets:
			b.enable_dataset(d)
		else:
			b.disable_dataset(d)
		# b.set_value_all(qualifier='enabled', dataset=d, value=(d in localDatasets))

def abilitateFeatures(b: phoebe.Bundle, *enableFeatures: list[str]):
	"""
	Enables specified features (eg. spots) and disables all others.
	"""		
	for d in b.features:
		if d in enableFeatures:
			b.enable_feature(d)
		else:
			b.disable_feature(d)

def plotModelResidualsFigsize(b: phoebe.Bundle, figsize: tuple[float, float], datasetGroups: list[list[str] | str], model: str, phase=True, scale_max_flux=True,
							  model_kwargs: dict['str', 'str'] = {}, residuals_kwargs: dict['str', 'str'] = {}, **plot_kwargs) -> None:
	"""
	Plots specified model for the datasets given. Plots dataset(s) with model overlay alongside residuals side-by-side.
	"""
	defaultPlotKwargs = {
		'marker': {'dataset': '.'},
		'color': GAIA_PLOT_COLORS | ZTF_PLOT_COLORS | ZTF_TRIMMED_PLOT_COLORS | ITURBIDE_PLOT_COLORS,
		'legend': True,
		'ls': {'model': 'solid'}
	}
	for key, defaultVal in defaultPlotKwargs.items():
		plot_kwargs[key] = plot_kwargs.get(key, defaultVal)

	if type(datasetGroups[0]) is str:
		scale_max_flux = False

	residuals_kwargs['marker'] = '.'

	for datasets in datasetGroups:
		maxFlux = 0
		if scale_max_flux:
			for d in datasets:
				maxFlux = max([maxFlux, max(b.get_value(qualifier='fluxes', context='dataset', dataset=d))])
			maxFluxScale = 1 + 0.17*(len(datasets))

		fig = plt.figure(figsize=figsize)
		b.plot(x=('phase' if phase else 'times'), model=model, dataset=datasets, axorder=1, fig=fig, s={'dataset':0.008, 'model': 0.01}, ylim=(None, maxFluxScale*maxFlux if scale_max_flux else None), **(plot_kwargs | model_kwargs))
		b.plot(x=('phase' if phase else 'times'), y='residuals', model=model, dataset=datasets, axorder=2, fig=fig, subplot_grid=(1,2), s=0.008, show=True, **(plot_kwargs | residuals_kwargs))

def exportCompute(b: phoebe.Bundle, model: str, datasets: list[str], subfolder: str = None, **compute_kwargs) -> None:
	if not os.path.exists("external-compute"):
		os.mkdir("external-compute")

	computeFolder = "external-compute"
	if subfolder:
		computeFolder = f"external-compute/{subfolder}"
		os.makedirs(computeFolder, exist_ok=True)

	b.export_compute(script_fname=os.path.join(computeFolder, f"{model}.py"), out_fname=f"./results/{model}.model", 
				  model=model, dataset=datasets, **compute_kwargs)
	
def adopt_solution(b: phoebe.Bundle, solution_name:str=None, model_name: str = None,
					reset_params=False, solution_file:str=None, 
					run_compute=True, print_sol=True, compute='phoebe01',
				   	avoid_nans=True, adopt_solution_kwargs: dict[str, str] = {}, **compute_kwargs) -> None:
	if solution_file:
		solution_name = b.import_solution(solution_file, solution=solution_name, overwrite=True).solutions[0]

	if print_sol:
		print("Adopted:")
		printFittedVals(b, solution_name)
		print("\nOriginal values:")
		printFittedTwigsConstraints(b, solution_name)

	try:
		initValues = {}
		if reset_params:
			for twig in b.get_value(qualifier='fitted_twigs', solution=solution_name):
				initValues[twig] = b.get_quantity(twig)

		if 'adopt_twigs' not in adopt_solution_kwargs:
			adopt_twigs = b.get_value('fitted_twigs', solution=solution_name)
			if avoid_nans:
				for t, val in zip(adopt_twigs, b.get_value('fitted_values', solution=solution_name)):
					if not val:
						adopt_twigs.remove(t)
			adopt_solution_kwargs['adopt_twigs'] = adopt_twigs

		b.adopt_solution(solution_name, **adopt_solution_kwargs)

		if run_compute: 
			b.run_compute(model=model_name, compute=compute, **compute_kwargs, overwrite=True)
	except Exception as e:
		raise e
	finally:
		if reset_params:
			for twig, val in initValues.items():
				b.set_value(twig, value=val)


def printChi2(b: phoebe.Bundle, model: str):
	"""
	Prints the chi2 fit of a model for all available datasets: Iturbide, Aviles, Gaia, and ZTF data, both normalized
	and raw datasets. Silently ignores any dataset that isn't present in the specified model.
	"""

	rawGaiaDatasets = [d for d in b.datasets if ('raw' in d and 'gaia' in d) or ('Gaia' in d)]
	ztfDatasets = [d for d in b.datasets if 'Ztf' in d]
	allLcs = [d for d in b.datasets if 'mesh' not in d]
	
	print(f"{model} - {b.calculate_chi2(model=model, dataset=allLcs)}", "=================================================", sep='\n')

	try:
		print('\t', "Gaia (Raw) -", np.sum(b.calculate_chi2(model=model, dataset=rawGaiaDatasets)))
		for gd in rawGaiaDatasets:
			print('\t\t', gd, "-", np.sum(b.calculate_chi2(model=model, dataset=gd)))
		print("------------------------------------------------")
	except: pass

	try:
		print('\t', "Iturbide (Norm) -", np.sum(b.calculate_chi2(model=model, dataset=['lc_iturbide_norm', 'lcIturbide'])))
	except: pass

	print("------------------------------------------------")

	try:
		print('\t', "ZTF -", np.sum(b.calculate_chi2(model=model, dataset=ztfDatasets)))
		for zd in ztfDatasets:
			try:
				print('\t\t', zd, "-", np.sum(b.calculate_chi2(model=model, dataset=zd)))
			except: 
				print("\t\t", zd, "Not found in model")
	except: pass

def printAllModelsChi2(b: phoebe.Bundle):
	for m in b.models:
		printChi2(b, m)

def printModelsChi2(b: phoebe.Bundle, models: list[str]):
	for m in models:
		if m not in b.models:
			print(f"{m} not found")
		else:
			printChi2(b, m)