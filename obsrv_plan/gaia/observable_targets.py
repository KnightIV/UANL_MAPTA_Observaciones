"""
Read in Gaia candidates from CSV file and determine which objects from Gaia are observable on the night in question.
"""

from obsrv_plan.general.params import TIMEZONE, OBSV_START_DATETIME, DATA_FILE_PATH, RESULT_DIR
from obsrv_plan.decorators.static_decorator import static_vars

import os
import numpy as np
import pandas as pd
import astropy.units as u
from math import ceil, floor
from datetime import timedelta

from astroplan import Observer
from astropy.coordinates import SkyCoord
from astropy.time import Time, TimeDelta

@static_vars(obsv=Observer(longitude=-99.895328*u.deg, latitude=24.75521 * u.deg, 
						elevation=2400*u.m, name="Iturbide", timezone=TIMEZONE))
def __is_observable(ra, dec, g_mag):
	# ITURBIDE_OBSV = Observer(longitude=-99.895328*u.deg, latitude=24.75521 * u.deg, 
	# 					elevation=2400*u.m, name="Iturbide", timezone=TIMEZONE)
	ITURBIDE_OBSV = __is_observable.obsv
	FMT_STR = "%Y-%m-%dT%H:%M:%S"
	MER_TOLERANCE = TimeDelta(val=timedelta(hours=3))
	acceptable_time_range = [(OBSV_START_DATETIME + timedelta(hours=3)).strftime(FMT_STR),
							 (OBSV_START_DATETIME - timedelta(hours=3)).strftime(FMT_STR)]
	ideal_mer_time = Time(val=acceptable_time_range,
						  format="isot",
						  location=ITURBIDE_OBSV.location)

	target = SkyCoord(ra, dec, unit="deg", frame="icrs", obstime="J2000")
	mer_time = ITURBIDE_OBSV.target_meridian_transit_time(
		time=Time(val=OBSV_START_DATETIME),
		target=target)

	return (mer_time, ITURBIDE_OBSV.is_night(time=mer_time, horizon=-6 * u.deg) and
			ITURBIDE_OBSV.target_is_up(target=target, time=mer_time, horizon=-6 * u.deg) and
			np.any(ideal_mer_time.isclose(other=mer_time, atol=MER_TOLERANCE)) and
			g_mag <= 16)

def gaiaObservableTargets():
	df = pd.read_csv(DATA_FILE_PATH)
	df = df.assign(can_obsv=lambda _: False, mer_time=lambda _: None)
	df.head()

	num_rows = len(df)
	print(f"Rows to process: {num_rows}")

	process_progress = 0
	for i in df.index:
		if process_progress % 100 == 0 or process_progress == num_rows - 1:
			print(f"{process_progress} elements processed")
		ra = df.loc[i, 'j2000_ra_prop']
		dec = df.loc[i, 'j2000_dec_prop']
		g_mag = df.loc[i, 'phot_g_mean_mag']
		(mer_time, can_obsv) = __is_observable(ra, dec, g_mag)
		df.loc[i, 'mer_time'] = mer_time
		df.loc[i, 'can_obsv'] = can_obsv
		process_progress += 1

	obsv_targets = df[df.can_obsv]
	obsv_targets = obsv_targets.sort_values(by=['dec'])
	result_dir_path = RESULT_DIR
	if not os.path.exists(result_dir_path):
		os.makedirs(result_dir_path)

	for _, df_i in enumerate(np.array_split(obsv_targets, 10)):
		min_dec = df_i.iloc[0]['dec']
		max_dec = df_i.iloc[-1]['dec']
		output_file_path = os.path.join(result_dir_path, f"dec_{floor(min_dec)}_{ceil(max_dec)}.csv")
		df_i.to_csv(output_file_path)
		print(f"Results output to {output_file_path}")
	print(obsv_targets.head())

if __name__ == "__main__":
	gaiaObservableTargets()