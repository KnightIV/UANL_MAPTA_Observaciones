import modin.pandas as pd
import matplotlib.pyplot as plt

PHOTOMETRY_CSV_PATH = r"/home/ramon/uanl/Tesis/Gaia DataLink/rcabal011663969705127/EPOCH_PHOTOMETRY_COMBINED.csv"

def plotBand(source_id, bands, vals, axsRow):
	axsRow[0].set_title(f"{source_id} Magnitude")
	axsRow[1].set_title(f"{source_id} Flux")

	for band in bands:
		filteredBand = vals[vals['band'] == band]
		axsRow[0].scatter(filteredBand['time'], filteredBand['mag'], label=f"{band}")
		axsRow[1].scatter(filteredBand['time'], filteredBand['flux'], label=f"{band}")
	
	axsRow[0].legend()

if __name__ == "__main__":
	df = pd.read_csv(PHOTOMETRY_CSV_PATH)
	df = df[df['rejected_by_photometry'] == False]

	source_ids = df['source_id'].unique()
	bands = df['band'].unique()

	fig, axs = plt.subplots(2, len(source_ids))
	fig.suptitle(f"GDR2 Light Curves")

	for i in range(len(source_ids)):
		source_id = source_ids[i]
		axsRow = axs[i]
		sourceVals = df[df['source_id'] == source_ids[i]]
		plotBand(source_id, bands, sourceVals, axsRow)

	plt.show()