import xarray as xr
import pandas as pd
import altair as alt
import numpy as np
import panel as pn
import matplotlib.cm as cm
import matplotlib.colors as mcolors

pn.extension('vega')
alt.data_transformers.enable("vegafusion")

ds = xr.open_dataset("processed_data.nc")

def compute_odmr(ds, t_idx, x_pixel, y_pixel):
    f=np.linspace(2.81e9, 2.92e9, 2000)
    odmr_signal = np.zeros_like(f)

    s_arr = [0, -2.16e6, 2.16e6]

    #first resonance
    params = ds["fit_params"].isel(t=t_idx, fit=0).isel(x=x_pixel, y=y_pixel)
    f0_0 = params.sel(param="f0").values
    a1, a2, a3 = params.sel(param="a1").values, params.sel(param="a2").values, params.sel(param="a3").values
    a_arr_0 = [a1, a2, a3]

    l_0 = params.sel(param="l").values
    off_0 = params.sel(param="off").values

    #second resonance
    params = ds["fit_params"].isel(t=t_idx, fit=1).isel(x=x_pixel, y=y_pixel)
    f0_1 = params.sel(param="f0").values
    a1, a2, a3 = params.sel(param="a1").values, params.sel(param="a2").values, params.sel(param="a3").values
    a_arr_1 = [a1, a2, a3]

    l_1 = params.sel(param="l").values
    off_1 = params.sel(param="off").values
    
    #compute
    odmr_signal = 1 + (off_0+off_1)/2
    
    for k in range(3):
        lorenztian = a_arr_0[k] * (l_0**2 / ((f - f0_0 + s_arr[k])**2 + l_0**2))
        odmr_signal -= lorenztian

    for k in range(3):
        lorenztian = a_arr_1[k] * (l_1**2 / ((f - f0_1 + s_arr[k])**2 + l_1**2))
        odmr_signal -= lorenztian

    #fix units
    f = f * 1e-9

    return f, odmr_signal



#panel widgets
t_slider = pn.widgets.IntSlider(name="Time Step", start=0, end=ds.dims["t"]-1, step=1)

# Store selected pixel
x_pixel_widget = pn.widgets.IntSlider(name="x_pixel", start=0, end=ds.sizes["x"]-1, visible=False)
y_pixel_widget = pn.widgets.IntSlider(name="y_pixel", start=0, end=ds.sizes["y"]-1, visible=False)

@pn.depends(t_slider)
def heatmap_chart(t_idx):
    B = ds.isel(t=t_idx)
    df = B.to_dataframe().reset_index()  # x, y, B

    color_scale = alt.Scale(domain=[df["B"].min(), df["B"].max()], scheme='turbo')

    #bfield chart
    click = alt.selection_single(fields=['x','y'], on='click')
    chart = alt.Chart(df).mark_rect().encode(
        x=alt.X('x:O', axis=None),
        y=alt.Y('y:O', axis=None),
        color=alt.Color('B:Q', scale=color_scale, legend=alt.Legend(title='μT', format='.8f', tickCount=8)),
        tooltip=['x','y','B']
    ).add_selection(click).properties(width=192*3, height=108*3)
    
    return pn.pane.Vega(chart.to_dict(format="vega"))

@pn.depends(t_slider, x_pixel_widget, y_pixel_widget)
def odmr_line_chart(t_idx, x_pixel, y_pixel):
    f, signal = compute_odmr(ds, t_idx, x_pixel, y_pixel)
    df = pd.DataFrame({"Microwave Frequency (GHz)": f, "Normalized Fluorescence Intensity": signal})

    y_scale = alt.Scale(domain=[0.98, 1.001])

    #change color with bfield map
    B = ds.isel(t=t_idx)
    bfield_df = B.to_dataframe().reset_index()
    cmap = cm.get_cmap("turbo")
    norm = mcolors.Normalize(vmin=bfield_df["B"].min(), vmax=bfield_df["B"].max())
    B_val = float(B["B"].isel(x=x_pixel, y=y_pixel).values)
    rgba = cmap(norm(B_val))
    line_color = mcolors.to_hex(rgba)

    chart = alt.Chart(df).mark_line(color=line_color).encode(
        x='Microwave Frequency (GHz):Q',
        y=alt.Y('Normalized Fluorescence Intensity:Q', scale=y_scale)
    ).properties(width=400, height=400)

    print("Updating ODMR:", t_idx, x_pixel, y_pixel)

    return pn.pane.Vega(chart.to_dict(format="vega"))

dashboard = pn.Row(
    pn.Column("## Magnetic Field Map", t_slider, heatmap_chart),
    pn.Column("## ODMR", odmr_line_chart)
)

dashboard.servable()
# dashboard.save("dashboard.html")


