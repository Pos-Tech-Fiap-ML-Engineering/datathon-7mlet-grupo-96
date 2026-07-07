from bandit_platform.policies.features import (
    JOB_CATEGORIES,
    POUTCOME_CATEGORIES,
    featurize,
    segment_key,
)


def test_segment_key_uses_job():
    assert segment_key({"job": "admin.", "age": 40}) == "admin."


def test_featurize_has_16_dimensions():
    context = {"job": "admin.", "age": 40, "poutcome": "nonexistent"}
    x = featurize(context)
    assert x.shape == (16,)


def test_featurize_one_hot_job_is_exclusive():
    context = {"job": JOB_CATEGORIES[2], "age": 30, "poutcome": "failure"}
    x = featurize(context)
    job_slice = x[: len(JOB_CATEGORIES)]
    assert job_slice.sum() == 1.0
    assert job_slice[2] == 1.0


def test_featurize_one_hot_poutcome_is_exclusive():
    context = {"job": JOB_CATEGORIES[0], "age": 30, "poutcome": "success"}
    x = featurize(context)
    poutcome_slice = x[len(JOB_CATEGORIES) + 1 :]
    assert poutcome_slice.sum() == 1.0
    assert poutcome_slice[POUTCOME_CATEGORIES.index("success")] == 1.0


def test_featurize_age_is_normalized():
    context = {"job": JOB_CATEGORIES[0], "age": 50, "poutcome": "failure"}
    x = featurize(context)
    age_value = x[len(JOB_CATEGORIES)]
    assert age_value == 0.5


def test_featurize_unknown_job_falls_back_to_zero_vector_slice():
    context = {"job": "not-a-real-job", "age": 40, "poutcome": "nonexistent"}
    x = featurize(context)
    job_slice = x[: len(JOB_CATEGORIES)]
    assert job_slice.sum() == 0.0
