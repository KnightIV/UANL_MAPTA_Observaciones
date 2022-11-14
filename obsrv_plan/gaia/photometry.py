import modin.pandas as pd
import matplotlib.pyplot as plt

PHOTOMETRY_CSV_PATH = r"/run/media/ramon/USBD/Tesis/Gaia Analisis/Gaia Light Curves/EPOCH_PHOTOMETRY-Gaia DR3 1982536326650942336.csv"

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
	sourceIdCount = len(source_ids)
	bands = df['band'].unique()

	fig, axs = plt.subplots(2, sourceIdCount)
	fig.suptitle(f"GDR3 Light Curves")

	for i in range(sourceIdCount):
		source_id = source_ids[i]

		axsRow: None
		if sourceIdCount > 1:
			axsRow = axs[i]
		else:
			axsRow = axs
		sourceVals = df[df['source_id'] == source_ids[i]]
		plotBand(source_id, bands, sourceVals, axsRow)

	plt.show()