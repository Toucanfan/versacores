def find_first_where(objs, **kwargs):
    for obj in objs:
        matching = True
        for k, v in kwargs.items():
            if not getattr(obj, k) == v:
                matching = False
                break
        if matching:
            return obj
    return None
