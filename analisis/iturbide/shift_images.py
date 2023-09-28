# Plate solving

import os
import ccdproc
import subprocess
import datetime
import numpy as np

from multiprocessing import Pool, Lock, cpu_count

from ccdproc import wcs_project
from astropy.wcs import WCS
from astropy.io import fits

from astropy import log
log.setLevel('ERROR')

OBSV_DATE = datetime.date(year=2022, month=11, day=5).strftime("%Y-%m-%d")
MAX_PARALLEL = max(cpu_count() - 2, 2)
SOLVE_CMD_TEMPLATE = 'solve-field --fits-image --no-plots --timestamp --new-fits "{solvedOutPath}" --cpulimit 180 -D "{tempFiles}" "{inputPath}" --overwrite'
BASE_DATA_DIR = "/run/media/ramon/ROG_Data/Tesis/IturbideDatos/ATOJ339.9469+45.1464/"
DATA_DIR = os.path.join(BASE_DATA_DIR, "Objeto")
CCD_KWARGS = {'unit': 'adu'}

def getMkdir(dirPath: str) -> str:
	if not os.path.exists(dirPath):
		os.mkdir(dirPath)
	return dirPath

LOGGING_LOCK = Lock()
def printToLog(msg: str):
	with LOGGING_LOCK:
		with open(os.path.join(BASE_DATA_DIR, f"{OBSV_DATE}.log"), "a+") as logFile:
			logFile.write(f"[{datetime.datetime.now()}] {msg}\n")

def plateSolveFile(correctedFile: str, correctedDir: str):
	solvedFitsDir = getMkdir(os.path.join(correctedDir, "solved-fits"))
	plateSolveCmd = SOLVE_CMD_TEMPLATE.format(inputPath=os.path.join(correctedDir, correctedFile), 
											solvedOutPath=os.path.join(solvedFitsDir, correctedFile),
											tempFiles=os.path.join(correctedDir, "solved"))
	print(plateSolveCmd)
	result = subprocess.run(plateSolveCmd, shell=True)
	if result.returncode != 0:
		printToLog(f"Failed to plate solve {correctedFile}")

def plateSolve(correctedFiles: list[str], correctedDir: str):
	# print(f"{os.getpid()} {correctedFiles[0]} {len(correctedFiles)}\n")
	printToLog(f"[{os.getpid()}] Begin plate solving")
	for cFile in correctedFiles:
		plateSolveFile(cFile, correctedDir)
	printToLog(f"[{os.getpid()}] Finished plate solving")

class SolveCaller:
	def __init__(self, correctedDir: str) -> None:
		self.correctedDir = correctedDir

	def __call__(self, imagesChunks):
		plateSolve(imagesChunks, self.correctedDir)

correctedDir = os.path.join(DATA_DIR, "corrected") # output files from previous cell
imagesChunks = np.array_split(os.listdir(correctedDir), MAX_PARALLEL)
with Pool(MAX_PARALLEL) as pool:
	pool.map(SolveCaller(correctedDir), imagesChunks)

# Shift plate solved images. Will also only take the first header from the FITS file to allow them to work in IRAF. 
# This step should NOT be required once every part of the analysis is migrated to use astropy.

targetWcs: WCS = None
correctedDir = os.path.join(DATA_DIR, "corrected")
solvedFitsDir = os.path.join(correctedDir, "solved-fits")
shiftedDir = getMkdir(os.path.join(correctedDir, "iraf-shifted"))

rawImages = ccdproc.ImageFileCollection(solvedFitsDir)
for img, img_fname in rawImages.ccds(ccd_kwargs=CCD_KWARGS, return_fname=True):
	shiftedResultPath = os.path.join(shiftedDir, f"s_{img_fname}")
	if not targetWcs:
		targetWcs = WCS(img.header)
		with fits.open(os.path.join(solvedFitsDir, img_fname)) as fitsImg:
			targetWcs = WCS(fitsImg.pop())
		img.write(shiftedResultPath, overwrite=True)
	else:
		shiftedImg = wcs_project(img, targetWcs)
		primaryImg = shiftedImg.to_hdu()[0] # Takes only the science image from the HDU list, ignoring the mask
		primaryImg.writeto(shiftedResultPath, overwrite=True)

log.setLevel("INFO")