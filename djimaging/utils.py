import hashlib


def dict_to_hash(key):
    """
	Given a dictionary `key`, returns a hash string
    """
    hashed = hashlib.md5()
    for k, v in sorted(key.items()):
        hashed.update(str(k).encode())
        hashed.update(str(v).encode())
    return hashed.hexdigest()
