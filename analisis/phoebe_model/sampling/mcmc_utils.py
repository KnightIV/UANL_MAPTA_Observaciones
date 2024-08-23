import os
import warnings

import phoebe
import emcee
import numpy as np
import matplotlib.pyplot as plt

import analisis.phoebe_model.utils as gen_utils

def __createExternalJobsFolder(subfolder: str) -> str:
	exportFolder = "external-jobs"
	if subfolder is not None:
		exportFolder = os.path.join(exportFolder, subfolder)
	os.makedirs(exportFolder, exist_ok=True)
	return exportFolder

def exportSampler(b: phoebe.Bundle, sampler_solver: str, datasets: list[str], subfolder: str = None, **solver_kwargs) -> None:
	exportFolder = __createExternalJobsFolder(subfolder)

	prevEnabledDatasets = [d for d in b.datasets if b.get_value(qualifier='enabled', dataset=d)]
	gen_utils.abilitateDatasets(b, datasets, False)
	try:
		b.add_solver('sampler.emcee', solver=sampler_solver, overwrite=True, **solver_kwargs)
		exportFilePath = os.path.join(exportFolder, f"{sampler_solver}.py")
		resultsFilePath = os.path.join("results", sampler_solver)
		fname, out_fname = b.export_solver(script_fname=exportFilePath, out_fname=resultsFilePath, solver=sampler_solver, solution=f"{sampler_solver}_solution", overwrite=True)
		print(sampler_solver, fname, out_fname, sep=" | ")
	finally:
		gen_utils.abilitateDatasets(b, prevEnabledDatasets)

def continueSampler(b: phoebe.Bundle, solver: str, prev_solution: str, continuation_label: str, datasets: list[str], subfolder: str = None, **solver_kwargs) -> None:
	exportFolder = __createExternalJobsFolder(subfolder)

	prevEnabledDatasets = [d for d in b.datasets if b.get_value(qualifier='enabled', dataset=d)]
	gen_utils.abilitateDatasets(b, datasets, False)

	try:
		exportFilePath = os.path.join(exportFolder, f"{continuation_label}.py")
		resultsFilePath = os.path.join("results", f"{continuation_label}_solution")
		fname, out_fname = b.export_solver(script_fname=exportFilePath, out_fname=resultsFilePath, solver=solver, solution=f"{continuation_label}_solution", 
									 continue_from=prev_solution, use_server='none', **solver_kwargs)
		print(solver, fname, out_fname, sep=" | ")
	finally:
		gen_utils.abilitateDatasets(b, prevEnabledDatasets)

# def plotSamplerAcceptanceFractions(b: phoebe.Bundle, sampler_solution: str, min_acceptable=0.4, max_acceptable=0.8, figsize=(22, 7)) -> None:
def plotSamplerAcceptanceFractions(b: phoebe.Bundle, sampler_solution: str, min_acceptable=0.4, max_acceptable=0.8, figsize=(13, 23), vertical=True) -> None:
	nwalkers = b.get_value(qualifier='nwalkers', solution=sampler_solution)

	plt.figure(figsize=figsize)
	walkersIds = list(map(lambda wid: str(wid), range(0, nwalkers)))
	acceptanceFracs = b.get_value(qualifier='acceptance_fractions', solution=sampler_solution)
	passRate = len(acceptanceFracs[(acceptanceFracs >= min_acceptable) & (acceptanceFracs <= max_acceptable)]) / len(acceptanceFracs)
	for w_id, ac_frac in zip(walkersIds, acceptanceFracs):
		if vertical:
			plt.barh(y=w_id, width=ac_frac, color=('b' if min_acceptable <= ac_frac <= max_acceptable else 'r'))
		else:
			plt.bar(x=w_id, height=ac_frac, color=('b' if min_acceptable <= ac_frac <= max_acceptable else 'r'))

	if vertical:
		plt.xlim(0, 1)
		plt.ylim(-1, nwalkers)
		plt.yticks(fontsize=9)
		plt.fill_betweenx(list(range(-1, len(walkersIds) + 1)), min_acceptable, max_acceptable, color='goldenrod', alpha=0.4, label="Desired range")
	else:
		plt.ylim(0, 1)
		plt.xlim(-1, nwalkers + 1)
		plt.xticks(rotation=45, fontsize=9)
		plt.fill_between(list(range(-1, len(walkersIds) + 2)), min_acceptable, max_acceptable, color='goldenrod', alpha=0.4, label="Desired range")

	plt.title(f"$\\mathtt{{{sampler_solution.replace('_', r'\_')}}}$ Acceptance Fractions | ${passRate*100:.2f}\\%$ passing rate", fontsize=20)
	plt.legend(fontsize=14)

	xlabel: str
	ylabel: str
	if vertical:
		xlabel = "Acceptance fraction"
		ylabel = "Walker ID"
	else:
		xlabel = "Walker ID"
		ylabel = "Acceptance fraction"
	plt.xlabel(xlabel, fontsize=16)
	plt.ylabel(ylabel, fontsize=16)
	plt.show()
	
