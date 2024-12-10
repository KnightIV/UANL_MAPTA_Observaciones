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

## Object Search (`obsrv_plan`)

The notebook `filter-candidates.ipynb` takes as input the Gaia DR3 query results (performed through the ADQL interface in the [**Gaia Archive**](https://gea.esac.esa.int/archive/)), selects sources based on their SIMBAD classification (taking only *eclipsing binary systems* and candidates, as well as *cataclysmic variables* and candidates), and outputs to a file the sources that are visible from the *CDK-20* 0.5m telescope located at the **Observatorio Astronómico Universitario - Iturbide**. This list was used to select `ATO J339.9469+45.1464` for follow-up photometric observations.

## Data analysis (`analisis`)

The `analisis` directory contains a collection of notebooks employed for aiding in the processing of science and calibration images as well as analyzing the resulting photometric light curve using [PHOEBE](https://phoebe-project.org). 

## CCD Reduction Guide

https://www.astropy.org/ccd-reduction-and-photometry-guide/v/dev/notebooks/00-00-Preface.html 

## Astrometry

Main doc page: https://nova.astrometry.net/api_help

Base guide used for installation on Fedora: http://plaidhat.com/code/astrometry080-centos82.php