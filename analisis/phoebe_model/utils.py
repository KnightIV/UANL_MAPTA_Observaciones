import os
from collections import namedtuple

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
# GAIA_NORM_PLOT_COLORS = {'lc_gaia_g@dataset':'green', 'lc_gaia_rp@dataset':'red', 'lc_gaia_bp@dataset':'blue',
# 						'lc_gaia_g@model':'darkgreen', 'lc_gaia_rp@model':'darkred', 'lc_gaia_bp@model':'darkblue'}
GAIA_NORM_PLOT_COLORS = {'lc_gaia_g_norm@dataset':'green', 'lc_gaia_rp_norm@dataset':'red', 'lc_gaia_bp_norm@dataset':'blue',
						'lc_gaia_g_norm@model':'darkgreen', 'lc_gaia_rp_norm@model':'darkred', 'lc_gaia_bp_norm@model':'darkblue'}

# for re-named datasets in sampler
GAIA_PLOT_COLORS = {'lcGaiaG@dataset':'green', 'lcGaiaRP@dataset':'red', 'lcGaiaBP@dataset':'blue',
						'lcGaiaG@model':'darkgreen', 'lcGaiaRP@model':'darkred', 'lcGaiaBP@model':'darkblue'}

ZTF_PLOT_COLORS = {'lcZtfG@dataset': 'yellowgreen', 'lcZtfR@dataset': 'indianred',
				   'lcZtfG@model': 'seagreen', 'lcZtfR@model': 'maroon'}

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
	displayAnims(1, 1, anim)

def printFittedVals(b: phoebe.Bundle, solution: str):
	for param, value, unit in zip(b.get_value('fitted_twigs', solution=solution),
								b.get_value('fitted_values', solution=solution),
								b.get_value('fitted_units', solution=solution)): 
		try:
			print(f"{param} = {value:.5f} {unit}")
		except:
			print(param, value, unit)

def printFittedTwigsConstraints(b: phoebe.Bundle, solution: str, units: dict[str, u.Unit] = {}):
	for fitTwig in b.get_value('fitted_twigs', solution=solution):
		quantity = b.get_quantity(fitTwig)
		print("C" if b[fitTwig].constrained_by else " ", fitTwig, quantity.to(units.get(fitTwig, quantity.unit)))

def saveBundle(b: phoebe.Bundle, bundleName: str, subfolder: str = None) -> str:
	if not os.path.exists("bundle-saves"):
		os.mkdir("bundle-saves")

	saveFolder = "bundle-saves"
	if subfolder:
		saveFolder = f"bundle-saves/{subfolder}"
		os.makedirs(saveFolder, exist_ok=True)

	if os.path.exists(os.path.join(saveFolder, bundleName)):
		print(f"CAUTION: overwriting {os.path.join(saveFolder, bundleName)}")
	
	return b.save(f"{saveFolder}/{bundleName}")

def avoidAtmosphereErrors(b: phoebe.Bundle):
	b.set_value_all(qualifier='ld_mode', value='manual') # original value = interp
	b.set_value_all(qualifier='ld_mode_bol', value='manual') # original value = lookup

def resetAtmosphere(b: phoebe.Bundle):
	b.set_value_all(qualifier='ld_mode', value='interp') # original value = interp
	b.set_value_all(qualifier='ld_mode_bol', value='lookup') # original value = lookup

def genAnimatedMesh(b: phoebe.Bundle, logger=None, meshDataset="mesh01", fc='teffs', **plot_kwargs):
	if logger: logger.setLevel('ERROR')
	_, mplfig = b.plot(dataset=meshDataset, kind='mesh', fc=fc, ec='face', animate=True, draw_sidebars=True, **plot_kwargs)
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

def plotEnabledData(b: phoebe.Bundle, **plot_kwargs):
	b.plot(kind='lc', dataset=getEnabledDatasets(b), marker='.', show=True, legend=True, **plot_kwargs)
	
def phasePlotEnabledData(b: phoebe.Bundle, **plot_kwargs):
	period = b.get_quantity(qualifier='period', component='binary')
	plotEnabledData(b, x='phase', title=f"$P_{{orb}}$ = {period:.3f} | {period.to(u.hour):.3f}", draw_title=True, **plot_kwargs)

def plotFigSize(b: phoebe.Bundle, figsize: tuple[float, float], **plot_kwargs):
	fig = plt.figure(figsize=figsize)
	b.plot(fig=fig, **plot_kwargs)

