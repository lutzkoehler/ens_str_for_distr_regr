# Ensembling Strategies for Neural Network-based Distributional Regression

This repository provides Python-code accompanying the Thesis

> Köhler, L. (2023). 
> Ensembling Strategies for Neural Network-based Distributional Regression.
> Chair of Statistical Methods and Econometrics (Prof. Dr. Melanie Schienle, ECON, KIT).
> Supervision: Sebastian Lerch, Benedikt Schulz.

## Abstract

Ensembles, in particular neural network-based ensembles, are increasingly applied to improve the predictive performance of neural networks and to obtain uncertainty measures. For the latter, a distributional regression offers full access to the distribution's information based on which the modeller can calculate the needed uncertainty metrics. Yet, multiple design choices have to be made which poses a major challenge to generating neural network ensembles. These include the network design to model the distribution, the network architecture of each ensemble member and the aggregation strategies to combine the individual forecasts.

Therefore, this thesis evaluates different ensembling and aggregation strategy combinations on two simulated and nine open-source datasets to derive useful recommendations on what methods work well and when. The ensembling strategies include the naive ensemble based on random initialization as well as bagging and BatchEnsemble. Additionally, Bayesian neural networks, Monte Carlo dropout, concrete dropout and variational dropout only need a single training procedure to generate the ensemble. In general, this thesis distinguishes between a parametric approach, namely the distributional regression network, and a non-parametric one, the Bernstein quantile network, to predict distributions. Finally, the ensemble member forecasts are aggregated using the linear pool and Vincentization.

Based on the experiments, seven recommendations are derived. Overall, the Bernstein quantile network performs superior to the distributional regression network when the target's conditional distribution is unknown and vice versa. Furthermore, distributional regression networks can be improved by truncating the distributional assumption if applicable. In addition, bigger ensembles usually show better results than smaller ones. Moreover, even the smallest ensemble outperforms the mean network. The best performing ensembling methods are the naive ensemble and bagging. Yet, they take significantly longer to train and predict than the other methods. Thus, predictive performance and runtime need to be balanced out given the use case. As the aggregation strategies show only minor differences, no recommendation can be derived.


## Code

| File | Description |
| ---- | ----------- | 
| `BaseModel` | Abstract class for NN models. |
| `BQNModels` | NN models for Bernstein Quantile Networks. |
| `DRNModels` | NN models for Distributional Regression Networks. |
| ---- | ----------- |
| `figures` | Generation of figures. |
| `fn_basic` | Helper functions for network functions paper. |
| `fn_eval` | Functions for the evaluation of probabilistic forecasts. |
| `process_uci_datasets` | Function to transform UCI data into needed dataformat. |
| `results` | Functions to collect and summarize results. |
| ---- | ----------- | 
| `ss_0_data` | Data generation of simulated scenarios. |
| `ss_1_ensemble` | Deep ensemble generation. |
| `ss_2_aggregation` | Deep ensemble aggregation. |
| `ss_3_scores` | Evaluation of deep ensemble and aggregated forecasts. |
| ---- | ----------- | 
| `config` | Configuration file to specify datasets, NN architecture and relevant hyperparameters, among others. | 
| ---- | ----------- | 
| `data/` | Directory for the evaluation data. |
| `plots/` | Directory for the plots generated by the `figure`-file and notebooks. |
| `r_scripts` | Legacy R-code from https://github.com/benediktschulz/agg_distr_deep_ens |
| ---- | ----------- |
| `*.ipynb` | Notebooks to evaluate the results and generate plots for the thesis. |

## Data

### Simulation study

The simulated data, the deep ensembles and the aggregated forecasts result in files that are too large to be stored in this repository, thus we supply only the data on the evaluation of the forecasts. The files corresponding to the simulation study can be used to replicate the data, apply the network variants and aggregate the deep ensemble forecasts.

### UCI datasets

The data files result from the Gal & Ghahramani (2015) https://github.com/yaringal/DropoutUncertaintyExps and can be processed using the functions in `process_uci_datasets.py`.

## Results

Results of the final experiments and the thesis can be found under `data/results/final_results_*`. Corresponding plots are available under `plots/final_results_*`.

## How To

### Environment and dependencies

Used packages and the environment can be found in `ens_str_for_distr_regr.yml` or `requirements.txt`.

### Configuration

**Dataset** Specify the datasets as a list in `DATASET`. Possible datasets are listed in `_available_DATASET`.

**Ensemble method** Specify the ensemble method as a string in `ENS_METHOD`. Possible ensemble methods are listed in `_available_ENS_METHOD`.

**Neural Network architecture** Specify the NN archiecture as a three-dimensional list in `NN_DEEP_ARCH`. Each layer is specified as a list of a string specifying the name of the layer and an int specifying the number of neurons. Additional layers can be added. If different architectures should be distributed across the ensemble members, add another list in the first dimension. Examples are shown in `_available_NN_ARCH`.

**Paths** Paths to the data, input, results, ensemble model, aggregated model and plots directory need to be specified in `PATHS`.

**Hyperparameters** Relevant hyperparameters need to be specified in `PARAMS`. These include the loss function. Available ones are shown in `_available_LOSS`. These include a normal distribution, the zero-truncated and upper-lower truncated normal distribution. The two float values refer to the upper-lower truncated distr. and don't apply to the other two.

**NN design** Specify the NN designs that should be run in `NN_VEC`. Possible ones are shown in `_available_NN_VEC`.

**Aggregation methods** Specify the aggregation methods for both DRN and BQN in `AGG_METHS_LS`. Possible ones are `"lp"`, `"vi"`, `"vi-w"`, `"vi-a"` and `"vi-aw"`.

**Simulation runs** Specify the number of simulation runs in `N_SIM`.

**Ensemble size** Specify the ensemble size in `N_ENS`.

**Number of predictions to average** Specify the number of predictions that should be averaged for single models in `N_MEAN_PREDICTION`.

**Cores** Specify the number of cores used in `NUM_CORES`.

### Additional configuration

Additionally, other hyperparameters like the batch size can be set in the `init` functions of the model classes (`DRNModels.py` and `BQNModels.py`).


### Generating deep ensembles

Deep ensembles are generated in `ss_1_ensemble.py`. On the top of the file, single models (BNN and dropout), parallel models (BatchEnsemble) and multi models (naive ensemble / random initialization and bagging) are specified. Each type uses a different function. Additionally, parallelization and the corresponding cores can be set at the end of the file. 

### Aggregating deep ensembles

Deep ensemble forecasts are aggregated in `ss_2_aggregation.py`. Parallelization and the corresponding cores can be set at the end of the file.
