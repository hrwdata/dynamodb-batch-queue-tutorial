try:
    import torch
    from torch import nn
except ImportError as exc:
    raise RuntimeError(
        "This optional extension requires torch. Install it with "
        "'pip install -r requirements-ml.txt'."
    ) from exc

from queue_analysis import feature_vector, scale_job_runtimes, simulate_batch
from sample_jobs import BATCH_END, BATCH_START, available_batch_dates, get_sample_job_requests


class WaitForecastRegressor(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
        )

    def forward(self, values):
        return self.network(values)


def build_training_examples(batch_dates):
    features = []
    targets = []

    for batch_date in batch_dates:
        jobs = get_sample_job_requests(batch_date=batch_date)
        for workers in (2, 3, 4):
            for runtime_scale in (0.9, 1.0, 1.15):
                scaled_jobs = scale_job_runtimes(jobs, runtime_scale)
                simulation = simulate_batch(
                    scaled_jobs,
                    workers=workers,
                    batch_start=BATCH_START,
                    batch_end=BATCH_END,
                )
                features.append(feature_vector(scaled_jobs) + [workers / 4.0, runtime_scale / 1.2])
                targets.append([simulation["average_wait_minutes"] / 60.0])

    return (
        torch.tensor(features, dtype=torch.float32),
        torch.tensor(targets, dtype=torch.float32),
    )


def train_model(x_train, y_train):
    model = WaitForecastRegressor(x_train.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.MSELoss()

    for epoch in range(300):
        predictions = model(x_train)
        loss = criterion(predictions, y_train)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 100 == 0:
            print(f"Epoch {epoch + 1:3d} | train_loss={loss.item():.4f}")

    return model


def main():
    batch_dates = available_batch_dates()
    holdout_date = batch_dates[-1]
    training_dates = batch_dates[:-1]

    print("Optional PyTorch extension")
    print("This script is not part of the core tutorial.")
    print(
        "It trains a small regressor on synthetic historical scenarios to forecast "
        "average wait for a future batch night."
    )
    print()

    x_train, y_train = build_training_examples(training_dates)
    model = train_model(x_train, y_train)

    holdout_jobs = get_sample_job_requests(batch_date=holdout_date)
    actual = simulate_batch(
        holdout_jobs, workers=2, batch_start=BATCH_START, batch_end=BATCH_END
    )
    holdout_features = torch.tensor(
        [feature_vector(holdout_jobs) + [2 / 4.0, 1.0 / 1.2]], dtype=torch.float32
    )

    with torch.no_grad():
        predicted = model(holdout_features)[0, 0].item() * 60.0

    print(f"holdout_batch_date={holdout_date}")
    print(f"predicted_average_wait_minutes={predicted:.2f}")
    print(f"actual_average_wait_minutes={actual['average_wait_minutes']:.2f}")
    print(f"actual_overflow_risk={actual['overflow_risk']:.2%}")
    print()
    print(
        "This toy forecast uses a tiny synthetic training set, so large holdout "
        "error is expected. In practice, you would train on real nightly history "
        "before trusting an ML forecast."
    )
    print()
    print(
        "Use this path only when first-principles queueing assumptions stop being "
        "credible, for example when runtime varies sharply by workload class or "
        "arrival pressure depends on many correlated upstream signals."
    )


if __name__ == "__main__":
    main()