# TODO: make this return the figures drawn to allow for subsequent operations
def plotModelResidualsFigsize(b: phoebe.Bundle, figsize: tuple[float, float], datasetGroups: list[list[str] | str], model: str, **plot_kwargs) -> dict[str, Figure]:
	"""
	Plots specified model for the datasets given. Plots dataset(s) with model overlay alongside residuals side-by-side.
	"""
	defaultPlotKwargs = {
		'marker': {'dataset': '.'},
		'color': GAIA_PLOT_COLORS | GAIA_RAW_PLOT_COLORS | GAIA_NORM_PLOT_COLORS | ZTF_PLOT_COLORS,
		'legend': True
	}
	for key, defaultVal in defaultPlotKwargs.items():
		plot_kwargs[key] = plot_kwargs.get(key, defaultVal)

	residuals_kwargs = plot_kwargs.copy()
	residuals_kwargs['marker'] = '.'

	datasetGroupsFigures = {}
	for datasets in datasetGroups:
		fig = plt.figure(figsize=figsize)
		b.plot(x='phase', model=model, dataset=datasets, axorder=1, fig=fig, s={'dataset':0.008}, **plot_kwargs)
		b.plot(x='phase', y='residuals', model=model, dataset=datasets, axorder=2, fig=fig, subplot_grid=(1,2), s=0.008, show=True, **residuals_kwargs)
		datasetGroupsFigures["-".join(datasets)] = fig
	return datasetGroupsFigures

def exportCompute(b: phoebe.Bundle, model: str, datasets: list[str], subfolder: str = None, **compute_kwargs) -> None:
	if not os.path.exists("external-compute"):
		os.mkdir("external-compute")

	computeFolder = "external-compute"
	if subfolder:
		computeFolder = f"external-compute/{subfolder}"
		os.makedirs(computeFolder, exist_ok=True)

	b.export_compute(script_fname=os.path.join(computeFolder, f"{model}.py"), out_fname=os.path.join(computeFolder, "results", f"{model}.model"), 
				  model=model, dataset=datasets, **compute_kwargs)
	
def adopt_solution(b: phoebe.Bundle, solution_name:str=None, model_name: str = None,
					reset_params=False, solution_file:str=None, 
					run_compute=True, print_sol=True, compute='phoebe01', **compute_kwargs):
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

		b.adopt_solution(solution_name)

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

	rawGaiaDatasets = [d for d in b.datasets if 'raw' in d and 'gaia' in d]
	normGaiaDatasets = [d for d in b.datasets if 'norm' in d and 'gaia' in d]
	ztfDatasets = [d for d in b.datasets if 'Ztf' in d]
	
	print(model, "=================================================", sep='\n')
	try:
		print('\t', "Iturbide (Aviles) (Raw) -", np.sum(b.calculate_chi2(model=model, dataset='lc_iturbide_aviles_raw')))
	except: pass

	try:
		print('\t', "Iturbide (Full) (Raw) -", np.sum(b.calculate_chi2(model=model, dataset='lc_iturbide_raw')))
	except: pass

	try:
		print('\t', "Gaia (Raw) -", np.sum(b.calculate_chi2(model=model, dataset=rawGaiaDatasets)))
		for gd in rawGaiaDatasets:
			print('\t\t', gd, "-", np.sum(b.calculate_chi2(model=model, dataset=gd)))
	except: pass
	
	print("------------------------------------------------")

	try:
		print('\t', "Iturbide (Aviles) (Norm) -", np.sum(b.calculate_chi2(model=model, dataset='lc_iturbide_aviles_norm')))
	except: pass

	try:
		print('\t', "Iturbide (Full) (Norm) -", np.sum(b.calculate_chi2(model=model, dataset='lc_iturbide_norm')))
	except: pass

	try:
		print('\t', "Gaia (Norm) -", np.sum(b.calculate_chi2(model=model, dataset=normGaiaDatasets)))
		for gd in normGaiaDatasets:
			print('\t\t', gd, "-", np.sum(b.calculate_chi2(model=model, dataset=gd)))
	except: pass

	try:
		print('\t', "ZTF -", np.sum(b.calculate_chi2(model=model, dataset=ztfDatasets)))
		for zd in ztfDatasets:
			print('\t\t', zd, "-", np.sum(b.calculate_chi2(model=model, dataset=zd)))
	except: pass

def printAllModelsChi2(b: phoebe.Bundle):
	for m in b.models:
		printChi2(b, m)