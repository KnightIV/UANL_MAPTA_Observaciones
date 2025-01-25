# UANL_MAPTA_Observaciones

This repository contains the code developed for my master's thesis research project *The Search for Eclipsing Binary Systems and Photometric Analysis of ATO J339.9469+45.1464*. The full dissertation can be found in [this repository](https://github.com/KnightIV/UANL_MAPTA_Master_Thesis). The code is organized as follows:

```
├── analisis - Data analysis
│   ├── apo - Rudimentary analysis of spectra obtained from Apache Point Observatory (thanks to Dr. Paula Szkody)
│   ├── gaia - Light curve and spectra analysis of GDR3 data
│   ├── general - Common IO helper
│   ├── iturbide - IRAF helpers and analysis of IRAF differential aperture photometry results
│   ├── period-analysis - Determining orbital period from ZTF, GDR3, and Iturbide light curves
│   ├── phoebe_model - Photometric solution for ATOJ339 obtained using PHOEBE
│   └── ztf - ZTF light curve processing
├── obsrv_plan - Search for eclipsing binary systems of interest
│   ├── gaia - (WIP) Analysis of Gaia DR3 results in observational HR diagram
│   ├── general - Define common variables for use in obsrv_plan modules
│   └── filter-candidates.ipynb - Identifies ideal candidates for an observational campaign
├── mapta-tesis.yaml - Conda environment used during local development
└── phoebe-server.yaml - Conda environment used for offloading compute (PHOEBE optimization and MCMC sampling)
```

## Pre-requisites



## Object Search (`obsrv_plan`)

The notebook `filter-candidates.ipynb` takes as input the Gaia DR3 query results (performed through the ADQL interface in the [**Gaia Archive**](https://gea.esac.esa.int/archive/)), selects sources based on their SIMBAD classification (taking only *eclipsing binary systems* and candidates, as well as *cataclysmic variables* and candidates), and outputs to a file the sources that are visible from the *CDK-20* 0.5m telescope located at the **Observatorio Astronómico Universitario - Iturbide**. This list was used to select `ATO J339.9469+45.1464` for follow-up photometric observations.

## Data analysis (`analisis`)

The `analisis` directory contains a collection of notebooks employed for aiding in the processing of science and calibration images as well as analyzing the resulting photometric light curve using [PHOEBE](https://phoebe-project.org). 

### `apo/spectra-analysis.ipynb`

Processing of `ATO J339.9469+45.1464` spectra (integration time of 10 minutes each, corresponding to the orbital phase of maximum flux) obtained utilizing the KOSMOS 3.5m spectrograph at the *Apache Point Observatory*, courtesy of Dr. Paula Szkody. Outputs average of both individual spectra to improve estimated SNR; this averaged spectrum is then used for further analysis using the spectral typing tool [PyHammer](https://github.com/BU-hammerTeam/PyHammer).

### `gaia`

#### `light_curves.ipynb`

Visual analysis of Gaia DR3 light curves in each passband ($G$, $G_{BP}$, and $G_{RP}$). Outputs light curve data for all bands into a single `ecsv` file for convenient loading into a PHOEBE bundle.

#### `xp-mean-spectra.ipynb`

Reading and parsing of XP Mean Sampled Spectrum obtained through the Datalink service for Gaia DR3. This file contains the low-resolution spectrum of `ATO J339.9469+45.1464` encoded as a set of basis functions with the given coefficients. In order to analyze this data using PyHammer, this Notebook samples the mean spectrum at a fixed set of wavelengths and outputs the result to a `csv` file. An incomplete analysis of the interstellar extinction in the direction of `ATO J339.9469+45.1464`was attempted, using both F90 models with coefficients given by Savage et al. (1985), as well as calculating $E(B-V)$ values using the [`dustmaps`](https://dustmaps.readthedocs.io/en/latest/) Python package with the dust map reported by Green, Schlafly, Finkbeiner et al. (2019).

### `ztf`

Visual analysis of light curves from the *Zwicky Transient Facility* (ZTF) survey. Outputs light curve data from both passbands (ZTF:g and ZTF:r) to `csv` files for convenient loading into a PHOEBE bundle; these fluxes were normalized such that the color information between both passbands is preserved.

## PHOEBE Model

Located in the `analisis/phoebe_model` folder, 

## CCD Reduction Guide

https://www.astropy.org/ccd-reduction-and-photometry-guide/v/dev/notebooks/00-00-Preface.html 

## Astrometry

Main doc page: https://nova.astrometry.net/api_help

Base guide used for installation on Fedora: http://plaidhat.com/code/astrometry080-centos82.php