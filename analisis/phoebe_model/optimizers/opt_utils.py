import os
from collections import namedtuple

import phoebe
from phoebe import u

try:
	import analisis.phoebe_model.utils as gen_utils
except ImportError:
	import utils as gen_utils

AdoptSolutionResult = namedtuple("AdoptSolutionResult", "solutionName computeModelName")
def adopt_solution(b: phoebe.Bundle, label:str=None, solution_name:str=None,
					reset_params=False, solution_file:str=None, adopt_twigs:list[str]=None, param_units:dict[str:u.Unit]={'incl': u.degree},
					run_compute=True, print_sol=True, compute='phoebe01', compute_model_name:str=None, 
					**compute_kwargs) -> AdoptSolutionResult:
	if label is not None:
		solution_name = f"opt_{label}_solution"

	if solution_file:
		solution_name = b.import_solution(solution_file, overwrite=True).solutions[0]

	if print_sol:
		print("Adopted:")
		gen_utils.printFittedVals(b, solution_name, adopt_twigs=adopt_twigs, units=param_units)
		print("\nOriginal values:")
		gen_utils.printFittedTwigsConstraints(b, solution_name, adopt_twigs=adopt_twigs, units=param_units)

	try:
		initValues = {}
		if reset_params:
			for twig in b.get_value(qualifier='fitted_twigs', solution=solution_name):
				initValues[twig] = b.get_quantity(twig)

		b.adopt_solution(solution_name, adopt_parameters=adopt_twigs)

		if label is None:
			label = solution_name.replace("_solution", "").replace("opt_", "")

		computeModelName = None
		if run_compute: 
			computeModelName = compute_model_name if compute_model_name else f"opt_{label}_model"
			b.run_compute(model=computeModelName, compute=compute, **compute_kwargs, overwrite=True)
	except Exception as e: # reset values if an exception occurs, regardless of reset_params value
		print("Ran into exception", e)
		for twig, val in initValues.items():
			b.set_value(twig, value=val)
	finally:
		if reset_params:
			for twig, val in initValues.items():
				b.set_value(twig, value=val)
	return AdoptSolutionResult(solution_name, computeModelName)

def optimize_params(b: phoebe.Bundle, fit_twigs: list[str], label: str, export: bool, datasets: list[str], subfolder: str=None, 
					optimizer='optimizer.nelder_mead', compute='phoebe01', overwrite_export=True,
					**solver_kwargs):
	if not 'maxiter' in solver_kwargs.keys():
		solver_kwargs['maxiter'] = 200 if export else 10

	abilitatedDatasets = [d for d in b.datasets if b.get_value(qualifier='enabled', dataset=d)]
	gen_utils.abilitateDatasets(b, datasets, False)
	
	saveIterProgress = 1 if export and optimizer == 'optimizer.nelder_mead' else 0
	b.add_solver(optimizer, solver=f'opt_{label}', fit_parameters=fit_twigs, overwrite=True, 
			  				progress_every_niters=saveIterProgress, compute=compute, **solver_kwargs)
	if export:
		if not os.path.exists('external-jobs'):
			os.mkdir('external-jobs')
		if subfolder is not None:
			os.makedirs(os.path.join('external-jobs', subfolder), exist_ok=True)
		
		exportPath = f'./external-jobs{f"/{subfolder}" if subfolder is not None else ""}/{optimizer}_opt_{label}.py'
		if not overwrite_export and os.path.exists(exportPath):
			print("Solver already exists |", exportPath)
		else:
			fname, out_fname = b.export_solver(script_fname=exportPath, out_fname=f'./results/opt_{label}_solution', 
												solver=f'opt_{label}', solution=f'opt_{label}_solution', overwrite=True)
			print("External Solver:", fname, out_fname)
	else:
		b.run_solver(solver=f'opt_{label}', solution=f'opt_{label}_solution', overwrite=True, **solver_kwargs)

	gen_utils.abilitateDatasets(b, abilitatedDatasets)
	
	return f'opt_{label}', f'opt_{label}_solution'