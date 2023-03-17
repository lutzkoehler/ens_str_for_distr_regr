import os
import pickle

import numpy as np
import pandas as pd


def get_panel_data(
    data_path, dataset_ls, score_vec, nn_vec, n_ens_vec, agg_meths, ens_method
):
    """Creates DataFrame for the list of
    [datasets, NN types, ensemble sizes, agg methods] and one ens_method.

    Parameters
    ----------
    data_path : string
        Path to eval_{dataset}_{ens_method}.pkl files
    dataset_ls : list[string]
        List containing the names of datasets to summarize
    score_vec : list[string]
        List containing the names of scores to summarize
        (e.g. crps, a, w, etc.)
    nn_vec : list[string]
        List containing the NN types to consider ("drn", "bqn")
    n_ens_vec : list[int]
        List containing ensemble sizes to consider
    agg_meths : list[string]
        List containing the aggregation methods to consider (e.g. "lp", "vi")
    ens_method : string
        Ensemble method name

    Returns
    -------
    DataFrame
        Columns: dataset, nn, metric, n_ens, agg, score
    """
    df_plot = pd.DataFrame()
    # For-Loop over scenarios
    for dataset in dataset_ls:
        ### Simulation: Load data ###
        filename = f"eval_{dataset}_{ens_method}.pkl"
        temp_data_path = data_path.replace("dataset", dataset)
        with open(os.path.join(temp_data_path, filename), "rb") as f:
            df_scores = pickle.load(f)

        # Check dataset is simulated or UCI Dataset
        if dataset.startswith("scen"):
            optimal_scores_available = True
        else:
            optimal_scores_available = False

        ### Initialization ###
        # Only scenario
        df_sc = df_scores[df_scores["model"] == dataset]

        ### Calculate quantities ###

        # For-Loop over quantities of interest
        for temp_sr in score_vec:
            # Consider special case CRPSS
            if temp_sr == "crpss":
                temp_out = "crps"
            else:
                temp_out = temp_sr

            # Get optimal score of scenario for CRPSS
            s_opt = 0
            if optimal_scores_available and (temp_sr not in ["a", "w"]):
                s_opt = df_sc[df_sc["type"] == "ref"][temp_out].mean()

            # For-Loop over network variants
            for temp_nn in nn_vec:
                # Only network type
                df_nn = df_sc[df_sc["nn"] == temp_nn]

                # For-Lop over ensemble sizes and aggregation methods
                for i_ens in n_ens_vec:
                    for temp_agg in ["opt", "ens"] + agg_meths:
                        # Skip ensemble for skill
                        if (temp_sr == "crpss") and (temp_agg == "ens"):
                            continue
                        elif (temp_sr == "crpss") and (temp_agg == "opt"):
                            continue
                        elif (temp_sr == "a") and (temp_agg == "opt"):
                            continue
                        elif (temp_sr == "w") and (temp_agg == "opt"):
                            continue

                        # Fill in data frame
                        new_row = {
                            "dataset": dataset,
                            "nn": temp_nn,
                            "metric": temp_sr,
                            "n_ens": i_ens,
                            "agg": temp_agg,
                        }

                        # Reference: Average score of ensemble members
                        s_ref = df_nn[
                            (df_nn["n_rep"] <= i_ens)
                            & (df_nn["type"] == "ind")
                        ][temp_out].mean()

                        # Special case: Average ensemble score
                        if temp_agg == "ens":
                            new_row["score"] = s_ref
                        elif temp_agg == "opt":
                            new_row["score"] = s_opt
                        else:
                            # Read out score
                            new_row["score"] = df_nn[
                                (df_nn["n_ens"] == i_ens)
                                & (df_nn["type"] == temp_agg)
                            ][temp_out].mean()

                            # Special case: CRPSS
                            if temp_sr == "crpss":
                                # Calcuate skill
                                new_row["score"] = (
                                    100
                                    * (s_ref - new_row["score"])
                                    / (s_ref - s_opt)
                                )

                            # Relative weight difference to equal weights in %
                            if temp_sr == "w":
                                new_row["score"] = 100 * (
                                    i_ens * new_row["score"] - 1
                                )

                        df_plot = pd.concat(
                            [
                                df_plot,
                                pd.DataFrame(new_row, index=[0]),
                            ],
                            ignore_index=True,
                        )

    return df_plot


