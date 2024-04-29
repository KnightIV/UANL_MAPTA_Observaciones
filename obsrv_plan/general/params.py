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
# WORKING_DIR = "/run/media/ramon/T7/Tesis/Gaia Analisis";
# WORKING_DIR = "/home/ramon/uanl/Tesis/Backup Data/Gaia Query Results/sdss-half"
WORKING_DIR = "/home/ramon/uanl/Tesis/Backup Data/Gaia Query Results/sdss-3_4"

# DATA_FILE_PATH = join(WORKING_DIR, "gdr3_sdss_exclusion_phot_cv_candidates-result.csv")
# DATA_FILE_PATH = join(WORKING_DIR, "SDSS Half Photometric Filter GDR3 - Limit-result.csv")
DATA_FILE_PATH = join(WORKING_DIR, "SDSS 3_4 Filter GDR3-result.csv")

TIMEZONE = timezone(timedelta(hours=-6))
# OBSV_START_DATETIME = datetime.combine(date(year=2024, month=4, day=26), time(hour=21, minute=0, tzinfo=TIMEZONE))
OBSV_START_DATETIME = datetime.combine(date(year=2024, month=4, day=27), time(hour=2, minute=0, tzinfo=TIMEZONE))
RESULT_DIR = join(WORKING_DIR, OBSV_START_DATETIME.strftime("%Y%m%d"))

SIMBAD_VOT_RESULTS = join(RESULT_DIR, "simbad-raw_vot")
# SIMBAD_VOT_RESULTS = join(RESULT_DIR, "simbad") # uncomment for backwards compat with previous dates

SIMBAD_CATEGORIES = join(RESULT_DIR, "simbad-categories")
MAX_PARALLEL = max(cpu_count() - 2, 2)