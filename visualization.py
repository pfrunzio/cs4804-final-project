import xarray as xr
import pandas as pd
import altair as alt
import numpy as np
import panel as pn
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import holoviews as hv
from holoviews import opts, streams

pn.extension('vega')
alt.data_transformers.enable("vegafusion")
hv.extension('bokeh')



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

def compute_global_odmr(ds, t_idx):
    f=np.linspace(2.81e9, 2.92e9, 2000)
    odmr_signal = np.zeros_like(f)

    s_arr = [0, -2.16e6, 2.16e6]

    #first resonance
    params = ds["fit_params"].isel(t=t_idx, fit=0).mean(dim=("x","y"))
    f0_0 = params.sel(param="f0").values
    a1, a2, a3 = params.sel(param="a1").values, params.sel(param="a2").values, params.sel(param="a3").values
    a_arr_0 = [a1, a2, a3]

    l_0 = params.sel(param="l").values
    off_0 = params.sel(param="off").values

    #second resonance
    params = ds["fit_params"].isel(t=t_idx, fit=1).mean(dim=("x","y"))
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
t_slider = pn.widgets.IntSlider(name="Experiment Run Time", start=0, end=ds.dims["t"]-1, step=1)

# Store selected pixel
x_pixel_widget = pn.widgets.IntSlider(name="x_pixel", start=0, end=ds.sizes["x"]-1, visible=False)
y_pixel_widget = pn.widgets.IntSlider(name="y_pixel", start=0, end=ds.sizes["y"]-1, visible=False)

# @pn.depends(t_slider)
# def heatmap_chart(t_idx):
#     B = ds.isel(t=t_idx)
#     df = B.to_dataframe().reset_index()  # x, y, B

#     color_scale = alt.Scale(domain=[df["B"].min(), df["B"].max()], scheme='turbo')

#     #bfield chart
#     click = alt.selection_single(fields=['x','y'], on='click')
#     chart = alt.Chart(df).mark_rect().encode(
#         x=alt.X('x:O', axis=None),
#         y=alt.Y('y:O', axis=None),
#         color=alt.Color('B:Q', scale=color_scale, legend=alt.Legend(title='mT', format='.6f', tickCount=8)),
#         tooltip=['x','y','B']
#     ).add_selection(click).properties(
#         title="Magnetic Field Map",
#         width=192*3, 
#         height=108*3
#     )

#     return pn.pane.Vega(chart.to_dict(format="vega"))

@pn.depends(t_slider)
def heatmap_chart_hv(t_idx):
    B = ds.isel(t=t_idx)
    df = B.to_dataframe().reset_index()

    heatmap = hv.HeatMap(df, kdims=['x','y'], vdims=['B']).opts(
        width=192*3,
        height=108*3,
        tools=['hover', 'tap'],
        colorbar=True,
        cmap='turbo',
        nonselection_alpha=1.0
    )

    tap = streams.Tap(source=heatmap)
    def update_pixel_from_tap(**kwargs):
        x = kwargs.get('x')
        y = kwargs.get('y')
        if x is not None and y is not None:
            x_pixel_widget.value = int(x)
            y_pixel_widget.value = int(y)
    tap.add_subscriber(update_pixel_from_tap)

    overlay = heatmap.opts(title="Magnetic Field Map")
    return pn.panel(overlay)

@pn.depends(t_slider, x_pixel_widget, y_pixel_widget)
def odmr_line_chart(t_idx, x_pixel, y_pixel):
    f, pixel_signal = compute_odmr(ds, t_idx, x_pixel, y_pixel)
    f, global_signal = compute_global_odmr(ds, t_idx)

    df = pd.DataFrame({
        "Frequency": np.concatenate([f, f]),
        "ODMR": np.concatenate([global_signal, pixel_signal]),
        "Type": ["Global Average"]*len(f) + ["Selected Pixel"]*len(f)
    })

    #set scales
    y_scale = alt.Scale(domain=[0.98, 1.001])
    x_scale = alt.Scale(domain=[2.81, 2.92])

    #change color with bfield map
    B = ds.isel(t=t_idx)
    bfield_df = B.to_dataframe().reset_index()
    cmap = cm.get_cmap("turbo")
    norm = mcolors.Normalize(vmin=bfield_df["B"].min(), vmax=bfield_df["B"].max())
    B_val = float(B["B"].isel(x=x_pixel, y=y_pixel).values)
    rgba = cmap(norm(B_val))
    line_color = mcolors.to_hex(rgba)

    chart = alt.Chart(df).mark_line().encode(
        x=alt.X("Frequency:Q", title="Microwave Frequency (GHz)", scale=x_scale),
        y=alt.Y('ODMR:Q', title="Normalized Fluorescence Intensity", scale=y_scale),
        color=alt.Color(
            "Type:N",
            scale=alt.Scale(
                domain=["Global Average", "Selected Pixel"],
                range=["grey", line_color],
            ),
            title="Key"
        )
    ).properties(
        width=400,
        height=350,
        title="ODMR"
    )

    print("Updating ODMR:", t_idx, x_pixel, y_pixel)

    return pn.pane.Vega(chart.to_dict(format="vega"))

