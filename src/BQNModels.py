import time
from typing import Any

import keras.backend as K
import numpy as np
import scipy.stats as ss
import tensorflow as tf
from nptyping import Float, NDArray
from tensorflow.keras import Model  # type: ignore
from tensorflow.keras.callbacks import EarlyStopping  # type: ignore
from tensorflow.keras.layers import Dense  # type: ignore
from tensorflow.keras.layers import Concatenate, Dropout, Input  # type: ignore
from tensorflow.keras.optimizers import Adam  # type: ignore

from BaseModel import BaseModel
from fn_eval import bern_quants, fn_scores_ens


class BQNBaseModel(BaseModel):
    def __init__(
        self,
        n_ens: int,
        n_cores: int,
        rpy_elements: dict[str, Any],
        dtype: str = "float32",
        q_levels: NDArray[Any, Float] | None = None,
        **kwargs
    ) -> None:
        self.n_ens = n_ens
        self.n_cores = n_cores
        self.rpy_elements = rpy_elements
        self.dtype = dtype
        # If not given use equidistant quantiles (multiple of ensemble
        # coverage, incl. median)
        if q_levels is None:
            step = 1 / 100
            self.q_levels = np.arange(start=1 / 100, stop=1 + step, step=step)
        else:
            self.q_levels = q_levels
        self.hpar = {
            "p_degree": 12,
            "n_q": 99,
            "lr_adam": 5e-4,  # -1 for Adam-default
            "n_epochs": 150,
            "n_patience": 10,
            "n_batch": 64,
            "lay1": 48,
            "actv": "softplus",
            "actv_out": "softplus",
            "nn_verbose": 0,
            "p_dropout": 0.5,
            "p_dropout_input": 0.2,
        }
        self.training = False
        if "training" in kwargs.keys():
            self.training = kwargs["training"]

    def _build(self, input_length: int) -> Model:
        # Calculate equidistant quantile levels for loss function
        self.q_levels_loss = np.arange(
            start=1 / (self.hpar["n_q"] + 1),
            stop=(self.hpar["n_q"] + 1) / (self.hpar["n_q"] + 1),
            step=1 / (self.hpar["n_q"] + 1),
        )

        # Basis of Bernstein polynomials evaluated at quantile levels
        self.B = np.apply_along_axis(
            func1d=ss.binom.pmf,
            arr=np.reshape(
                np.arange(start=0, stop=self.hpar["p_degree"] + 1, step=1),
                newshape=(1, self.hpar["p_degree"] + 1),
            ),
            axis=0,
            p=self.q_levels_loss,
            n=self.hpar["p_degree"],
        )

        # Quantile loss functions (for neural network)
        def qt_loss(y_true, y_pred):
            """Quantile loss for BQN network

            Quantile Loss:
            L(yp_i, y_i) = max[ q(y_i - yp_i), (q - 1)(y_i - yp_i) ]

            Parameters
            ----------
            y_true : array(n x 1)
                True observation to predict
            y_pred : array(n x n_coeff)
                Predicted Bernstein coefficients and increments

            Returns
            -------
            scalar
                Mean quantile loss across all observations
            """
            # Quantiles calculated via basis and increments -> q_shape: (64,99)
            q = K.dot(
                K.cumsum(y_pred, axis=1), K.constant(self.B.T)
            )  # , dtype=np.float64))

            # Calculate individual quantile scores
            err = y_true - q  # err_shape (64,99)
            e1 = err * K.constant(
                value=self.q_levels_loss,
                shape=(1, self.hpar["n_q"]),  # , dtype=np.float64
            )  # e1_shape (64,99)
            e2 = err * K.constant(
                value=self.q_levels_loss - 1,
                shape=(1, self.hpar["n_q"]),  # , dtype=np.float64
            )

            # Find correct values (max) and return mean
            return K.mean(
                K.maximum(e1, e2), axis=1
            )  # max_shape (64,99) - mean_shape (64,)

        # Custom optizimer
        if self.hpar["lr_adam"] == -1:
            custom_opt = "adam"
        else:
            custom_opt = Adam(learning_rate=self.hpar["lr_adam"])

        ### Build network ###
        model = self._get_architecture(
            input_length=input_length, training=self.training
        )

        ### Estimation ###
        # Compile model
        # run_eagerly to help debug (default: False)
        model.compile(optimizer=custom_opt, loss=qt_loss, run_eagerly=False)

        # Return model
        return model

    def fit(
        self,
        X_train: NDArray,
        y_train: NDArray,
        X_valid: NDArray,
        y_valid: NDArray,
    ) -> None:
        ### Data preparation ###
        # Read out set sizes
        self.n_train = X_train.shape[0]
        self.n_valid = X_valid.shape[0]

        # Save center and scale parameters
        self.tr_center = np.mean(X_train, axis=0)
        self.tr_scale = np.std(X_train, axis=0)

        # Scale training data
        X_train = (X_train - self.tr_center) / self.tr_scale

        # Scale validation data with training data attributes
        X_valid = (X_valid - self.tr_center) / self.tr_scale

        ### Build model ###
        self.model = self._build(input_length=X_train.shape[1])

        # Take time
        start_tm = time.time_ns()

        # Fit model
        self.model.fit(
            x=X_train,
            y=y_train,
            epochs=self.hpar["n_epochs"],
            batch_size=self.hpar["n_batch"],
            validation_data=(X_valid, y_valid),
            verbose=self.hpar["nn_verbose"],
            callbacks=EarlyStopping(
                patience=self.hpar["n_patience"],
                restore_best_weights=True,
                monitor="val_loss",
            ),
        )

        # Take time
        end_tm = time.time_ns()

        # Time needed
        self.runtime_est = end_tm - start_tm

    def predict(self, X_test: NDArray) -> None:
        # Scale data for prediction
        self.n_test = X_test.shape[0]
        X_pred = (X_test - self.tr_center) / self.tr_scale

        ### Prediciton ###
        # Take time
        start_tm = time.time_ns()

        # Predict coefficients of Bernstein polynomials
        self.coeff_bern = self.model.predict(X_pred)

        # Take time
        end_tm = time.time_ns()

        # Time needed
        self.runtime_pred = end_tm - start_tm

    def get_results(self, y_test: NDArray) -> dict[str, Any]:
        # Accumulate increments
        coeff_bern = np.cumsum(self.coeff_bern, axis=1)

        ### Evaluation ###
        # Sum up calcuated quantiles (Sum of basis at quantiles times
        # coefficients)
        q = bern_quants(alpha=coeff_bern, q_levels=self.q_levels)
        # Calculate evaluation measres of DRN forecasts
        scores = fn_scores_ens(
            ens=q,
            y=y_test,
            skip_evals=["e_me"],
            scores_ens=True,
            rpy_elements=self.rpy_elements,
        )

        # Transform ranks to n_(ens+1) bins (for multiples of (n_ens+1) exact)
        if q.shape[1] != self.n_ens:
            scores["rank"] = np.ceil(
                scores["rank"] * (self.n_ens + 1) / (q.shape[1] + 1)
            )

        # Calculate bias of mean forecast (formula given)
        scores["e_me"] = np.mean(coeff_bern, axis=1) - y_test

        ### Output ###
        # Output
        return {
            "f": q,
            "alpha": coeff_bern,
            "nn_ls": self.hpar,
            "scores": scores,
            "n_train": self.n_train,
            "n_valid": self.n_valid,
            "n_test": self.n_test,
            "runtime_est": self.runtime_est,
            "runtime_pred": self.runtime_pred,
        }


