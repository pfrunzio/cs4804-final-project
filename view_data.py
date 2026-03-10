import numpy as np

file_name = "unprocessed-data/24hour-batches/run0-fit-batch1.npz"
file = np.load(file_name, allow_pickle=True)
print(file.files)

# fit_params = file['fit_params']
# print(fit_params.shape)

# chi_squared = file['chi_squared']
# print(chi_squared.shape)
bfield = file['bfield']
print(bfield.shape)