"""
General use variables; SIMBAD query URL, result directory, observation datetime
"""

from datetime import datetime, date, time, timedelta, timezone
from os.path import join

WORKING_DIR = r"C:\Users\Ramon\Documents\Uni\Tesis\CVs Data"
DATA_FILE_PATH = join(WORKING_DIR, "sdssdr9_exclusion-color_filter-variable-gdr2-j2000-result.csv")
TIMEZONE = timezone(timedelta(hours=-5))
OBSV_START_DATETIME = datetime.combine(
		date(year=2022, month=9, day=10), time(hour=23, minute=0, tzinfo=TIMEZONE))
RESULT_DIR = join(WORKING_DIR, OBSV_START_DATETIME.strftime("%Y%m%d"))
SIMBAD_VOT_RESULTS = join(RESULT_DIR, "simbad")