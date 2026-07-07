from __future__ import annotations

import numpy as np

JOB_CATEGORIES = [
    "admin.", "blue-collar", "entrepreneur", "housemaid", "management",
    "retired", "self-employed", "services", "student", "technician",
    "unemployed", "unknown",
]

POUTCOME_CATEGORIES = ["failure", "nonexistent", "success"]


def segment_key(context: dict) -> str:
    return str(context.get("job", "unknown"))


def featurize(context: dict) -> np.ndarray:
    job_vec = np.zeros(len(JOB_CATEGORIES))
    job = context.get("job")
    if job in JOB_CATEGORIES:
        job_vec[JOB_CATEGORIES.index(job)] = 1.0

    age_vec = np.array([context.get("age", 0) / 100.0])

    poutcome_vec = np.zeros(len(POUTCOME_CATEGORIES))
    poutcome = context.get("poutcome")
    if poutcome in POUTCOME_CATEGORIES:
        poutcome_vec[POUTCOME_CATEGORIES.index(poutcome)] = 1.0

    return np.concatenate([job_vec, age_vec, poutcome_vec])
