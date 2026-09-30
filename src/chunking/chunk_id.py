import hashlib

# They can change if the source documentation changes, the chunking logic changes, ]
# or the chunk boundaries/content change. In that situation, the 
# cache should detect the changed chunks and rebuild the affected Chroma index.

def make_chunk_id(*parts):
    """
    Create a stable persistent ID from the chunk's logical identity.

    The ID should remain stable when the chunk text changes,
    as long as the chunk still represents the same logical section.
    """
    identity = "|".join(
        str(part).strip()
        for part in parts
    )

    return hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()[:16]