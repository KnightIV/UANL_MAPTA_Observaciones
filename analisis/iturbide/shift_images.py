import os
import ccdproc
import subprocess
import datetime
import numpy as np

from multiprocessing import Pool, Lock, cpu_count

from ccdproc import wcs_project
from astropy.wcs import WCS
from astropy.io import fits
from astropy.coordinates import SkyCoord
from astropy import units as u

from astropy import log
log.setLevel('ERROR')

MAX_PARALLEL = max(cpu_count() - 2, 2)
SOLVE_CMD_TEMPLATE = ('solve-field --fits-image --no-plots --timestamp --new-fits "{solvedOutPath}" --cpulimit 180 -D '
					  '"{tempFiles}" "{inputPath}" --overwrite')
DATA_DIR = "SCIENCE_IMAGES_DIRECTORY_HERE"
CCD_KWARGS = {'unit': 'adu'}

OBJ_COORD = SkyCoord.from_name("ATO J339.9469+45.1464")

def getMkdir(dirPath: str) -> str:
	if not os.path.exists(dirPath):
		os.mkdir(dirPath)
	return dirPath

LOGGING_LOCK = Lock()
def printToLog(msg: str):
	with LOGGING_LOCK:
		with open(os.path.join(DATA_DIR, f"shifter.log"), "a+") as logFile:
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
	printToLog(f"[{os.getpid()}] Begin plate solving")
	for cFile in correctedFiles:
		plateSolveFile(cFile, correctedDir)
	printToLog(f"[{os.getpid()}] Finished plate solving")

class SolveCaller:
	def __init__(self, correctedDir: str) -> None:
		self.correctedDir = correctedDir

	def __call__(self, imagesChunks):
		plateSolve(imagesChunks, self.correctedDir)

correctedDir = DATA_DIR # cleaned images (bias, dark, flat subtracted) directory
imagesChunks = np.array_split(os.listdir(correctedDir), MAX_PARALLEL)
with Pool(MAX_PARALLEL) as pool:
	pool.map(SolveCaller(correctedDir), imagesChunks)

# Shift plate solved images. Will also only take the first header from the FITS file to allow them to work in IRAF. 
targetWcs: WCS = None
solvedFitsDir = os.path.join(correctedDir, "solved-fits")
fixedSolvedFitsDir = getMkdir(os.path.join(correctedDir, "fixed-solved-fits"))
shiftedDir = getMkdir(os.path.join(correctedDir, "iraf-shifted"))

# fixing 'broken' header entries (from work with Dr. Raul Michel to use with his photometry pipeline)
for f in os.listdir(solvedFitsDir):
	with fits.open(os.path.join(solvedFitsDir, f)) as hdul:
		hdul[0].header['RA'] = OBJ_COORD.ra.value
		hdul[0].header['DEC'] = OBJ_COORD.dec.value
		hdul[0].verify('fix')
		hdul.writeto(os.path.join(fixedSolvedFitsDir, f))

rawImages = ccdproc.ImageFileCollection(fixedSolvedFitsDir)
for img, img_fname in rawImages.ccds(ccd_kwargs=CCD_KWARGS, return_fname=True):
	shiftedResultPath = os.path.join(shiftedDir, f"s_{img_fname}")
	if not targetWcs:
		targetWcs = WCS(img.header)
		with fits.open(os.path.join(solvedFitsDir, img_fname)) as fitsImg:
			targetWcs = WCS(fitsImg.pop())
		img.write(shiftedResultPath, overwrite=True)
	else:
		shiftedImg = wcs_project(img, targetWcs)
		primaryImg = shiftedImg.to_hdu()[0] # Takes only the science image from the HDU list, ignoring the mask, for use in IRAF
		primaryImg.writeto(shiftedResultPath, overwrite=True)