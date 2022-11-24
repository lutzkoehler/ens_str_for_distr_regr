## Simulation study: Script 1
# Generation of deep ensembles


import multiprocessing
import os
import pickle
import time
import itertools

import numpy as np
from joblib import Parallel, delayed


import fn_nn_ss
from fn_basic import fn_upit


def run_ensemble(
    i_scenario, i_sim, n_ens, nn_vec, data_in_path, data_out_path
):
    # Choose number of cores
    num_cores = multiprocessing.cpu_count() / 2 - 1
    # if pc == "simu":
    #     num_cores = 10

    ### Loop over scenarios ###
    # for i_scenario in scenario_vec:
    #    for i_sim in range(n_sim):
    ### Get data ###
    # Load corresponding data
    temp_data_in_path = os.path.join(
        data_in_path, f"scen_{i_scenario}_sim_{i_sim}.pkl"
    )
    with open(temp_data_in_path, "rb") as f:
        (
            X_train,
            y_train,
            X_test,
            y_test,
            f_opt,
            scores_opt,
        ) = pickle.load(f)

    # Indices of validation set
    if i_scenario == 6:
        i_valid = np.arange(start=2500, stop=3000, step=1)
    else:
        i_valid = np.arange(start=5000, stop=6000, step=1)

    # Observations of validation set
    y_valid = y_train[i_valid]

    ### Loop over network variants ###
    # For-Loop over network variants
    for temp_nn in nn_vec:
        # Read out function
        fn_pp = getattr(fn_nn_ss, f"{temp_nn}_pp")

        # Set seed (same for each network variant)
        np.random.seed(123 + 10 * i_scenario + 100 * i_sim)

        # For-Loop over ensemble member
        for i_ens in range(n_ens):
            # Take time
            start_time = time.time_ns()

            # Postprocessing
            pred_nn = fn_pp(
                train=X_train,
                test=np.r_[X_train[i_valid, :], X_test],
                y_train=y_train,
                y_test=np.hstack((y_valid, y_test)),
                i_valid=i_valid,
                n_ens=n_ens,
                n_cores=num_cores,
            )

            # Transform ranks
            if "rank" in pred_nn["scores"].keys():
                pred_nn["scores"]["pit"] = fn_upit(
                    ranks=pred_nn["scores"]["rank"],
                    max_rank=max(pred_nn["scores"]["rank"]),
                )

                # Omit ranks
                pred_nn["scores"]["rank"] = np.nan

            # Take time
            end_time = time.time_ns()

            # Save ensemble member
            filename = os.path.join(
                f"{temp_nn}_scen_{i_scenario}_sim_{i_sim}_ens_{i_ens}.pkl",  # noqa: E501
            )
            temp_data_out_path = os.path.join(data_out_path, filename)

            with open(temp_data_out_path, "wb") as f:
                pickle.dump([pred_nn, y_valid, y_test], f)

            print(
                f"{temp_nn.upper()}: Finished training of {filename}"
                f" - {(end_time - start_time)/1e+9}s",
            )


if __name__ == "__main__":
    # Path of simulated data
    data_in_path = os.path.join("data", "ss_data")

    # Path of deep ensemble forecasts
    data_out_path = os.path.join("data", "model")

    ### Initialize ###
    # Networks
    # nn_vec = ["drn", "bqn"]  # For now without "hen"
    nn_vec = ["bqn"]

    # Models considered
    # scenario_vec = range(1, 7, 1)
    scenario_vec = [1, 4]

    # Number of simulated runs
    # n_sim = 50
    n_sim = 10

    # Size of network ensembles
    # n_ens = 40
    n_ens = 10

    ### Run sequential ###
    # for i_scenario in scenario_vec:
    #    for i_sim in range(n_sim):
    #        run_ensemble(
    #            i_scenario, i_sim, n_ens, nn_vec, data_in_path, data_out_path
    #        )

    ### Run parallel ###
    Parallel(n_jobs=7, backend="multiprocessing")(
        delayed(run_ensemble)(
            i_scenario=i_scenario,
            i_sim=i_sim,
            n_ens=n_ens,
            nn_vec=nn_vec,
            data_in_path=data_in_path,
            data_out_path=data_out_path,
        )
        for i_scenario, i_sim in itertools.product(scenario_vec, range(n_sim))
    )
