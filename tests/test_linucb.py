from bandit_platform.policies.features import featurize
from bandit_platform.policies.linucb import LinUCBPolicy

ARMS = ["cdb_12m", "cdb_24m"]
N_FEATURES = featurize({"job": "admin.", "age": 40, "poutcome": "failure"}).shape[0]


def test_select_arm_returns_known_arm_and_reason_code():
    policy = LinUCBPolicy(ARMS, n_features=N_FEATURES, alpha=1.0)
    arm, reason = policy.select_arm({"job": "admin.", "age": 40, "poutcome": "failure"})
    assert arm in ARMS
    assert reason == "linucb_v0"


def test_untried_arms_are_favored_by_uncertainty_bonus():
    policy = LinUCBPolicy(ARMS, n_features=N_FEATURES, alpha=5.0)
    context = {"job": "admin.", "age": 40, "poutcome": "failure"}

    for _ in range(50):
        policy.update("cdb_12m", context, reward=0.0)

    arm, _ = policy.select_arm(context)
    assert arm == "cdb_24m"


def test_learns_to_prefer_rewarding_arm():
    policy = LinUCBPolicy(ARMS, n_features=N_FEATURES, alpha=0.1)
    context = {"job": "admin.", "age": 40, "poutcome": "failure"}

    for _ in range(100):
        policy.update("cdb_12m", context, reward=1.0)
        policy.update("cdb_24m", context, reward=0.0)

    arm, _ = policy.select_arm(context)
    assert arm == "cdb_12m"


def test_same_state_gives_same_pick_no_randomness():
    policy = LinUCBPolicy(ARMS, n_features=N_FEATURES, alpha=1.0)
    context = {"job": "admin.", "age": 40, "poutcome": "failure"}

    pick_a, _ = policy.select_arm(context)
    pick_b, _ = policy.select_arm(context)

    assert pick_a == pick_b