def get_best_result_table(
    data_path, nn_vec, ens_method_ls, agg_meths, dataset_ls, n_ens_vec
):
    """Summarize best score for each (dataset, ens_method).
    Also contains the corresponding agg and n_ens.

    Parameters
    ----------
    data_path : string
        Path to eval_{dataset}_{ens_method}.pkl files
    nn_vec : list[string]
        List containing the NN types to consider ("drn", "bqn")
    ens_method_ls : list[string]
        List containing the names of ensembles to consider (e.g. "rand_init)
    agg_meths : list[string]
        List containing the aggregation methods to consider (e.g. "lp", "vi")
    dataset_ls : list[string]
        List containing the names of datasets to summarize
    n_ens_vec : list[int]
        List containing ensemble sizes to consider

    Returns
    -------
    dict
        First entry contains the results for DRNs, second for BQN
    """
    score_vec = ["crps", "crpss", "me", "lgt", "cov", "a", "w"]

    results = {"drn_results": None, "bqn_results": None}

    for ens_method in ens_method_ls:
        # temp_data_path = os.path.join(data_path, ens_method)
        df = get_panel_data(
            data_path,
            dataset_ls,
            score_vec,
            nn_vec,
            n_ens_vec,
            agg_meths,
            ens_method,
        )

        # Basic filtering
        df = df[df["agg"].isin(agg_meths)]
        df = df[df["metric"] == "crps"]
        df["score"] = df["score"].astype("float")

        for nn in nn_vec:
            if nn == "drn":
                temp_results = results["drn_results"]
            else:
                temp_results = results["bqn_results"]
            df_nn = df[df["nn"] == nn]

            if any(df_nn["score"].isna()):
                break

            # Group by and get idx of best scores
            best_row_idx = list(df_nn.groupby("dataset").score.idxmin())
            # Select best row for each dataset
            best_row = df_nn.loc[best_row_idx]

            data = {
                f"{ens_method}": best_row["score"],
                "dataset": best_row["dataset"],
                f"{ens_method}_agg": best_row["agg"],
                f"{ens_method}_n_ens": best_row["n_ens"],
            }
            df_ens_result = pd.DataFrame(data)

            if temp_results is None:
                temp_results = df_ens_result
                temp_results = temp_results.set_index("dataset")
            else:
                df_ens_result = df_ens_result.set_index("dataset")
                temp_results = temp_results.join(df_ens_result)

            if nn == "drn":
                results["drn_results"] = temp_results  # type: ignore
            else:
                results["bqn_results"] = temp_results  # type: ignore

    return results


def get_skills_table(
    data_path,
    dataset_ls,
    score_vec,
    nn_vec,
    n_ens_vec,
    agg_meths,
    ens_method_ls,
):
    """Creates DataFrame containing the skills for each
    ensemble size in n_ens_vec and for each (ens_method, dataset, nn, agg)

    Parameters
    ----------
    data_path : string
        Path to eval_{dataset}_{ens_method}.pkl files
    dataset_ls : list[string]
        List containing the names of datasets to summarize
    score_vec : list[string]
        List containing the names of scores to summarize
        (e.g. crps, a, w, etc.)
    nn_vec : list[string]
        List containing the NN types to consider ("drn", "bqn")
    n_ens_vec : list[int]
        List containing ensemble sizes to consider
    agg_meths : list[string]
        List containing the aggregation methods to consider (e.g. "lp", "vi")
    ens_method_ls : list[string]
        List containing the names of ensembles to consider (e.g. "rand_init)

    Returns
    -------
    DataFrame
        Contains the skills for each ensemble size
    """
    df_skills = pd.DataFrame()

    for ens_method in ens_method_ls:
        df = get_panel_data(
            data_path,
            dataset_ls,
            score_vec,
            nn_vec,
            n_ens_vec,
            agg_meths,
            ens_method,
        )
        # df = df_results.dropna()

        for dataset in df["dataset"].unique():
            for nn in df["nn"].unique():
                # Filtered for dataset, NN type and ens_method
                df_temp = df[(df["dataset"] == dataset) & (df["nn"] == nn)]

                for agg in agg_meths:
                    # Get skill for agg method
                    # Filtered for dataset, NN type, ens_method and
                    # aggregation method
                    df_temp_agg = df_temp[df_temp["agg"] == agg]
                    skills = df_temp_agg[df_temp_agg["metric"] == "crpss"][
                        "score"
                    ].tolist()

                    dict_skills = {
                        f"skill_{n_ens}": skill
                        for (n_ens, skill) in zip(n_ens_vec, skills)
                    }

                    # Add information to row
                    new_row = {
                        "ens_method": ens_method,
                        "dataset": df_temp_agg["dataset"].iloc[0],
                        "nn": df_temp_agg["nn"].iloc[0],
                        "agg": df_temp_agg["agg"].iloc[0],
                        **dict_skills,
                        "avg_skill": np.mean(skills),
                    }

                    # Append to data frame
                    df_skills = pd.concat(
                        [
                            df_skills,
                            pd.DataFrame(new_row, index=[0]),
                        ],
                        ignore_index=True,
                    )

    return df_skills
