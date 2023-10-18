"""
Read in Gaia candidates from CSV file and determine which objects from Gaia are observable on the night in question.
"""

from obsrv_plan.general.params import TIMEZONE, OBSV_START_DATETIME, DATA_FILE_PATH, RESULT_DIR, MAX_PARALLEL
from obsrv_plan.decorators.static_decorator import static_vars
from obsrv_plan.general.log import printToLog

import os
import numpy as np
import pandas as pd
import astropy.units as u
from math import ceil, floor
from datetime import timedelta
from multiprocessing import Pool

from astroplan import Observer
from astropy.coordinates import SkyCoord
from astropy.time import Time, TimeDelta

@static_vars(obsv=Observer(longitude=-99.895328*u.deg, latitude=24.75521 * u.deg, 
						elevation=2400*u.m, name="Iturbide", timezone=TIMEZONE))
def __is_observable(ra, dec, g_mag):
	ITURBIDE_OBSV = __is_observable.obsv
	FMT_STR = "%Y-%m-%dT%H:%M:%S"
	acceptable_time_range = [(OBSV_START_DATETIME + timedelta(hours=3)).strftime(FMT_STR),
							 (OBSV_START_DATETIME - timedelta(hours=3)).strftime(FMT_STR)]
	ideal_mer_time = Time(val=acceptable_time_range,
						  format="isot",
						  location=ITURBIDE_OBSV.location)

	target = SkyCoord(ra, dec, unit="deg", frame="icrs")
	mer_time = ITURBIDE_OBSV.target_meridian_transit_time(
		time=Time(val=OBSV_START_DATETIME),
		target=target)

	MER_TOLERANCE = TimeDelta(val=timedelta(hours=3))
	return (mer_time, 
			ITURBIDE_OBSV.is_night(time=mer_time, horizon=-6 * u.deg) and
				ITURBIDE_OBSV.target_is_up(target=target, time=mer_time, horizon=-6 * u.deg) and
				np.any(ideal_mer_time.isclose(other=mer_time, atol=MER_TOLERANCE)) and
				g_mag <= 16)

def __processSubset(df):
	pid = os.getpid()
	rowsToProcess = len(df)
	printToLog(f"{pid}: Begin processing {rowsToProcess} rows")

	for i in df.index:
		if rowsToProcess % 100 == 0:
			print(f"{pid}: {rowsToProcess} elements left to process")
		ra = df.loc[i, 'J2000_ra_prop']
		dec = df.loc[i, 'J2000_dec_prop']
		g_mag = df.loc[i, 'phot_g_mean_mag']
		(mer_time, can_obsv) = __is_observable(ra, dec, g_mag)
		df.loc[i, 'mer_time'] = mer_time
		df.loc[i, 'can_obsv'] = can_obsv
		rowsToProcess -= 1

	obsv_targets = df[df.can_obsv]
	obsv_targets = obsv_targets.sort_values(by=['dec'])
	print(f"{pid}: {len(obsv_targets)} objects visible found")
	return obsv_targets

def __exportTargets(obsv_targets: pd.DataFrame):
	min_dec = obsv_targets.iloc[0]['dec']
	max_dec = obsv_targets.iloc[-1]['dec']
	output_file_path = os.path.join(RESULT_DIR, f"dec_{floor(min_dec)}_{ceil(max_dec)}.csv")
	obsv_targets.to_csv(output_file_path)
	printToLog(f"Results output to {output_file_path}")

def gaiaObservableTargets():
	if not os.path.exists(RESULT_DIR):
		os.makedirs(RESULT_DIR)

	df = pd.read_csv(DATA_FILE_PATH)
	print("Finished reading in Gaia CSV data.")
	# df = df.sample(20000)
	df = df.assign(can_obsv=lambda _: False, mer_time=lambda _: None)

	num_rows = len(df)
	print(f"Rows to process: {num_rows}")

	obsv_targets: pd.DataFrame
	with Pool(MAX_PARALLEL) as p:
		obsv_targets = pd.concat(p.map(__processSubset, np.array_split(df, MAX_PARALLEL)))
	print(f"Found total {len(obsv_targets)} visible objects")
	obsv_targets = obsv_targets.sort_values(by=['dec'])

	[__exportTargets(tgts) for tgts in np.array_split(obsv_targets, MAX_PARALLEL)]

if __name__ == "__main__":
	gaiaObservableTargets()