def emceeAutoCorr(b: phoebe.Bundle, solution: str):
	emceeObj = phoebe.helpers.get_emcee_object_from_solution(b, solution=solution)
	try:
		print(f"Burnin = {b.get_value(qualifier='burnin', solution=solution)}", "------------------------", sep='\n')
		emceeObj.get_autocorr_time(discard=b.get_value(qualifier='burnin', solution=solution))
	except emcee.autocorr.AutocorrError as e:
		print(e)

	try:
		print("Burnin = 0", "------------------------", sep='\n')
		emceeObj.get_autocorr_time()
	except emcee.autocorr.AutocorrError as e:
		print(e)
		
# MCMC convergence test: https://johannesbuchner.github.io/autoemcee/mcmc-ensemble-convergence.html
def emceeConvergenceTest(b: phoebe.Bundle, solution: str, plot_twigs=[]):
	adoptParams = b.get_value(qualifier='adopt_parameters', solution=solution)
	emceeObj = phoebe.helpers.get_emcee_object_from_solution(b, solution=solution)
	min_autocorr_times = 10
	burnin = b.get_value(qualifier='burnin', solution=solution)

	chain = emceeObj.get_chain()
	flat_chain = emceeObj.get_chain(flat=True)
	num_steps, num_walkers, ndim = chain.shape
	# 0. analyse each variable
	max_autocorrlength = 1
	for i in range(ndim):
		if len(plot_twigs) > 0 and adoptParams[i] not in plot_twigs:
			continue
		chain_variable = chain[:, :, i]
		# 1. treat each walker as a independent chain
		for w in range(num_walkers):
			try:
				chain_walker = chain_variable[:, w]
				with warnings.catch_warnings():
					warnings.simplefilter("ignore")
					tau = emcee.autocorr.integrated_time(chain_walker, c=5, tol=50, quiet=False)
					tau = max(tau, 1)
				max_autocorrlength = max(max_autocorrlength, tau)
				if len(chain_walker) / tau < min_autocorr_times:
					print("autocorrelation is long for parameter %d: tau=%.1f -> %dx lengths" % (i+1, tau, num_steps / tau))
					converged = False
					# you could plot chain_walker to visualise
					continue
			except emcee.autocorr.AutocorrError as e:
				print(e)
				max_autocorrlength = np.inf
				if min_autocorr_times > 0:
					print("autocorrelation is too long for parameter %d to be estimated" % (i+1))
					converged = False
					
					# you could plot chain_walker to visualise
					plt.plot(chain_walker)
					plt.title(f"{adoptParams[i]} - Walker {w}")
					plt.show()
					# break

	# 	if not converged:
	# 		break

	# 	# secondly, detect drift with geweke
	# 	a = flat_chain[:len(flat_chain) // 4, i]
	# 	b = flat_chain[-len(flat_chain) // 4:, i]
	# 	geweke_z = (a.mean() - b.mean()) / (np.var(a) + np.var(b))**0.5
	# 	if geweke_z > geweke_max:
	# 		print("geweke drift (z=%.1f) detected for parameter %d" % (geweke_z, i+1))
	# 		converged = False
	# 		# you can plot histograms of a and b to visualise`

def printParameterAutocorrTimes(b: phoebe.Bundle, solution: str):
	numIterations = b.get_value(qualifier='niters', solution=solution)
	burninIterations = b.get_value(qualifier='burnin', solution=solution)
	effectiveIterations = numIterations - burninIterations

	autocorrTimes = b.get_value(qualifier='autocorr_times', solution=solution)
	avgAutocorrTime = np.sum(autocorrTimes)/len(autocorrTimes)

	print(f"""Parameter autocorrelation times 
	   Total iterations: {numIterations} ({burninIterations} burnin) 
	   Avg. autocorr time: {avgAutocorrTime} 
	   Avg. IIDs: {effectiveIterations/avgAutocorrTime}""")
	print('---------------------------------------------------------------')
	for twig, autocorr_time in zip(b.get_value(qualifier='fitted_twigs', solution=solution), autocorrTimes):
		# print(twig, autocorr_time, '|', effectiveIterations / autocorr_time)
		print(twig)
		print("\tAutocorrelation time:", autocorr_time)
		print("\tIIDs ([iters - burnin]/autocorr_time):", effectiveIterations/autocorr_time)