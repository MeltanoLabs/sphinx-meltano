{% import 'plugin.macros.j2' as macros -%}

.. role:: raw-html(raw)
   :format: html

{{ docs.label }}
{{ "=" * docs.label|length }}

``{{ docs.name }}`` from ``{{ docs.variant }}``

:raw-html:`<hr>`


{% set title = "Description" + (' :raw-html:`<a title="' + docs.description.tooltip + '"><small>` :octicon:`info` :raw-html:`</small></a>`' if docs.description.tooltip else "") %}
{{ title }}
{{ "-" * title|length }}

{% if docs.description.value %}
.. raw:: html

   {% filter indent(width=3, first=True) %}
   {{ md2html(docs.description.value) }}
   {% endfilter %}

{% endif %}

{% if docs.settings %}
Settings
--------

{{ macros.render_settings_card_carousel(docs) }}


{% if docs.environment_setting_values %}
Configured Setting Values per Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. tab-set::

{% for env_setting_values in docs.environment_setting_values %}
   .. tab-item:: {{ env_setting_values.environment }}

      .. table::
         :width: 100%
         :widths: 4 32 32 32

         {% filter indent(width=9) %}
         {{ env_setting_values.as_table() }}
         {% endfilter %}

{% endfor %}
{% endif %}
{% endif %}


{% if docs.capabilities %}
Capabilities
------------

Plugins can advertise 'capabilities' as part of their definition, which define what common actions the plugin supports (e.g. ``discover`` to generate a Singer ``catalog.json file``). This plugin has the following capabilities:

{{ macros.render_capability_card_carousel(docs.capabilities) }}

You can `override these capabilities or specify additional ones <https://docs.meltano.com/guide/configuration#overriding-discoverable-plugin-properties>`_ in your ``meltano.yml`` by adding the ``capabilities`` key.
{% endif %}
