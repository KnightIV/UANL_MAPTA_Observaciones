import os

import phoebe
from phoebe import u

import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation
from IPython import display
# from ipywidgets import Output, GridspecLayout, HTML
import ipywidgets

def displayAnim(anim: FuncAnimation):
	plt.rcParams["animation.html"] = "html5"
	plt.rcParams["figure.figsize"] = (15,8)

	video = anim.to_html5_video()
	display.display(display.HTML(video))

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

def printFittedVals(b: phoebe.Bundle, solution: str):
	for param, value, unit in zip(b.get_value('fitted_twigs', solution=solution),
								b.get_value('fitted_values', solution=solution),
								b.get_value('fitted_units', solution=solution)): 
		try:
			print(f"{param} = {value:.2f} {unit}")
		except:
			print(param, value, unit)

def printFittedTwigsConstraints(b: phoebe.Bundle, solution: str, units: dict[str, u.Unit]):
	for fitTwig in b.get_value('fitted_twigs', solution=solution):
		quantity = b.get_quantity(fitTwig)
		print("C" if b[fitTwig].constrained_by else " ", fitTwig, quantity.to(units.get(fitTwig, quantity.unit)))

def saveBundle(b: phoebe.Bundle, bundleName: str) -> str:
	if not os.path.exists("bundle-saves"):
		os.mkdir("bundle-saves")
	
	return b.save(f"bundle-saves/{bundleName}")

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