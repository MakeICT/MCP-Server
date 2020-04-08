from wtforms.widgets import Select, html_params, HTMLString


def select_multi_checkbox(field, div_class='', **kwargs):
    kwargs.setdefault('type', 'checkbox')
    field_id = kwargs.pop('id', field.id)
    # div_class = kwargs.pop('class', )
    # html = [u'<ul %s>' % html_params(id=field_id, class_=ul_class)]
    html = [u'<div %s>' % html_params(id=field_id, class_=div_class)]
    for value, label, checked in field.iter_choices():
        choice_id = u'%s-%s' % (field_id, value)
        options = dict(kwargs, name=field.name, value=value, id=choice_id)
        if checked:
            options['checked'] = 'checked'
        # html.append(u'<li><input %s /> ' % html_params(**options))
        # html.append(u'<label for="%s">%s</label></li>' % (field_id, label))
        html.append(u'''<div class="form-check-inline col-md-3">
        <label class="form-check-label" for="%s">
            <input class="form-check-input" %s >%s
        </label>
        </div>''' % (field_id, html_params(**options), label))
    # html.append(u'</ul>')
    html.append(u'</div>')
    return HTMLString(u''.join(html))