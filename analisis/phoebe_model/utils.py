import os

import phoebe
from phoebe import u

import matplotlib.pyplot as plt
plt.rcParams["animation.html"] = "html5"
plt.rcParams["figure.figsize"] = (15,8)

from matplotlib.animation import FuncAnimation
from IPython import display

def displayAnim(anim: FuncAnimation):
	video = anim.to_html5_video()
	display.display(display.HTML(video))

def printFittedVals(b: phoebe.Bundle, solution: str):
	for param, value, unit in zip(b.get_value('fitted_twigs', solution=solution),
								b.get_value('fitted_values', solution=solution),
								b.get_value('fitted_units', solution=solution)): 
		try:
			print(f"{param} = {value:.2f} {unit}")
		except:
			print(param, value, unit)

def printFittedTwigsConstraints(b: phoebe.Bundle, solution: str):
	for fitTwig in b.get_value('fitted_twigs', solution=solution):
		print(b.filter(fitTwig))

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

def animateMesh(b: phoebe.Bundle, logger=None, meshDataset="mesh01", fc='teffs', **plot_kwargs):
	if logger: logger.setLevel('ERROR')
	_, mplfig = b.plot(dataset=meshDataset, kind='mesh', fc=fc, ec='face', animate=True, draw_sidebars=True, **plot_kwargs)
	if logger: logger.setLevel('WARNING')
	displayAnim(mplfig)

def getEnabledDatasets(b: phoebe.Bundle):
	enabledDatasets = []
	for c in b.computes:
		for d in b.datasets:
			if b.get_value(qualifier='enabled', compute=c, dataset=d) and d not in enabledDatasets:
				enabledDatasets.append(d)
	return enabledDatasets

def plotEnabledData(b: phoebe.Bundle, **plot_kwargs):
	b.plot(kind='lc', dataset=getEnabledDatasets(b), marker='.', show=True, legend=True, **plot_kwargs)
	
def phasePlotEnabledData(b: phoebe.Bundle, **plot_kwargs):
	period = b.get_quantity(qualifier='period', component='binary')
	plotEnabledData(b, x='phase', title=f"$P_{{orb}}$ = {period:.3f} | {period.to(u.hour):.3f}", draw_title=True, **plot_kwargs)