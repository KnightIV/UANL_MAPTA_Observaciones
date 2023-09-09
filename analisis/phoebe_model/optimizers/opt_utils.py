import os
from collections import namedtuple

import phoebe
from phoebe import u

import analisis.phoebe_model.utils as gen_utils


AdoptSolutionResult = namedtuple("AdoptSolutionResult", "solutionName computeModelName")
def adopt_solution(b: phoebe.Bundle, label:str=None, 
					reset_params=False, solution_file:str=None, plot=True, 
					run_compute=True, print_sol=True, compute='phoebe01', **compute_kwargs) -> AdoptSolutionResult:
	solutionName: str
	if label is not None:
		solutionName = f"opt_{label}_solution"

	if solution_file:
		solutionName = b.import_solution(solution_file, overwrite=True).solutions[0]
		label = solutionName.replace("_solution", "").replace("opt_", "")

	if print_sol:
		gen_utils.printFittedVals(b, solutionName)
		print("=========================\nAdopted\n=========================")
		gen_utils.printFittedTwigsConstraints(b, solutionName)
	b.adopt_solution(solutionName)

	computeModelName = None
	if run_compute: 
		computeModelName = f"opt_{label}_model"
		b.run_compute(model=computeModelName, compute=compute, **compute_kwargs, overwrite=True)
	if plot:
		b.plot(model=computeModelName, kind='lc', x='phase', show=True, legend=True)
	if reset_params:
		for twig, val, unit in zip(b.get_value(f'{solutionName}@fitted_twigs'),
						   		b.get_value(f'{solutionName}@initial_values'),
						   		b.get_value(f'{solutionName}@fitted_units')):
			b.set_value(twig, val * u.Unit(unit))
	
	return AdoptSolutionResult(solutionName, computeModelName)

def optimize_params(b: phoebe.Bundle, fit_twigs: list[str], label: str, export: bool, 
		    		datasets=['lc_iturbide'], optimizer='optimizer.nelder_mead', compute='phoebe01', 
					**solver_kwargs):
	if not 'maxiter' in solver_kwargs.keys():
		solver_kwargs['maxiter'] = 200 if export else 10

	abilitatedDatasets = [d for d in b.datasets if b.get_value(qualifier='enabled', dataset=d)]
	gen_utils.abilitateDatasets(b, datasets, False)
	
	saveIterProgress = 1 if export else 0
	b.add_solver(optimizer, solver=f'opt_{label}', fit_parameters=fit_twigs, overwrite=True, progress_every_niters=saveIterProgress, compute=compute, **solver_kwargs)
	if export:
		if not os.path.exists('external-jobs'):
			os.mkdir('external-jobs')
				
		fname, out_fname = b.export_solver(script_fname=f'./external-jobs/{optimizer}_opt_{label}.py', out_fname=f'./results/opt_{label}_solution', 
											  solver=f'opt_{label}', solution=f'opt_{label}_solution', overwrite=True)
		print("External Solver:", fname, out_fname)
	else:
		b.run_solver(solver=f'opt_{label}', solution=f'opt_{label}_solution', **solver_kwargs)

	gen_utils.abilitateDatasets(b, abilitatedDatasets)
	
	return f'opt_{label}', f'opt_{label}_solution'