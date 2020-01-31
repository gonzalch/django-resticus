import re

from django.conf import settings
from django.contrib.admindocs.views import simplify_regex
from django.core.exceptions import FieldDoesNotExist
from django.urls import URLPattern, URLResolver

from . import mixins

root_urlconf = __import__(settings.ROOT_URLCONF, {}, {}, [''])


class SchemaGenerator(object):
    def __init__(self, title=None, description=None, prefix=None, urlconf=None, version=None):

        if not urlconf:
            self.urlconf = root_urlconf
        else:
            self.urlconf = urlconf

        self.prefix = prefix
        self.title = title
        self.description = description
        self.version = version

    def get_model_props(self, view_class):
        model = {}
        fields_dict = {
            'AutoField': {'type': 'integer'},
            'BigAutoField': {'type': 'integer'},
            'BigIntegerField': {'type': 'integer'},
            'BinaryField': {'type': 'bytes'},
            'BooleanField': {'type': 'boolean'},
            'CharField': {'type': 'string'},
            'DateField': {'type': 'string'},
            'DateTimeField': {'type': 'string'},
            'DecimalField': {'type': 'number'},
            'DurationField': {'type': 'integer'},
            'EmailField': {'type': 'string'},
            'FileField': {'type': 'string'},
            'FilePathField': {'type': 'string'},
            'FloatField': {'type': 'number'},
            'ForeignKey': {'type': 'array', 'items': {'type': 'string'}},
            'ImageField': {'type': 'string'},
            'IntegerField': {'type': 'integer'},
            'GenericIPAddressField': {'type': 'string'},
            'ManyToManyField': {'type': 'array', 'items': {'type': 'string'}},
            'NullBooleanField': {'type': 'boolean'},
            'OneToOneField': {'type': 'string'},
            'PositiveIntegerField': {'type': 'integer'},
            'PositiveSmallIntegerField': {'type': 'integer'},
            'SlugField': {'type': 'string'},
            'SmallIntegerField': {'type': 'integer'},
            'TextField': {'type': 'string'},
            'TimeField': {'type': 'string'},
            'URLField': {'type': 'string'},
            'UUIDField': {'type': 'string'},
        }

        if isinstance(view_class.fields, tuple):
            for field in view_class.fields:
                if isinstance(field, str):
                    try:
                        print(field, view_class.model._meta.get_field(
                            field).get_internal_type())
                        name = view_class.model._meta.get_field(field).name
                        field_type = view_class.model._meta.get_field(field).get_internal_type()
                        if fields_dict.get(field_type):
                            # print({name: {'type': fields_dict[field_type]}})
                            # model.update({name:{'type': 'array', 'items': {'type': 'string'}}})
                            model.update({name: fields_dict[field_type]})
                    except FieldDoesNotExist:
                        continue
                elif isinstance(field, tuple):
                    # print('tuple', field)
                    for item in field:
                        if isinstance(item, str):
                            try:
                                name = view_class.model._meta.get_field(item).name
                                field_type = view_class.model._meta.get_field(item).get_internal_type()
                                # print('xxx', name, field_type)
                            except FieldDoesNotExist:
                                continue
                # else:
                #     print('field not string', field, type(field))
        return model

    def list_routes(self, callback, parameters):
        # print('list_routes', callback, parameters)
        '''
        Add http methods and responses to routes
        '''
        functions = ['get', 'post', 'patch', 'delete']
        routes = {}
        summary = ''

        if hasattr(callback, 'view_class'):
            for f in functions:
                if hasattr(callback.view_class, f):
                    routes.update({f: {'summary': '', 'parameters': parameters, 'responses': {'200': {'description': 'success'}}}})

                    if hasattr(callback.view_class, 'model'):
                        attr = getattr(callback.view_class, f)
                        try:
                            tag = name = callback.view_class.model.__name__
                            summary = attr.__doc__.replace('object', name)
                        except AttributeError:
                            name = ''
                            tag = 'default'
                            summary = attr.__doc__

                        if f == 'delete':
                            routes.update(
                                {
                                    f:
                                        {
                                            'tags': [tag],
                                            'summary': attr.__doc__.replace('object', name),
                                            'responses': {
                                                '204': {
                                                'description': 'Deleted'
                                                }
                                            },
                                            'parameters': parameters
                                        }
                                    }
                                )
                        if f == 'post' and mixins.ListModelMixin in callback.view_class.__mro__:
                            routes.update(
                                {
                                    f:
                                        {
                                            'tags': [tag],
                                            'summary': summary,
                                            'parameters': parameters,
                                            'responses': {
                                                '201': {
                                                    'description': 'Created ' + name + ' object',
                                                    'content': {
                                                        'application/json': {
                                                            'schema': {
                                                                'type': 'object',
                                                                'properties': {
                                                                    'data': {
                                                                        'type': 'object',
                                                                        'properties': self.get_model_props(callback.view_class)
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                }
                            )

                        if f == 'patch' and mixins.DetailModelMixin in callback.view_class.__mro__:
                            routes.update(
                                {
                                    f:
                                        {
                                            'tags': [tag],
                                            'summary': summary,
                                            'parameters': parameters,
                                            'responses': {
                                                '200': {
                                                    'description': 'Updated ' + name + ' object',
                                                    'content': {
                                                        'application/json': {
                                                            'schema': {
                                                                'type': 'object',
                                                                'properties': {
                                                                    'data': {
                                                                        'type': 'object',
                                                                        'properties': self.get_model_props(callback.view_class)
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                }
                            )

                        if f == 'get' and mixins.DetailModelMixin in callback.view_class.__mro__:
                            routes.update(
                                {
                                    f:
                                        {
                                            'tags': [tag],
                                            'summary': summary,
                                            'parameters': parameters,
                                            'responses': {
                                                '200': {
                                                    'description': 'A single ' + name + ' object',
                                                    'content': {
                                                        'application/json': {
                                                            'schema': {
                                                                'type': 'object',
                                                                'properties': {
                                                                    'data': {
                                                                        'type': 'object',
                                                                        'properties': self.get_model_props(callback.view_class)
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                }
                            )

                        if f == 'get' and mixins.ListModelMixin in callback.view_class.__mro__:
                            routes.update(
                                {
                                    f:
                                        {
                                            'tags': [tag],
                                            'summary': summary,
                                            'parameters': parameters,
                                            'responses': {
                                                '200': {
                                                    'description': 'A list of ' + name + ' objects',
                                                    'content': {
                                                        'application/json': {
                                                            'schema': {
                                                                'type': 'object',
                                                                'properties': {
                                                                    'data': {
                                                                        'type': 'object',
                                                                        'properties': self.get_model_props(callback.view_class)
                                                                    },
                                                                    'page': {
                                                                        'type': 'integer',
                                                                    },
                                                                    'count': {
                                                                        'type': 'integer',
                                                                    },
                                                                    'pages': {
                                                                        'type': 'integer',
                                                                    },
                                                                    'has_next_page': {
                                                                        'type': 'boolean',
                                                                    },
                                                                    'has_previous_page': {
                                                                        'type': 'boolean',
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                }
                            )
        return routes

    def parse_patterns(self, patterns, paths, prefix):
        '''
        Parse through url resolvers until all url patterns have been added
        '''
        for p in patterns:
            if isinstance(p, URLPattern):
                urlstring = prefix + simplify_regex(str(p.pattern))
                urlstring = re.sub(r'//', r'/', urlstring)
                parameters = []
                params_list = re.findall('<(.*?)>', urlstring, re.DOTALL)
                for param in params_list:
                    parameters.append({'name': param, 'in': 'path', 'description': param,
                                        'required': True, 'type': 'string', 'format': 'string'})

                path_info = self.list_routes(p.callback, parameters)
                path_info.update({'description': 'test'})

                a_list = ('description', 'get', 'post',
                            'patch', 'put', 'delete')

                pi_sorted = dict([(key, path_info[key])
                                    for key in a_list if key in path_info])

                path = {urlstring: pi_sorted}
                paths.update(path)

            elif isinstance(p, URLResolver):
                self.list_urls(p, paths=paths, prefix=prefix)

            elif isinstance(p, list):
                self.parse_patterns(p, paths=paths, prefix=prefix)

    def list_urls(self, urls, paths=None, prefix=None, count=0):
        '''
        Get a list of all urls from the given urlconf and all children
        '''
        if paths is None:
            paths = {}

        if prefix is not None and hasattr(urls, "pattern"):
            prefix = prefix + simplify_regex(str(urls.pattern))
        elif not prefix:
            prefix = ''

        if hasattr(urls, 'urlpatterns'):
            patterns = urls.urlpatterns
            self.parse_patterns(patterns, paths, prefix)

        elif hasattr(urls, 'url_patterns'):
            patterns = urls.url_patterns
            self.parse_patterns(patterns, paths, prefix)

        return paths

    def get_paths(self):
        paths = self.list_urls(self.urlconf, prefix=self.prefix)
        # print(*paths, sep="\n")
        return paths

    def get_info(self):
        # Title and version are required by openapi specification 3.x
        info = {
            'title': self.title or '',
            'version': self.version or ''
        }

        if self.description is not None:
            info['description'] = self.description

        return info

    def get_schema(self, request=None, public=False):
        """
        Generate a OpenAPI schema.
        """
        paths = self.get_paths()
        if not paths:
            return None

        schema = {
            'openapi': '3.0.2',
            'info': self.get_info(),
            'paths': paths,
        }

        return schema