@pn.depends(t_slider, x_pixel_widget, y_pixel_widget)
def variable_table(t_idx, x_pixel, y_pixel):

    #pixel values
    B_pixel = ds["B"].isel(t=t_idx, x=x_pixel, y=y_pixel).values
    chi_pixel = ds["chi_squared"].isel(t=t_idx, x=x_pixel, y=y_pixel).values

    c1_pixel = ds["contrast"].isel(t=t_idx, fit=0, x=x_pixel, y=y_pixel).values
    c2_pixel = ds["contrast"].isel(t=t_idx, fit=1, x=x_pixel, y=y_pixel).values

    # l1_pixel = ds["linewidth"].isel(t=t_idx, fit=0, x=x_pixel, y=y_pixel).values
    # l2_pixel = ds["linewidth"].isel(t=t_idx, fit=1, x=x_pixel, y=y_pixel).values

    #global values
    B_global = ds["B"].isel(t=t_idx).mean(dim=("x","y")).values
    chi_global = ds["chi_squared"].isel(t=t_idx).mean(dim=("x","y")).values

    c1_global = ds["contrast"].isel(t=t_idx, fit=0).mean(dim=("x","y")).values
    c2_global = ds["contrast"].isel(t=t_idx, fit=1).mean(dim=("x","y")).values

    # l1_global = ds["linewidth"].isel(t=t_idx, fit=0).mean(dim=("x","y")).values
    # l2_global = ds["linewidth"].isel(t=t_idx, fit=1).mean(dim=("x","y")).values

    df = pd.DataFrame({
        "Variable": [
            "Magnetic Field (mT)",
            "Chi Squared Fit",
            "Contrast Fit 1 (%)",
            "Contrast Fit 2 (%)"
            # "Linewidth Fit 1 (MHz)",
            # "Linewidth Fit 2 (MHz)"
        ],
        "Selected Pixel": [
            f"{B_pixel:.6f}",
            f"{chi_pixel:.3e}",
            f"{c1_pixel:.2f}",
            f"{c2_pixel:.2f}"
            # f"{l1_pixel:.2f}",
            # f"{l2_pixel:.2f}"
        ],
        "Global Average": [
            f"{B_global:.6f}",
            f"{chi_global:.3e}",
            f"{c1_global:.2f}",
            f"{c2_global:.2f}"
            # f"{l1_global:.2f}",
            # f"{l2_global:.2f}"
        ]
    })

    return pn.pane.DataFrame(df, width=400, height=150, index=False)



header = pn.pane.Markdown(
    """
# Quantum Sensing Magnetometry Dashboard
By Paola Frunzio
""",
    width=1500
)

instructions = pn.pane.Markdown(
    """
### How to Use
- Click a pixel on the magnetic field map to view the ODMR spectrum at that point.
- Select the experiment run time length with the slider.
- Use chart controls to zoom in on, pan across, and reset the magnetic field map. 
""",
    width=500, height=150
)

body = pn.pane.Markdown(
    """

The above interactive visualization explores magnetic field measurements collected using Nitrogen-Vacancy (NV) Centers in Diamond for quantum sensing. The visualization allows users to navigate the experiment across both spatial and temporal dimensions, clicking on any pixel in the magnetic field map to see the Optically Detected Magnetic Resonance (ODMR) spectrum used to calculate the field at that location and comparing it to the global average. This dashboard helps show several patterns: the quality of the ODMR fits as seen in the chi_squared variable values improves steadily as longer experiment run times accumulate more data, the two resonance dips in the ODMR chart are consistently asymmetric, and certain regions of the magnetic field map have noticeably lower contrast which suggests larger measurement uncertainty. This dashboard demonstrates that interactive visualizations like this one can help develop additional insight on complex, high dimensional data that would be difficult to detect with static plots alone.

Process Book Link: https://github.com/pfrunzio/cs4804-final-project/blob/main/Process_Book.pdf
Data Link: https://github.com/pfrunzio/cs4804-final-project/blob/main/processed_data.nc
Screen Cast Link: https://www.loom.com/share/92999c74e503497cbf9d1b7fc3a2bf48

<div style="position: relative; padding-bottom: 49.375%; height: 0;"><iframe src="https://www.loom.com/embed/92999c74e503497cbf9d1b7fc3a2bf48" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></iframe></div>
""",
    width=1500
)

dashboard = pn.Column(
    header,
    pn.Row(
        pn.Column(
            instructions,
            heatmap_chart_hv,
            t_slider
        ),
        pn.Column(
            variable_table,
            odmr_line_chart
        )
    ),
    body
)


# dashboard.servable()
dashboard.save("dashboard.html")


