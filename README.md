# CS 4804 Data Visualization Final Project

All code in this project is my own.

Python libraries used include:
- Pandas
- Numpy
- Xarray
- Matplotlib 
- Altair
- Panel

### Project Website and Screen Cast
The GitHub repository for this project can be found at https://github.com/pfrunzio/cs4804-final-project

The project website can be found at https://pfrunzio.github.io/cs4804-final-project/dashboard.html

The fully interactive dashboard can be hosted using this repository by running the command
`panel serve visualization.py --show`

A screen cast showing the interactive elements of this dashboard can be found at [https://www.loom.com/share/92999c74e503497cbf9d1b7fc3a2bf48](https://www.loom.com/share/92999c74e503497cbf9d1b7fc3a2bf48)

Process Book for this project can be found at https://github.com/pfrunzio/cs4804-final-project/blob/main/Process_Book.pdf


### How to Use
- Click a pixel on the magnetic field map to view the ODMR spectrum at that point.
- Select the experiment run time length with the slider.
- Use chart controls to zoom in on, pan across, and reset the magnetic field map. 

### Technical Achievements
Data Processing
- Converted experimental data from NumPy arrays in .npz files into a structured netCDF dataset using Xarray with labeled multidimensional access.
- Used efficient data handling, reducing a potential 99.5 million row flat dataframe by opting for a multidimensional array structure.
- Implemented spatial data downsampling from 1080x1920 to 108x192 maps, enabling interactive rendering of the magnetic field map without losing too much visual information.
Visualization
- Developed an interactive visualization dashboard in Python using multiple libraries including Pandas, NumPy, Xarray, Matplotlib, Altair, Panel, and Holoviews.
- Handled visualizing large datasets by enabling VegaFusion in Altair to bypass the default 5k row limit and support 20k datapoints.
- Built an interactive dashboard that allows for exploring experimental data in spatial and temporal dimensions.
- Used panel widgets and Python callbacks to dynamically update the visualizations based on user interaction.

Design Achievements
- Designed a multi-chart dashboard with a magnetic field map, pixel specific ODMR spectrum, global ODMR spectrum, and quantitative variable comparisons.
- Enabled spatial exploration of the experimental data by clicking any pixel on the magnetic field map to explore the associated ODMR spectrum. 
- Enabled temporal exploration of the experimental data through a slider that changes the experiment runtime length and updates all visualizations.
- Used color to connect magnetic field map and ODMR data visually and allowing the colorbar to serve as a key for both charts and help the user to make connections among other components of the data by using color as a visual clue to understand the magnetic field values.
- Improved comparative analysis by overlaying the selected pixel ODMR with the global average ODMR on the same chart.
- Designed the dashboard to minimize scrolling and show all relevant views simultaneously.
- Used clear axis labels and physical unit labels to allow for scientific interpretability consistent with physics research standards.
- Included user instructions for straightforward dashboard use.
