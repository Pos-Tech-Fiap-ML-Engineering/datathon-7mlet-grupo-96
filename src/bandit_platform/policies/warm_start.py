from __future__ import annotations

import pandas as pd
import torch
import torch.nn as nn

from bandit_platform.policies.features import featurize


class PropensityModel(nn.Module):
    def __init__(self, n_features: int):
        super().__init__()
        self.linear = nn.Linear(n_features, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(self.linear(x)).squeeze(-1)


def train_propensity_model(
    processed_df: pd.DataFrame,
    epochs: int = 200,
    lr: float = 0.1,
    seed: int = 0,
) -> PropensityModel:
    torch.manual_seed(seed)

    features = [
        featurize({"job": row.job, "age": row.age, "poutcome": row.poutcome})
        for row in processed_df.itertuples()
    ]
    x = torch.tensor(features, dtype=torch.float32)
    y = torch.tensor(processed_df["target"].to_numpy(), dtype=torch.float32)

    model = PropensityModel(n_features=x.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.BCELoss()

    for _ in range(epochs):
        optimizer.zero_grad()
        predictions = model(x)
        loss = loss_fn(predictions, y)
        loss.backward()
        optimizer.step()

    return model


def compute_segment_priors(
    model: PropensityModel,
    processed_df: pd.DataFrame,
    prior_strength: float = 4.0,
) -> tuple[dict[str, float], dict[str, float]]:
    prior_alpha: dict[str, float] = {}
    prior_beta: dict[str, float] = {}

    model.eval()
    with torch.no_grad():
        for job, group in processed_df.groupby("job"):
            rows = group.iloc[[0]]
            feats = featurize(
                {"job": rows.iloc[0].job, "age": rows.iloc[0].age, "poutcome": rows.iloc[0].poutcome}
            )
            p_hat = model(torch.tensor([feats], dtype=torch.float32)).item()
            prior_alpha[job] = p_hat * prior_strength
            prior_beta[job] = (1 - p_hat) * prior_strength

    return prior_alpha, prior_beta
