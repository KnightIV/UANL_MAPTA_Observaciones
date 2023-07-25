import os
import phoebe

import analisis.phoebe_model.utils as gen_utils

def adopt_solution(b: phoebe.Bundle, label: str, solution_file:str=None, plot=True, run_compute=True, print_sol=True, **compute_kwargs):
    if solution_file:
        b.import_solution(solution_file, overwrite=True)

    if print_sol:
        gen_utils.printFittedVals(b, f"opt_{label}_solution")
        print('\n')
        gen_utils.printFittedTwigsConstraints(b, f"opt_{label}_solution")

    b.adopt_solution(f"opt_{label}_solution")
    if run_compute: 
        b.run_compute(model=f"opt_{label}_model", **compute_kwargs, overwrite=True)
    if plot:
        b.plot(model=f'opt_{label}_model', kind='lc', x='phase', show=True, legend=True)

def optimize_params(b: phoebe.Bundle, fit_twigs: list[str], label: str, export: bool, optimizer='optimizer.nelder_mead', **solver_kwargs):
    if not 'maxiter' in solver_kwargs.keys():
        solver_kwargs['maxiter'] = 200 if export else 10
    b.add_solver(optimizer, solver=f'opt_{label}', fit_parameters=fit_twigs, overwrite=True, **solver_kwargs)
    if export:
        fname, out_fname = b.export_solver(script_fname=f'./external-jobs/{optimizer}_opt_{label}.py', out_fname=f'./results/opt_{label}_solution', 
                                              solver=f'opt_{label}', solution=f'opt_{label}_solution')
        print("External Solver:", fname, out_fname)
    else:
        b.run_solver(solver=f'opt_{label}', solution=f'opt_{label}_solution', **solver_kwargs)
    
    return f'opt_{label}', f'opt_{label}_solution'

if not os.path.exists('external-jobs'):
	os.mkdir('external-jobs')
        
if not os.path.exists('bundle-saves'):
	os.mkdir('bundle-saves')