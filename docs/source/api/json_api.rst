FIELD_NAME = <string>
INTERFACE_NAME = <string>
INSTANCE_DICT = {}
LOOKUP_DICT = {}
MANAGER_LOOKUP = INTERFACE_NAME | M2M_LOOKUP
M2M_LOOKUP = {
    'model': MANAGER_LOOKUP, 
    'object': LOOKUP_DICT, 
    'field': FIELD_NAME
}

QUERYSET_REQUEST = {
    'action': 'query' | 'count',
    'model': MANAGER_LOOKUP,
    'filters': FILTER_DICT
}

M2M_REQUEST = {
    'action': 'm2m_assign' | 'm2m_add' | 'm2m_remove',
    'model': M2M_LOOKUP,
    'data': [INSTANCE_DICT]
}

GET_REQUEST = {
    'action': 'get' | 'create' | 'get_or_create',
    'model': MANAGER_LOOKUP,
    'kwargs': INSTANCE_DICT
}

'get' and 'create' return INSTANCE_DICT, 'get_or_create' returns {'object': INSTANCE_DICT, 'created': <boolean>}

UPDATE_REQUEST = {
    'action': 'update',
    'model': MANAGER_LOOKUP,
    'filters': FILTER_DICT,
    'kwargs': INSTANCE_DICT
}


