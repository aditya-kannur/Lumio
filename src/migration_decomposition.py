"""Multi-hop migration decomposition with global batched grading."""

from src.constants import KNOWN_VERSIONS
from src.grading import retrieve_and_grade_batch


def get_hop_sequence(from_version, to_version):
    if from_version not in KNOWN_VERSIONS or to_version not in KNOWN_VERSIONS:
        return None

    sorted_versions = sorted(KNOWN_VERSIONS)
    start_idx = sorted_versions.index(from_version)
    end_idx = sorted_versions.index(to_version)

    if start_idx >= end_idx:
        return None

    return list(zip(
        sorted_versions[start_idx:end_idx],
        sorted_versions[start_idx + 1:end_idx + 1],
    ))


def decompose_and_retrieve(from_version, to_version, retrieve_fn):
    """
    Retrieve candidates independently for each migration hop, but send all
    candidates to the grader in one Gemini call per attempt. Thus MAX_RETRIES
    is global to the entire migration request, not per hop.
    """
    hops = get_hop_sequence(from_version, to_version)
    if hops is None:
        return {"status": "not_found"}

    groups = [
        {
            "question": f"What changed migrating from {version_a} to {version_b}?",
            "expected_version": version_b,
            "expected_doc_type": "migration",
            "from_version": version_a,
            "to_version": version_b,
        }
        for version_a, version_b in hops
    ]

    result = retrieve_and_grade_batch(groups, retrieve_fn)
    if result["status"] != "found":
        return result

    return {
        "status": "found",
        "hops": [
            {
                "from": group["from_version"],
                "to": group["to_version"],
                "chunks": group["chunks"],
            }
            for group in result["groups"]
        ],
    }
