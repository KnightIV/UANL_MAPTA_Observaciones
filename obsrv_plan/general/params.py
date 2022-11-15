"""
General use variables; SIMBAD query URL, result directory, observation datetime
"""

from datetime import datetime, date, time, timedelta, timezone
from os.path import join
from multiprocessing import cpu_count

# Windows
# WORKING_DIR = r"C:\Users\Ramon\Documents\Uni\Tesis\CVs Data"

# Fedora
# WORKING_DIR = "/home/ramon/uanl/Tesis/UANL_MAPTA_PlanObservaciones"
WORKING_DIR = "/run/media/ramon/USBD/Tesis/Gaia Analisis";

DATA_FILE_PATH = join(WORKING_DIR, "gdr3_sdss_exclusion_phot_cv_candidates-result.csv")
TIMEZONE = timezone(timedelta(hours=-5))
OBSV_START_DATETIME = datetime.combine(
		date(year=2022, month=11, day=19), time(hour=23, minute=0, tzinfo=TIMEZONE))
RESULT_DIR = join(WORKING_DIR, OBSV_START_DATETIME.strftime("%Y%m%d"))

SIMBAD_VOT_RESULTS = join(RESULT_DIR, "simbad-raw_vot")
# SIMBAD_VOT_RESULTS = join(RESULT_DIR, "simbad") # uncomment for backwards compat with previous dates

SIMBAD_CATEGORIES = join(RESULT_DIR, "simbad-categories")
MAX_PARALLEL = cpu_count() - 2