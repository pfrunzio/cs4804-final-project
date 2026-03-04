import pandas as pd 
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

batch_timelength = .5
nt = 24 #full 48 eventually
nx = 1080
ny = 1920
nfit = 2
nparam = 6


#helper function
f = np.linspace(2.81e9, 2.92e9, 400_000)
s_arr = np.array([-2.16e6, 0, 2.16e6])
def compute_fwhm(ds):
    linewidth_arr = np.zeros((nfit, nx, ny), dtype=np.float32)

    for fit in range(nfit):
        fit_params = ds["fit_params"].isel(fit=fit)

        #extract parameters
        a1 = fit_params.sel(param="a1").values
        a2 = fit_params.sel(param="a2").values
        a3 = fit_params.sel(param="a3").values
        l = fit_params.sel(param="l").values
        f0 = fit_params.sel(param="f0").values
        off = fit_params.sel(param="off").values
        contrast = ds["contrast"].isel(fit=fit).values/100

        # fig, axs = plt.subplots(1)

        #compute exact linewidth per pixel
        for i in range(nx):
            for j in range(ny):
                func = 1 + off[i,j]
                half_max = 1 + off[i,j] - contrast[i,j]/2
                a_arr = [a1[i,j], a2[i,j], a3[i,j]]
                l_val = l[i,j]
                f0_val = f0[i,j]

                # plt.axhline(y=half_max)

                for k in range(3):
                    lor = a_arr[k] * (l_val**2 / ((f - f0_val + s_arr[k])**2 + l_val**2))
                    func -= lor
                    # plt.plot(f, 1- lor, label=f"lorenztian {i}")

                idx = np.argwhere(np.diff(np.sign(func - half_max))).flatten()
                linewidth_arr[fit, i, j] = (f[idx[-1]] - f[idx[0]]) * 1e-6

                # plt.tight_layout()
                # plt.show()
        print(f"fit {fit} complete")
    
    return linewidth_arr


#create data structure
ds = xr.Dataset(
    {
        "B": (("t", "x", "y"),
              np.zeros((nt, nx, ny), dtype="float64"),
              {"units": "mT", "long_name": "Magnetic Field"}
        ),

        "chi_squared": (("t", "x", "y"),
                        np.zeros((nt, nx, ny), dtype="float32"),
                        {"units": "dimensionless", "long_name": "Chi-squared Fit"}
        ),

        "fit_params": (
            ("t", "fit", "param", "x", "y"),
            np.zeros((nt, nfit, nparam, nx, ny), dtype="float32"),
            {"long_name": "ODMR fit parameters"}
        ),

        "contrast": (
            ("t", "fit", "x", "y"),
            np.zeros((nt, nfit, nx, ny), dtype="float32"),
            {"units": "%", "long_name": "ODMR contrast"}
        ),

        "linewidth": (
            ("t", "fit", "x", "y"),
            np.zeros((nt, nfit, nx, ny), dtype="float32"),
            {"units": "MHz", "long_name": "ODMR linewidth"}
        ),
    },
    coords={
        "t": np.arange(nt),
        "x": np.arange(nx),
        "y": np.arange(ny),
        "fit": np.arange(nfit),
        "param": ["f0", "a1", "a2", "a3", "l", "off"],
        "param_units": ("param",["MHz", "arb", "arb", "arb", "MHz", "arb"]),
    },
)

#load in data
folder = "24hour-batches"
for t in range(nt):
    file_name = f"unprocessed-data/{folder}/run0-fit-batch{t+1}.npz"
    file = np.load(file_name, allow_pickle=True)
    # print(file.files)
    
    ds["B"][t] = file['bfield']
    ds["chi_squared"][t] = file['chi_squared']
    ds["fit_params"][t] = file['fit_params']
    
    ds["contrast"][t] = (
        ds["fit_params"][t]
        .sel(param=["a1", "a2", "a3"])
        .mean(dim="param")*100
    )

    #was taking too long to compute, ***fix later
    # ds["linewidth"][t] = compute_fwhm(ds.isel(t=t))

    # print(batch_timelength*(t+1))

#spatial data from 1080×1920 -> 108×192 to make it more managable
ds_small = ds.coarsen(x=10, y=10, boundary='trim').mean()

# reindex x and y to be integers
ds_small = ds_small.assign_coords(
    x=np.arange(1, ds_small.sizes["x"] + 1),
    y=np.arange(1, ds_small.sizes["y"] + 1)
)

#save processed data to file
ds_small.to_netcdf("processed_data.nc")
