
import sys
from xml.dom import minidom
from uml2django import settings
from uml2django import _logger


class DjangoModelField():
    name = None
    field_type = None
    field_options = None
    visibility = None

    def __init__(self, element: minidom.Element = None):
        if not element:
            _logger.debug("An element must be given")
            sys.exit(1)
        self.element = element
        self.set_name_from_element()
        self.fillNameAndFieldType()
        self.visibility = element.attributes.get("visibility")
       

    def __str__(self) -> str:
        return f"{self.name} - {self.field_type}"

    def set_name_from_element(self):
        name_and_field = self.element.attributes.get("name").value
        name_and_field = name_and_field.split(":")

        name = name_and_field[0]
        name = name.split(" ")
        name = "_".join(list(filter(None, name)))
        self.name = name

    def fillNameAndFieldType(self) -> None:
        # If no field type was informed
        # Set as CharField
        name_and_field = self.element.attributes.get("name").value
        name_and_field = name_and_field.split(":")
        if len(name_and_field) == 1:
            self.field_type = "CharField"
            self.field_options = [
                f"max_length={settings.UML2DJANGO_CHAR_FIELD_MAX_LENGTH}"]
        else:
            field = name_and_field[1]
            field = field.split(" ")
            field = "".join(list(filter(None, field)))
            self.field_type = field[:field.find("(")]
            # remove () from field string
            self.field_options = field[field.find(
                "(")+1:field.find(")")].split(",")
            # remove blank spaces
            self.field_options = list(filter(None, self.field_options))

        has_verbose_name = False
        has_help_text = False
        char_field_has_max_length = False
        foreign_key_has_on_delete = False
        # loop through field options and values
        for field_option in self.field_options:
            # if field options is 'verbose_name'
            has_verbose_name = True if field_option.startswith(
                "verbose_name") else False
            # if field options is 'help_text'
            has_help_text = True if field_option.startswith(
                "help_text") else False
            # if field type is char field
            if self.field_type == "CharField":
                # check if have a 'max_length' option
                char_field_has_max_length = True if field_option.startswith(
                    "max_length") else False

            if self.field_type == "ForeignKey":
                foreign_key_has_on_delete = True if field_option.startswith(
                    "on_delete") else False

        if not has_verbose_name:
            verbose_name = " ".join(self.name.split("_"))
            self.field_options.append(f"verbose_name=_('{verbose_name}')")
        if not has_help_text and settings.UML2DJANGO_GENERATE_FIELDS_HELP_TEXT:
            self.field_options.append(
                f"help_text=_('{verbose_name} help text')")

        if not char_field_has_max_length and self.field_type == "CharField":
            self.field_options.append(
                f"max_length={settings.UML2DJANGO_CHAR_FIELD_MAX_LENGTH}")
            # s = field
            # field_options = s[s.find("(")+1:s.find(")")]

        if self.field_type == "ForeignKey" and not foreign_key_has_on_delete:
            self.field_options.append(
                f"on_delete={settings.UML2DJANGO_FOREIGNKEY_ON_DELETE}")
