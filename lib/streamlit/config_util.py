import toml
from typing import Dict, List

import click

from streamlit.file_util import streamlit_write
from streamlit.config_option import ConfigOption


def server_option_changed(
    old_options: Dict[str, ConfigOption], new_options: Dict[str, ConfigOption]
) -> bool:
    """Return True if and only if an option in the server section differs
    between old_options and new_options."""
    for opt_name in old_options.keys():
        if not opt_name.startswith("server"):
            continue

        old_val = old_options[opt_name].value
        new_val = new_options[opt_name].value
        if old_val != new_val:
            return True

    return False


def generate_config(
    section_descriptions: Dict[str, str],
    config_options: Dict[str, ConfigOption],
    save_to_file: bool = False,
) -> List[str]:
    SKIP_SECTIONS = ("_test",)

    out = []
    out.append(
        _clean(
            """
        # Below are all the sections and options you can have in
        ~/.streamlit/config.toml.
    """
        )
    )

    def append_desc(text):
        if save_to_file:
            out.append(text)
        else:
            out.append(click.style(text, bold=True))

    def append_comment(text):
        if save_to_file:
            out.append(text)
        else:
            out.append(click.style(text))

    def append_section(text):
        if save_to_file:
            out.append(text)
        else:
            out.append(click.style(text, bold=True, fg="green"))

    def append_setting(text):
        if save_to_file:
            out.append(text)
        else:
            out.append(click.style(text, fg="green"))

    def append_newline():
        out.append("")

    for section, section_description in section_descriptions.items():
        if section in SKIP_SECTIONS:
            continue

        append_newline()
        append_section("[%s]" % section)
        append_newline()

        for key, option in config_options.items():
            if option.section != section:
                continue

            if option.visibility == "hidden":
                continue

            if option.is_expired():
                continue

            key = option.key.split(".")[1]
            description_paragraphs = _clean_paragraphs(option.description)

            for i, txt in enumerate(description_paragraphs):
                if i == 0:
                    append_desc("# %s" % txt)
                else:
                    append_comment("# %s" % txt)

            toml_default = toml.dumps({"default": option.default_val})
            toml_default = toml_default[10:].strip()

            if len(toml_default) > 0:
                append_comment("# Default: %s" % toml_default)
            else:
                # Don't say "Default: (unset)" here because this branch applies
                # to complex config settings too.
                pass

            if option.deprecated:
                append_comment("#")
                if not save_to_file:
                    append_comment("# " + click.style("DEPRECATED.", fg="yellow"))
                else:
                    append_comment("# DEPRECATED.")
                append_comment(
                    "# %s" % "\n".join(_clean_paragraphs(option.deprecation_text))
                )
                append_comment(
                    "# This option will be removed on or after %s."
                    % option.expiration_date
                )
                append_comment("#")

            option_is_manually_set = (
                option.where_defined != ConfigOption.DEFAULT_DEFINITION
            )

            if option_is_manually_set:
                append_comment("# The value below was set in %s" % option.where_defined)

            toml_setting = toml.dumps({key: option.value})

            if len(toml_setting) and not option_is_manually_set:
                toml_setting = "#%s" % toml_setting

            if len(toml_setting) == 0:
                toml_setting = "#%s =\n" % key

            append_setting(toml_setting)

    if save_to_file:
        with streamlit_write("config.toml", project=True) as f:
            f.write("\n".join(out))
            click.echo(f"Wrote config file to {f.name}")
    return out


def show_config(
    section_descriptions: Dict[str, str],
    config_options: Dict[str, ConfigOption],
) -> None:
    """Print the given config sections/options to the terminal."""
    out = generate_config(section_descriptions, config_options, save_to_file=False)

    click.echo("\n".join(out))


def _clean(txt):
    """Replace all whitespace with a single space."""
    return " ".join(txt.split()).strip()


def _clean_paragraphs(txt):
    paragraphs = txt.split("\n\n")
    cleaned_paragraphs = [_clean(x) for x in paragraphs]
    return cleaned_paragraphs
