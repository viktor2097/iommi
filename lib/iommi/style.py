from tri_declarative import (
    Namespace,
    RefinableObject,
)


# TODO: This system is extremely powerful. It can overwrite anything and everything. It should probably only be applicable to some specifically "stylable" parts.

def class_names_for(obj):
    from iommi import PagePart  # avoid circular import

    for cls in reversed(obj.__class__.mro()):
        if cls in (object, PagePart, RefinableObject):
            continue
        yield cls.__name__.rpartition('.')[-1]  # this converts iommi.form.Form to just Form


def recursive_namespace(d):
    if isinstance(d, dict):
        return Namespace({k: recursive_namespace(v) for k, v in d.items()})
    else:
        return d


class Style:
    def __init__(self, *bases, **kwargs):
        self.config = Namespace(*[x.config for x in bases], recursive_namespace(kwargs))

    def component(self, obj):
        result = Namespace()
        for class_name in class_names_for(obj):
            if class_name in self.config:
                config = Namespace(self.config.get(class_name, {}))
                shortcuts_config = Namespace(config.pop('shortcuts', {}))
                result.update(config)

                for shortcut_name in reversed(getattr(obj, '__tri_declarative_shortcut_stack', [])):
                    result = Namespace(result, shortcuts_config.get(shortcut_name, {}))
        return result


base = Style(
    Form=dict(
        template='iommi/form/form.html',
        actions_template='iommi/form/actions.html',
    ),
    Field=dict(
        label_template='iommi/form/label.html',
    ),
    # TODO: this is a bit bonkers
    Query__gui__attrs__id='iommi_query_form',
)


test = Style(
    base,
    Field=dict(
        shortcuts=dict(
            boolean=dict(
                template='iommi/form/bootstrap/row_checkbox.html',
            ),
        ),
        template='iommi/form/bootstrap/row.html',
        errors_template='iommi/form/bootstrap/errors.html',
    ),
)

# TODO: move to tests/settings.py
bootstrap = Style(
    base,
    Field=dict(
        shortcuts=dict(
            boolean=dict(
                input__attrs__class={'form-check-input': True, 'form-control': False},
                attrs__class={'form-check': True},
                label__attrs__class={'form-check-label': True},
                template='iommi/form/bootstrap/row_checkbox.html',
            ),
        ),
        attrs__class={
            'form-group': True,
        },
        input__attrs__class={
            'form-control': True,
        },
        errors__attrs__class={'invalid-feedback': True},
        template='iommi/form/bootstrap/row.html',
        errors_template='iommi/form/bootstrap/errors.html',
    ),
    Action=dict(
        shortcuts=dict(
            button__attrs__class={
                'btn': True,
                'btn-primary': True,
            }
        ),
    ),
    Table=dict(
        attrs__class__table=True,
    ),
    Query__gui__style='bootstrap_horizontal',
)

bootstrap_horizontal = Style(
    bootstrap,
    Field=dict(
        shortcuts=dict(
            boolean__label__attrs__class={
                'col-form-label': True,
            },
        ),
        attrs__class={
            'form-group': False,
            'col-sm-3': True,
            'my-1': True,
        },
        errors__attrs__class={'invalid-feedback': True},
        errors_template='iommi/form/bootstrap/errors.html',
    ),
    Form__attrs__class={
        'align-items-center': True,
    }
)

_styles = {}


def register_style(name, conf):
    assert name not in _styles
    _styles[name] = conf


register_style('base', base)
register_style('test', test)
register_style('bootstrap', bootstrap)
register_style('bootstrap_horizontal', bootstrap_horizontal)


def get_style(name):
    return _styles[name]


def apply_style_recursively(data, obj):
    if isinstance(obj, dict):
        obj.update(**data)
    else:
        for k, v in data.items():
            if isinstance(v, dict):
                apply_style_recursively(v, getattr(obj, k))
            else:
                setattr(obj, k, v)


def get_style_for_object(style, self):
    return get_style(style).component(self)