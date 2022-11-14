from obsrv_plan.general.params import DATA_FILE_PATH

import matplotlib.pyplot as plt
import modin.pandas as pd

if __name__ == '__main__':
	G_PROP = "phot_g_mean_mag"
	BP_RP_PROP = "bp_rp"

	df = pd.read_csv(DATA_FILE_PATH)
	g = df[G_PROP]
	bp_rp = df[BP_RP_PROP]

	plt.xlabel("$G_{BP} - G_{RP}$")
	plt.ylabel("$G$")

	plt.scatter(bp_rp, g)
	plt.yscale([-16, 24])
	plt.show()