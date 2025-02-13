import os
import gzip
import shutil
import datetime
import multiprocessing as mp

import tqdm

import phoebe
phoebe.update_all_passbands()
phoebe.progressbars_off()
logger = phoebe.logger(clevel='WARNING')
logger.disabled = True

import argparse
parser = argparse.ArgumentParser("q-search", 
                                description="Run a q-search for given PHOEBE bundle",
								usage="q-search [options]")
parser.add_argument("--path", required=True, help="Bundle path; supports JSON and gzipped JSON")
parser.add_argument("--q-min", type=float, required=True, help="Min for q-grid")
parser.add_argument("--q-max", type=float, required=True, help="Max for q-grid")
parser.add_argument("--q-step", type=float, required=True, help="Interval step for q-grid")

parser.add_argument("--n-procs", type=int, required=False, default=os.cpu_count()//2,
                                    help="(Optional) Number of parallel processes to use; defaults to (cpus//2)")
parser.add_argument("--nm-maxiter", type=int, required=False, default=250,
                                    help="(Optional) Max number of iterations for NM optimizer for each fixed q-value; defaults to 250")
parser.add_argument("--solution-dir", required=False, default=os.getcwd(),
                                    help="(Optional) P arent directory path to place solution files; defaults to cwd")

BUNDLE: phoebe.Bundle
PARENT_DIRECTORY: str

# region Util functions
LOGGING_LOCK = mp.Lock()

def printsync_log(msg: str, parent_dir: str, print_console=False):
    logPath = os.path.join(parent_dir, "q-solutions", ".log")
    with LOGGING_LOCK:
        with open(logPath, "a+") as logFile:
            logFile.write(f"[{datetime.datetime.now()}] {msg}\n")
        
        if print_console:
            print(f"[{os.getpid()}][{datetime.datetime.now()}] {msg}")
               
def load_bundle(path: str) -> phoebe.Bundle:
    print(f"Reading in bundle from {args.path}")

    b: phoebe.Bundle
    jsonBundlePath = path
    if path.endswith('.gz'):
        jsonBundlePath = path.replace('.gz', '')
        with gzip.open(path, 'rb') as f_in:
            with open(jsonBundlePath, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    b = phoebe.load(jsonBundlePath)
    if jsonBundlePath != path: os.remove(jsonBundlePath) # used temp file
    return b

def optimize_q(q: float) -> str:
    b = BUNDLE.copy()
    solution = "opt_q_search_solution"
    exportSolPath = os.path.join(PARENT_DIRECTORY, "q-solutions", f"{q:.4f}.sol")
    if os.path.exists(exportSolPath):
        printsync_log(f"{q} already solved", print_console=True)
        return

    b.run_solver(solver="opt_q_search", solution=solution, overwrite=True)
    b.set_value(qualifier='comments', solution=solution, value=str(q))
    return b.filter(context='solution', solution=solution, check_visible=False) \
            .save(exportSolPath, incl_uniqueid=True);
# endregion

def q_search(args: argparse.Namespace):
    global BUNDLE
    global PARENT_DIRECTORY
    PARENT_DIRECTORY = args.solution_dir

    BUNDLE = load_bundle(args.path)
    BUNDLE.set_value_all(qualifier='enabled', value=True) # enable all datasets to use
    BUNDLE.add_solver('optimizer.nelder_mead', solver="opt_q_search", maxiter=args.nm_maxiter, 
                                        fit_parameters=['teffratio', 'fillout_factor', 'incl@binary'])

    qGrid = phoebe.arange(args.q_min, args.q_max + args.q_step, args.q_step)
    
    with mp.Pool(args.n_procs) as pool:
        list(tqdm.tqdm(pool.imap(optimize_q, list(qGrid)), total=len(qGrid)))

if __name__ == "__main__":
    args = parser.parse_args()
    if not os.path.exists(args.path):
        raise FileExistsError(f"{args.path} does not exist")
    if not (args.path.endswith('.gz') or args.path.endswith('.json')):
        raise ValueError(f"{args.path} does not point to valid PHOEBE bundle")

    solutionDir = os.path.join(args.solution_dir, "q-solutions")
    if not os.path.exists(solutionDir):
        os.makedirs(solutionDir, exist_ok=True)

    q_search(args)