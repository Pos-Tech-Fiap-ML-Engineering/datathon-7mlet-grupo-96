from bandit_platform.policies.thompson_sampling import ThompsonSamplingPolicy

ARMS = ["cdb_12m", "cdb_24m", "poupanca_programada"]


def _policy(seed=0):
    prior_alpha = {"admin.": 1.0, "unknown": 1.0}
    prior_beta = {"admin.": 3.0, "unknown": 3.0}
    return ThompsonSamplingPolicy(ARMS, prior_alpha, prior_beta, seed=seed)


def test_select_arm_returns_known_arm_and_reason_code():
    policy = _policy()
    arm, reason = policy.select_arm({"job": "admin."})
    assert arm in ARMS
    assert reason == "thompson_sampling_v0"


def test_select_arm_uses_default_prior_for_unseen_segment():
    policy = _policy()
    arm, _ = policy.select_arm({"job": "never-seen"})
    assert arm in ARMS


def test_update_shifts_posterior_toward_rewarded_arm():
    policy = _policy(seed=123)
    context = {"job": "admin."}

    for _ in range(200):
        policy.update("cdb_12m", context, reward=1.0)
        policy.update("cdb_24m", context, reward=0.0)
        policy.update("poupanca_programada", context, reward=0.0)

    counts = {"cdb_12m": 0, "cdb_24m": 0, "poupanca_programada": 0}
    for _ in range(200):
        arm, _ = policy.select_arm(context)
        counts[arm] += 1

    assert counts["cdb_12m"] > counts["cdb_24m"]
    assert counts["cdb_12m"] > counts["poupanca_programada"]


def test_same_seed_is_deterministic():
    policy_a = _policy(seed=7)
    policy_b = _policy(seed=7)
    context = {"job": "admin."}

    picks_a = [policy_a.select_arm(context)[0] for _ in range(20)]
    picks_b = [policy_b.select_arm(context)[0] for _ in range(20)]

    assert picks_a == picks_b
