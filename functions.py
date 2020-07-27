import uuid, html

def get_objects(obj, count=False, **kwargs):
    res = obj.query
    for key, value in kwargs.items():
        res = res.filter(getattr(obj, key) == value)
    if count:
        return res.count()
    else:
        return res.all()


def gen_id(marker, seed):
    return marker + uuid.uuid5(uuid.NAMESPACE_DNS, seed).hex


def remove_plots(obj_response):
    """Remove all plots and data tables."""
    obj_response.html("#plots-container, #plot-list", "")