import os

import phoebe
from phoebe import u

import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation
from IPython import display
import ipywidgets

GAIA_RAW_PLOT_COLORS = {'lc_gaia_g_raw@dataset':'green', 'lc_gaia_rp_raw@dataset':'red', 'lc_gaia_bp_raw@dataset':'blue',
						'lc_gaia_g_raw@model':'darkgreen', 'lc_gaia_rp_raw@model':'darkred', 'lc_gaia_bp_raw@model':'darkblue'}
GAIA_NORM_PLOT_COLORS = {'lc_gaia_g@dataset':'green', 'lc_gaia_rp@dataset':'red', 'lc_gaia_bp@dataset':'blue',
						'lc_gaia_g@model':'darkgreen', 'lc_gaia_rp@model':'darkred', 'lc_gaia_bp@model':'darkblue'}

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
	
	return b.save(f"{saveFolder}/{bundleName}")

def avoidAtmosphereErrors(b: phoebe.Bundle):
	b.set_value_all(qualifier='ld_mode', value='manual') # original value = interp
	b.set_value_all(qualifier='ld_mode_bol', value='manual') # original value = lookup

def resetAtmosphere(b: phoebe.Bundle):
	b.set_value_all(qualifier='ld_mode', dataset='lc_iturbide', value='interp') # original value = interp
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
	localDatasets = enableDatasets.copy()
	if includeMesh:
		localDatasets.append('mesh01')
		
	for d in b.datasets:
		b.set_value_all(qualifier='enabled', dataset=d, value=(d in localDatasets))

def plotEnabledData(b: phoebe.Bundle, **plot_kwargs):
	b.plot(kind='lc', dataset=getEnabledDatasets(b), marker='.', show=True, legend=True, **plot_kwargs)
	
def phasePlotEnabledData(b: phoebe.Bundle, **plot_kwargs):
	period = b.get_quantity(qualifier='period', component='binary')
	plotEnabledData(b, x='phase', title=f"$P_{{orb}}$ = {period:.3f} | {period.to(u.hour):.3f}", draw_title=True, **plot_kwargs)

def plotFigSize(b: phoebe.Bundle, figsize: tuple[float, float], **plot_kwargs):
	fig = plt.figure(figsize=figsize)
	b.plot(fig=fig, **plot_kwargs)

def plotModelResidualsFigsize(b: phoebe.Bundle, figsize: tuple[float, float], datasetGroups: list[list[str]], model: str, **plot_kwargs):
	"""
	Plots specified model for the datasets given. Plots dataset(s) with model overlay alongside residuals side-by-side.
	"""
	residuals_kwargs = plot_kwargs.copy()
	residuals_kwargs['marker'] = '.'

	for datasets in datasetGroups:
		fig = plt.figure(figsize=figsize)
		b.plot(x='phase', model=model, dataset=datasets, axorder=1, fig=fig, s={'dataset':0.008}, **plot_kwargs)
		b.plot(x='phase', y='residuals', model=model, dataset=datasets, axorder=2, fig=fig, subplot_grid=(1,2), s=0.008, show=True, **residuals_kwargs)

	# fig = plt.figure(figsize=figsize)
	# b.plot(x='phase', model=model, dataset='lc_iturbide_raw', axorder=1, fig=fig, **plot_kwargs)
	# b.plot(x='phase', y='residuals', model=model, dataset='lc_iturbide_raw', axorder=1, fig=fig, **plot_kwargs)