class BQNRandInitModel(BQNBaseModel):
    def _get_architecture(
        self, input_length: int, training: bool = False
    ) -> Model:
        """Construct and return BQN base model

        Architecture:

        Layer (type)                Output Shape  Param #  Connected to
        ====================================================================
        input (InputLayer)          [(None, 5)]   0        []
        dense_1 (Dense)             (None, 64)    384      ['input[0][0]']
        dense_2 (Dense)             (None, 32)    2080     ['dense_1[0][0]']
        dense_3 (Dense)             (None, 1)     33       ['dense_2[0][0]']
        dense_4 (Dense)             (None, 12)    396      ['dense_2[0][0]']
        concatenate (Concatenate)   (None, 13)    0        ['dense_3[0][0]',
                                                            'dense_4[0][0]']

        Parameters
        ----------
        input_length : int
            Number of predictors
        hpar_ls : dict[str, Any]
            Contains several hyperparameter
        dtype : str
            Should be either float32 or float64

        Returns
        -------
        Model
            _description_
        """
        tf.keras.backend.set_floatx(self.dtype)

        ### Build network ###
        # Input
        input = Input(shape=input_length, name="input", dtype=self.dtype)

        # Hidden layers
        hidden_1 = Dense(
            units=self.hpar["lay1"],
            activation=self.hpar["actv"],
            dtype=self.dtype,
        )(input)
        hidden_2 = Dense(
            units=self.hpar["lay1"] / 2,
            activation=self.hpar["actv"],
            dtype=self.dtype,
        )(hidden_1)

        # Different activation functions for output (alpha_0 and positive
        # increments)
        alpha0_out = Dense(units=1, dtype=self.dtype)(hidden_2)
        alphai_out = Dense(
            units=self.hpar["p_degree"],
            activation="softplus",
            dtype=self.dtype,
        )(hidden_2)

        # Concatenate output
        output = Concatenate()([alpha0_out, alphai_out])

        # Define model
        model = Model(inputs=input, outputs=output)

        # Return model
        return model


