"""
Read in Gaia candidates from CSV file and determine which objects from Gaia are observable on the night in question.
"""

from obsrv_plan.general.params import TIMEZONE, OBSV_START_DATETIME, DATA_FILE_PATH, RESULT_DIR, MAX_PARALLEL, WORKING_DIR
from obsrv_plan.decorators.static_decorator import static_vars
from obsrv_plan.general.log import printToLog

import os
import csv

import numpy as np

import pandas as pd
import dask.dataframe as dd

import astropy.units as u
from math import ceil, floor
from datetime import timedelta
from multiprocessing import Pool

from astroplan import Observer
from astropy.coordinates import SkyCoord
from astropy.time import Time, TimeDelta

@static_vars(obsv=Observer(name="Iturbide", timezone=TIMEZONE,
					longitude=-99.895328*u.deg,
					latitude=24.75521 * u.deg,
					elevation=2400*u.m))
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
				g_mag <= 15)

def __processSubset(df_path: str):
	pid = os.getpid()
	printToLog(f"{pid}: Begin processing {df_path}", print_console=True)

	rowsProcessed = 0
	obsv_targets: pd.DataFrame
	with open(df_path, 'r') as csv_file:
		reader = csv.reader(csv_file)
		header = next(reader)
		RA_INDEX = header.index('J2000_ra_prop')
		DEC_INDEX = header.index('J2000_dec_prop')
		G_MAG_INDEX = header.index('phot_g_mean_mag')
		print(RA_INDEX, DEC_INDEX, G_MAG_INDEX)
		columns = header

		obsv_targets = pd.DataFrame(columns=columns)
		for row in reader:
			if len(row) == 0:
				continue # empty row
			if rowsProcessed % 100 == 0:
				print(f"{pid}: {rowsProcessed} rows processed")
			(mer_time, can_obsv) = __is_observable(float(row[RA_INDEX]), float(row[DEC_INDEX]), float(row[G_MAG_INDEX]))
			if can_obsv:
				row[-1] = mer_time
				row[-2] = can_obsv
				obsv_targets = pd.concat([obsv_targets, pd.DataFrame([row], columns=columns)], ignore_index=True)
			rowsProcessed += 1
	obsv_targets = obsv_targets.apply(pd.to_numeric, errors='ignore')

	obsv_targets = obsv_targets.sort_values(by=['dec'])
	print(f"{pid}: {len(obsv_targets)} objects visible found")
	return obsv_targets

def __exportTargets(obsv_targets: pd.DataFrame):
	min_dec = obsv_targets.iloc[0]['dec']
	max_dec = obsv_targets.iloc[-1]['dec']
	output_file_path = os.path.join(RESULT_DIR, f"dec_{floor(min_dec)}_{ceil(max_dec)}.csv")
	obsv_targets.to_csv(output_file_path, index=False)
	printToLog(f"Results output to {output_file_path}")

def gaiaObservableTargets():
	os.makedirs(RESULT_DIR, exist_ok=True)
	daskSplitsDir = os.path.join(WORKING_DIR, "dask-splits")

	if not os.path.exists(daskSplitsDir):
		df = dd.read_csv(DATA_FILE_PATH).repartition(npartitions=MAX_PARALLEL)
		# df = df.sample(frac=0.005)
		num_rows = len(df)
		print(f"Rows to process: {num_rows}")
		df = df.assign(can_obsv=lambda _: False, mer_time=lambda _: None)
		os.makedirs(daskSplitsDir, exist_ok=True)
		dd.to_csv(df, os.path.join(WORKING_DIR, "dask-splits", "*.csv"))

	obsv_targets: dd.DataFrame
	with Pool(MAX_PARALLEL) as p:
		obsv_targets = pd.concat(p.map(__processSubset, [os.path.join(daskSplitsDir, f) for f in os.listdir(daskSplitsDir)]))
	print(f"Found total {len(obsv_targets)} visible objects")
	obsv_targets = obsv_targets.sort_values(by=['dec'])
	for tgts in np.array_split(obsv_targets, MAX_PARALLEL):
		__exportTargets(tgts)

if __name__ == "__main__":
	gaiaObservableTargets()