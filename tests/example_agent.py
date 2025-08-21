import catdegus.active_learning.acquisition as aq
import catdegus.active_learning.gaussian_process as gpc
import catdegus.visualization.plot as pl

import argparse
import json
import sys
from s3fileHandler import get_data_s3
from s3fileHandler import upload_files_s3

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument("--catalyst-data", help="preprocessed time-on-stream catalyst testing data", type=str, default='20250228_sheet_for_ML_unique.xlsx')
parser.add_argument("--target-metric", help="target metric as output of GP surrogate model", type=str, default='CO2 Conversion (%)_initial value') # one of the columns in 'catalyst-data'

parser.add_argument("--min-reaction-temp", help="lower bound on reaction temperature", type=int, default=300)
parser.add_argument("--max-reaction-temp", help="lower bound on reaction temperature", type=int, default=550)
parser.add_argument("--step-reaction-temp", help="step size for reaction temerature", type=int, default=50)

parser.add_argument("--min-weight-loading", help="lower bound on Rh weight loading (wt%)", type=float, default=0.1)
parser.add_argument("--max-weight-loading", help="lower bound on Rh weight loading (wt%)", type=float, default=1.0)
parser.add_argument("--step-weight-loading", help="step size for Rh weight loading (wt%)", type=float, default=0.1)

parser.add_argument("--min-total-mass", help="lower bound on Rh total mass (mg)", type=float, default=0.005)
parser.add_argument("--max-total-mass", help="lower bound on Rh total mass (mg)", type=float, default=0.02)
parser.add_argument("--step-total-mass", help="step size for Rh total mass (mg)", type=float, default=0.0025)

parser.add_argument("--n-candidates", help="number of candidates to suggest for most informative experimental conditions with the largest uncertainity", type=int, default=5)
parser.add_argument("--synth-method", help="synthesis method for which most informative experimental conditions are desired", type=str, default='NP')
    # NP: Nanoprecipitation
    # WI: Wet Impregnation

args = parser.parse_args()

s3_bucket = "catdegus-io-data"
_path_to_data = get_data_s3(s3_bucket, args.catalyst_data) # check local or s3
if (_path_to_data == "file-not-found"):
    print("ERROR: Testing Data file not found!")
    sys.exit(1) 

# Define inputs to code --------
path_to_data = _path_to_data
target_metric = args.target_metric
x_range_min = [args.min_reaction_temp, args.min_weight_loading, args.min_total_mass, 0]                  # Lower boundaries for Temperature, Rh weight loading (wt%), Rh total mass (mg), Synthesis method
x_range_max = [args.max_reaction_temp, args.max_weight_loading, args.max_total_mass, 1]                  # Upper boundaries for Temperature, Rh weight loading (wt%), Rh total mass (mg), Synthesis method
x_step = [args.step_reaction_temp, args.step_weight_loading, args.step_total_mass, 1]                    # Step sizes for each feature
n_candidates = args.n_candidates                                                                         # Code will suggest top n_candidates informative conditions
temps_to_plot_2d = list(range(args.min_reaction_temp,args.max_reaction_temp, args.step_reaction_temp))   # Temperatures to plot in the 2d acquisition function
synth_method_to_plot = args.synth_method                                                                 # Synthesis method to plot the 2d/3d acquisition function for
# -----------------------------

# Train the Gaussian Process model
GP = gpc.GaussianProcess()
GP.preprocess_data_at_once(path=path_to_data,
                           target=target_metric,
                           x_range_min=x_range_min, x_range_max=x_range_max)
GP.train_gp()

# Construct the discrete grid for optimization
Grid = aq.DiscreteGrid(
    GP=GP,
    x_range_min=x_range_min, x_range_max=x_range_max, x_step=x_step
)
Grid.construct_grid()

result=Grid.optimize_posterior_std_dev_discrete(synth_method=synth_method_to_plot, n_candidates=n_candidates)
# Grid.optimize_upper_confidence_bound_discrete(synth_method_num='NP', n_candidates=5)
top_candidates=result.to_json()
with open(f"./posterior_std_dev_synth_{synth_method_to_plot}_top_{n_candidates}_candidates.json", 'w') as f:
    json.dump(top_candidates, f, indent=4)

# Plot the 2D/3D acquisition function
Plot = pl.Plotter(GP=GP, Grid=Grid)

# Plot.plot_2d_acquisition_function(
#     synth_method=synth_method_to_plot,
#     acq_max=1.1,
#     n_levels=32,
#     temperature_list=temps_to_plot_2d,
#     mode='custom', #'boundary',
#     custom_range=(0.0, 6.0, 0.0, 0.05),  # Custom range for contour plot
#     contour_resolution=50,
#     plot_allowed_grid=True,
#     plot_train=True,
#     show=False
# )

Plot.plot_3d_acquisition_function(
    synth_method=synth_method_to_plot,
    acq_max=1.1,
    mode='boundary', #'custom',
    custom_range=(0.0, 6.0, 0.0, 0.05, 300, 550),  # Custom range for contour plot
    contour_resolution=20,
    plot_allowed_grid=True,
    plot_train=True,
    show=False
)

# upload all locally produced json, png files to AWS s3 bucket
upload_files_s3(bucket=s3_bucket, extn='json')
upload_files_s3(bucket=s3_bucket, extn='png')