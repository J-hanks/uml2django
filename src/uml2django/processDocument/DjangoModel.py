import os
import sys
import json
from xml.dom import minidom
from pathlib import Path

from Cheetah.Template import Template
from redbaron import RedBaron
import inflect


from uml2django import templates
from uml2django import settings
from uml2django.XmiArgoUmlTagsNames import (
    XMI_ARGO_ATTRIBUTE_TAG_NAME,
    XMI_ARGO_CLASS_ABSTRACT_ATTRIBUTE,
    XMI_ARGO_CLASS_TAG_NAME
)
from uml2django.logger import _logger
from uml2django.processDocument import add_import_to_init_file
from uml2django.processDocument.is_element_abstract import is_element_abstract

from uml2django.processDocument.DjangoModelField import DjangoModelField


class DjangoModel():
    element = None
    xmi_id = None
    app_name = str()
    name = str()
    base_fathers = []
    fields = list()
    views_path = str()
    urls_paths = []
    is_abstract = False
    

    actions = [
        'create', 'delete', 'detail',
        'list', 'update',
    ]

    def __init__(self, element: minidom.Element = None):
        if not element:
            _logger.debug(
                "An element must be given to construct DjangoModel object"
            )
            sys.exit(1)
        self.element = element
        self.setNamesFromElement()
        self.app_name = element.attributes.get("namespace").value
        self.xmi_id = element.attributes.get("xmi.id").value
        self.is_abstract = is_element_abstract(self.element)
        self.setFieldsFromElement()
        self.setPaths()
        self.urls_paths = []
        self.base_fathers = []
    
    def __str__(self) -> str:
        return self.name
            
    def add_base_father(self, django_model):
        self.base_fathers.append(django_model)
        _logger.debug(f"{str(self)} fathers: {[str(father) for father in self.base_fathers]}")
        
    def generate_model_forms(self):
        Path(self.model_forms_path).mkdir(parents=True, exist_ok=True)
        for action in ["create", "update"]:
            form_class_name = f"{self.name}{action.capitalize()}Form"
            model_form_template = None
            if action == "create":
                model_form_template = Template(
                    file=templates.MODEL_CREATE_FORM_TEMPLATE_PATH
                )
            elif action == "update":
                model_form_template = Template(
                    file=templates.MODEL_UPDATE_FORM_TEMPLATE_PATH
                )
            model_form_template.model = self
            model_form_file_path = os.path.join(
                self.model_forms_path, f"{form_class_name}.py"
            )
            # write model form file
            with open(model_form_file_path, "w") as text_file:
                text_file.write(str(model_form_template))
                text_file.close()
            # add import to model forms __init__.py file
            add_import_to_init_file(
                self.model_forms_init_path,
                f"from .{form_class_name} import {form_class_name}\n"
            )
            # add import to app forms __init__.py file
            add_import_to_init_file(
                self.app_forms_init_path,
                f"from .{self.name_lower} import {form_class_name}\n"
            )

    def generate_templates(self):
        Path(self.model_templates_path).mkdir(parents=True, exist_ok=True)
        for action in self.actions:
            t = Template(
                file=templates.getTemplatePath(
                    directory="templates",
                    filename=f"template_{action}.tmpl"
                )
            )
            t.settings = settings
            t.model = self
            template_file_path = os.path.join(
                self.model_templates_path, f"{self.name_lower}_{action}.html"
            )
            with open(template_file_path, "w") as template_file:
                template_file.write(str(t))
                template_file.close()

    def generate_class_based_views(self):
        # Create model views directory
        Path(self.model_views_path).mkdir(parents=True, exist_ok=True)
        # loop through the actions
        for view_name in self.actions:
            cap_view_name = view_name.capitalize()
            # generate view from template for each action
            t = Template(
                file=templates.getTemplatePath(
                    directory="views",
                    filename=f"{cap_view_name}View.tmpl"
                )
            )
            t.model = self

            view_file_path = os.path.join(
                self.model_views_path, f"{self.name}{cap_view_name}View.py"
            )
            with open(view_file_path, "w") as view_file:
                view_file.write(str(t))
                view_file.close()

            # add import to __init__.py inside model views path
            add_import_to_init_file(
                self.model_views_init_file_path,
                f"from .{self.name}{cap_view_name}View import {self.name}{cap_view_name}View\n"
            )
            # add import to __init__.py inside app views path
            add_import_to_init_file(
                self.app_views_init_file_path,
                f"from .{self.name_lower} import {self.name}{cap_view_name}View\n"
            )

        # Generate tests
        Path(self.model_tests_path).mkdir(parents=True, exist_ok=True)
        model_views_test_template = Template(
            file=templates.getTemplatePath(
                directory="tests",
                filename=f"ModelViewsTest.tmpl"
            )
        )
        model_views_test_template.model = self
        model_views_test_template.actions = self.actions
        model_views_test_file_path = os.path.join(
            self.model_tests_path, f"{self.name}ViewsTest.py"
        )
        # Write python test file from template
        with open(model_views_test_file_path, "w") as test_file:
            test_file.write(str(model_views_test_template))
            test_file.close()
        # add import to model tests __init__.py
        add_import_to_init_file(
            self.model_tests_init_file_path,
            f"from .{self.name}ViewsTest import {self.name}ViewsTest\n"
        )
        # add import to app tests __init__.py
        add_import_to_init_file(
            self.app_tests_init_file_path,
            f"from .{self.name_lower} import {self.name}ViewsTest\n"
        )

    def generate_cbv_urls_routing(self):
        if not os.path.exists(self.app_path):
            # create app path if not exists
            Path(self.app_path).mkdir(parents=True, exist_ok=True)

        for view_name in self.actions:
            cap_view_name = view_name.capitalize()
            # append view path to self.urls_paths list
            # update and delete view
            if view_name in ("update", "delete"):
                self.urls_paths.append((
                    f"{self.name}/<int:pk>/{view_name}",
                    f"{self.name}{cap_view_name}View",
                    f"{self.name_lower}-{view_name}"
                ))
            elif view_name == "detail":
                self.urls_paths.append((
                    f"{self.name}/<int:pk>",
                    f"{self.name}{cap_view_name}View",
                    f"{self.name_lower}-{view_name}"
                ))
            else:
                # delete and list view comes here
                self.urls_paths.append((
                    f"{self.name}/{view_name}",
                    f"{self.name}{cap_view_name}View",
                    f"{self.name_lower}-{view_name}"
                ))

        existing_url_patterns = []
        if os.path.exists(self.app_urls_file_path):
            with open(self.app_urls_file_path, "r") as source:
                urls_node = RedBaron(source.read())
                existing_url_patterns_nodes = urls_node.find("name", value="urlpatterns").parent.value
                for existing_url_pattern in existing_url_patterns_nodes:
                    urls_arary = str(existing_url_pattern)[5:-1].replace("\"","").split(",")
                    urls_arary[1] = urls_arary[1].replace(".as_view()", "")
                    urls_arary[1] = urls_arary[1].replace(" ", "")
                    urls_arary[2] = urls_arary[2].replace("name=", "")
                    existing_url_patterns.append(urls_arary)
        
        extended_urls_paths = []
        extended_urls_paths = self.urls_paths + existing_url_patterns
        app_urls_template = Template(
            file=templates.getTemplatePath(
                filename="urls.tmpl"
            )
        )
        app_urls_template.urls_paths = extended_urls_paths
        app_urls_template.app_name = self.app_name
        
        with open(self.app_urls_file_path, "w") as app_urls_file:
            app_urls_file.write(str(app_urls_template))
            app_urls_file.close()

    def generate_model_python_file(self):
        django_model_template = Template(file=templates.MODEL_TEMPLATE_PATH)
        django_model_template.model = self
        django_model_template.settings = settings
        Path(self.app_models_path).mkdir(parents=True, exist_ok=True)
        # write model file
        with open(self.model_file_path, "w") as text_file:
            text_file.write(str(django_model_template))
            text_file.close()
        # add import to __init__.py
        add_import_to_init_file(
            self.app_models_init_path,
            f"from .{self.name} import {self.name}\n"
        )

    def setNamesFromElement(self):
        self.name = self.element.attributes.get(
            "name"
        ).value.capitalize()
        self.name_lower = self.name.lower()
        self.name_plural = inflect.engine().plural(self.name)
        return self.name

    def setFieldsFromElement(self):
        attributes_elements = self.element.getElementsByTagName(
            XMI_ARGO_ATTRIBUTE_TAG_NAME
        )
        attributes = list(
            map(
                lambda element: DjangoModelField(element), attributes_elements
            )
        )
        self.fields = attributes

    def setPaths(self):
        # App path
        self.app_path = os.path.join(
            settings.UML2DJANGO_OUTPUT_PATH,
            self.app_name,
        )
        # App urls.py path
        self.app_urls_file_path = os.path.join(
            settings.UML2DJANGO_OUTPUT_PATH,
            "urls.py",
        )
        # app Models  directory path
        self.app_models_path = os.path.join(
            self.app_path,
            "models"
        )
        # Models __init__.py path
        self.app_models_init_path = os.path.join(
            self.app_models_path,
            "__init__.py"
        )
        # Model file path
        self.model_file_path = os.path.join(
            self.app_models_path, f"{self.name}.py"
        )
        # App Forms path
        self.app_forms_path = os.path.join(
            self.app_path,
            "forms",
        )
        # App Forms __init__.py path
        self.app_forms_init_path = os.path.join(
            self.app_forms_path,
            "__init__.py"
        )
        # Model Forms path
        self.model_forms_path = os.path.join(
            self.app_forms_path,
            self.name_lower
        )
        # App Forms __init__.py path
        self.model_forms_init_path = os.path.join(
            self.model_forms_path,
            "__init__.py"
        )
        # App Views path
        # example: some_django_app/views/
        self.app_views_path = os.path.join(
            self.app_path,
            "views",
        )
        # App Views Path
        # example: some_django_app/views/__init__.py
        self.app_views_init_file_path = os.path.join(
            self.app_views_path,
            "__init__.py"
        )
        # Model Views Path
        # example: some_django_app/views/some_model/
        self.model_views_path = os.path.join(
            self.app_views_path,
            self.name_lower,
        )
        # Model Views __init__ Path
        # example: some_django_app/views/some_model/__init__.py
        self.model_views_init_file_path = os.path.join(
            self.model_views_path, "__init__.py"
        )
        # App Templates paths
        # example: some_django_app/templates/
        self.app_templates_path = os.path.join(
            self.app_path,
            "templates",
        )
        # Model templates
        # example: some_django_app/templates/some_model/
        self.model_templates_path = os.path.join(
            self.app_templates_path,
            self.app_name,
        )
        # App tests path
        # example: some_django_app/tests
        self.app_tests_path = os.path.join(
            self.app_path,
            "tests",
        )
        # App tests __init__ file path
        # example: some_django_app/tests
        self.app_tests_init_file_path = os.path.join(
            self.app_tests_path,
            "__init__.py",
        )
        # Model tests path
        # example: some_django_app/tests/some_model
        self.model_tests_path = os.path.join(
            self.app_tests_path,
            self.name_lower,
        )
        # Model tests path
        # example: some_django_app/tests/some_model
        self.model_tests_init_file_path = os.path.join(
            self.model_tests_path,
            "__init__.py",
        )

    def to_json(self):
        return json.dumps(
            self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)
