import logging
import os
from pathlib import Path
import shutil
from django.core import management as django_management

from redbaron import RedBaron
from uml2django import objects

from uml2django.settings import settings
from uml2django.parsers.files.file_reader import file_reader
from uml2django.parsers.files.file_writer import file_writer


def start_django_project():
    # START PROJECT COMMAND
    django_management.call_command(
        'startproject',
        (
            f"{settings.UML2DJANGO_PROJECT_NAME}",
            f"{settings.UML2DJANGO_OUTPUT_PATH}"
        )
    )
    logging.getLogger(__name__).debug("Created Django Project")

    # START APPS
    logging.getLogger(__name__).debug(f"APPS_NAMES: {objects.UML2DJANGO_APPS_NAMES}")
    for app_name in objects.UML2DJANGO_APPS_NAMES:
        app_path = os.path.join(
            f"{settings.UML2DJANGO_OUTPUT_PATH}",
            f"{app_name}"
        )
        Path(app_path).mkdir(
            parents=True, exist_ok=True
        )
        django_management.call_command(
            'startapp',
            (
                f"{app_name}",
                app_path
            )
        )
        os.remove(os.path.join(app_path, "models.py"))
        os.remove(os.path.join(app_path, "views.py"))
        os.remove(os.path.join(app_path, "tests.py"))

    # ADD APPS TO SETTINGS.PY
    django_project_settings_file_path = os.path.join(
        settings.UML2DJANGO_OUTPUT_PATH,
        settings.UML2DJANGO_PROJECT_NAME,
        "settings.py"
    )
    settings_node = None
    settings_node = RedBaron(file_reader(django_project_settings_file_path))
    installed_apps_node = settings_node.find(
        "name", value="INSTALLED_APPS"
    ).parent.value
    installed_apps_names_list = [
        # Add already existing apps in INSTALLED_APPS
        # to array installed_apps_names_list
        str(installed_app.value) for installed_app in installed_apps_node.value
    ]

    installed_apps_names_list.extend(
        # Extend installed apps
        # with third party packages
        # used by project generated
        f"'{app_name}'" for app_name in settings.UML2DJANGO_GENERATE_DJANGO_INSTALLED_APPS_REQUIREMENTS
    )
    installed_apps_names_list.extend(
        # Extend installed apps with apps generated by uml2django
        [
            # embrace each app name with ''
            f"'{app_name}'" for app_name in objects.UML2DJANGO_APPS_NAMES
        ]
    )

    # joins the apps names in a string
    # and set ins the installed app in settins.py
    installed_apps_node.value = ",\n\t".join(installed_apps_names_list) + "\n"

    # write settings.py
    file_writer(django_project_settings_file_path, settings_node.dumps())

    # Add console email backend config
    file_writer(django_project_settings_file_path, "\nEMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'\n",override=False)

    # ADD APPS URLS TO PROJECT URLS.PY
    django_project_urls_file_path = os.path.join(
        settings.UML2DJANGO_OUTPUT_PATH,
        settings.UML2DJANGO_PROJECT_NAME,
        "urls.py"
    )
    urls_node = RedBaron(
        # Read project urls.py file
        # Parse code with RedBaron
        file_reader(django_project_urls_file_path)
    )
    # get all imports in the file
    django_urls_imports_nodes = urls_node.find_all("from_import")
    for import_node in django_urls_imports_nodes:
        # find for the django.urls import node
        # ignore imports with mode than 2 levels deep
        if len(import_node.value) == 2:
            import_full_name = [
                # used to construct import full name
                str(value) for value in import_node.value
            ]
            if ".".join(import_full_name) == "django.urls":
                targets = [
                    # get already imported elements (ex: path)
                    x.value for x in import_node.targets
                ]
                targets.append("include") if "include" not in targets else None
                import_node.targets = ", ".join(targets)

    # get url_patterns_nodes
    url_patterns_nodes = urls_node.find(
        "name", value="urlpatterns").parent.value
    existing_urls = [
        # get already existed url_patterns
        url_pattern_node.dumps() for url_pattern_node in url_patterns_nodes
    ]
    # if settings.UML2DJANGO_GENERATE_REST_APIS and settings.UML2DJANGO_REST_APIS_BROWSABLE:
    #     existing_urls.append(
    #         "path('api-auth/', include('rest_framework.urls'), namespace='rest_framework'))"
    #     )
    # append the include directive for each app_name
    for app_name in objects.UML2DJANGO_APPS_NAMES:
        existing_urls.append(f"path('{app_name}/', include('{app_name}.urls'))")
        

    # Set the urls_patterns nodes value
    # by joining the array
    url_patterns_nodes.value = ",\n\t".join(existing_urls) 

    # write the the modified code to
    # django project urls file
    file_writer(
        file_path=django_project_urls_file_path,
        content=urls_node.dumps()
    )