class BQNDropoutModel(BQNBaseModel):
    def _get_architecture(
        self, input_length: int, training: bool = False
    ) -> Model:
        """Construct and return BQN base model

        Architecture:

        Layer (type)                Output Shape  Param #  Connected to
        ====================================================================
        input (InputLayer)          [(None, 5)]   0        []
        dense_1 (Dense)             (None, 64)    384      ['input[0][0]']
        dense_2 (Dense)             (None, 32)    2080     ['dense_1[0][0]']
        dense_3 (Dense)             (None, 1)     33       ['dense_2[0][0]']
        dense_4 (Dense)             (None, 12)    396      ['dense_2[0][0]']
        concatenate (Concatenate)   (None, 13)    0        ['dense_3[0][0]',
                                                            'dense_4[0][0]']

        Parameters
        ----------
        input_length : int
            Number of predictors
        hpar_ls : dict[str, Any]
            Contains several hyperparameter
        dtype : str
            Should be either float32 or float64

        Returns
        -------
        Model
            _description_
        """
        tf.keras.backend.set_floatx(self.dtype)

        # Extract params
        p_dropout = self.hpar["p_dropout"]

        ### Build network ###
        # Input
        input = Input(shape=input_length, name="input", dtype=self.dtype)
        # Input dropout
        input_d = Dropout(
            rate=self.hpar["p_dropout_input"], noise_shape=(input_length,)
        )(input, training=training)

        # Hidden layer 1
        n_units_1 = int(self.hpar["lay1"] / (1 - p_dropout))
        hidden_1 = Dense(
            units=n_units_1,
            activation=self.hpar["actv"],
            dtype=self.dtype,
        )(input_d)
        hidden_1_d = Dropout(rate=p_dropout, noise_shape=(n_units_1,))(
            hidden_1, training=training
        )

        # Hidden layer 2
        n_units_2 = int(self.hpar["lay1"] / ((1 - p_dropout) * 2))
        hidden_2 = Dense(
            units=n_units_2,
            activation=self.hpar["actv"],
            dtype=self.dtype,
        )(hidden_1_d)
        hidden_2_d = Dropout(rate=p_dropout, noise_shape=(n_units_2,))(
            hidden_2, training=training
        )

        # Different activation functions for output (alpha_0 and positive
        # increments)
        alpha0_out = Dense(units=1, dtype=self.dtype)(hidden_2_d)
        alphai_out = Dense(
            units=self.hpar["p_degree"],
            activation="softplus",
            dtype=self.dtype,
        )(hidden_2_d)

        # Concatenate output
        output = Concatenate()([alpha0_out, alphai_out])

        # Define model
        model = Model(inputs=input, outputs=output)

        # Return model
        return model
