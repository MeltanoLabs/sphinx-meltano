# sphinx-meltano

Automated documentation of your Meltano project.

## How `sphinx-meltano` works

1. At the `builder-inited` stage of Sphinx execution, `sphinx-meltano` is called.
1. `sphinx-meltano` does the work to evaluate your Meltano project, pulling out plugins and settings into JSON formatted documents readable by the relevant Directives added by the plugin (e.g. the `MeltanoExtractor` directive that renders an extractor plugin).
1. JSON representations of your Meltano objects' docs, together with `.rst` files containing the Meltano directives for reading and rendering those JSON objects, are placed in a `meltano` dir of your docs Source dir and are available to Sphinx as if it were hand-written. You are of course able to hand-write docs using the Meltano directives advertised by `sphinx-meltano`, however allowing the plugin to generate them is far easier! The `meltano` source folder is completely managed by `sphinx-meltano` (deleted and recreated on each run) and should not be checked into source control.
1. After the build stage Sphinx continues as with regular docs, reading and rendering each docs file. This means you can mix regular documentation (including in Markdown with the `MyST` plugin) in addition to the auto-generated docs from `sphinx-meltano`.

In future, the first `build` stage may be replaced with a `parse` stage, consuming a [pre-built manifest from the Meltano CLI](https://github.com/meltano/meltano/issues/6876).
This will improve the performance of `sphinx-meltano` when building docs and also remove direct dependence on the `meltano` python package and its internals for sourcing project information.

## Notes

- [Here](https://github.com/meltano/meltano/blob/main/schema/meltano.schema.json) are the schemas from the relevant objects/plugins.
- [Here](https://docutils.sourceforge.io/docs/howto/rst-directives.html) are some docs on creating directives.
- [Here](https://github.com/docutils/docutils/blob/master/docutils/docutils/parsers/rst/directives/images.py) is an example `image` directive.
- [Here](https://docutils.sourceforge.io/docs/ref/rst/directives.html#tables) are some available directives from Docutils.

More thoughts:

- Use `pydantic` to handle ser/de of json to objects.
- [These](https://github.com/readthedocs/sphinx-autoapi/tree/master/autoapi/templates/python) example templates from `autoapi` show usage of objects in jinja2.
- Use raw html snippets to more closely match the Hub template ([here](https://github.com/meltano/hub/blob/8f9fb6f502a36da7797f4637409ea9ae248eb456/_layouts/meltano_plugin.html))
