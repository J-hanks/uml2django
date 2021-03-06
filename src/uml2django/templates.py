import os
from uml2django import templates


def getSvelteDaisyTemplate(filename: str):
    template_path = os.path.join(
        os.path.dirname(templates.__file__),
        "cheetah_templates",
        "svelte", "daisy",
        filename,
    )
    return template_path


def getTemplatePath(filename: str, directory="") -> str:
    if not filename.endswith(".tmpl"):
        filename = f"{filename}.tmpl"
    template_path = os.path.join(
        os.path.dirname(templates.__file__),
        "cheetah_templates",
        directory,
        filename,
    )
    return template_path


def getAppTemplatePath(filename: str, directory="") -> str:
    template_path = os.path.join(
        os.path.dirname(templates.__file__),
        "cheetah_templates",
        "app",
        directory,
        filename,
    )
    return template_path


def getViewsTemplatePath(filename: str) -> str:
    return getAppTemplatePath(filename, "views")


PREPARE_DATABASE = getTemplatePath(
    "prepare_database"
)

BASE_MODEL_TEMPLATE_PATH = getAppTemplatePath(
    "BaseModel.tmpl", "models"
)
MODEL_TEMPLATE_PATH = getAppTemplatePath(
    "Model.tmpl", "models"
)
MODEL_CREATE_FORM_TEMPLATE_PATH = getAppTemplatePath(
    "ModelCreateForm.tmpl", "forms"
)
MODEL_UPDATE_FORM_TEMPLATE_PATH = getAppTemplatePath(
    "ModelUpdateForm.tmpl", "forms"
)

REST_API_ROUTER_TEMPLATE_PATH = getAppTemplatePath(
    "router.tmpl", "rest_api"
)
REST_API_MODEL_SERIALIZER_TEMPLATE_PATH = getAppTemplatePath(
    "ModelSerializer.tmpl", "rest_api"
)
REST_API_MODEL_VIEWSET_TEMPLATE_PATH = getAppTemplatePath(
    "ModelViewSet.tmpl", "rest_api"
)
CREATE_VIEW_TEMPLATE_PATH = getViewsTemplatePath("CreateView.tmpl")
DELETE_VIEW_TEMPLATE_PATH = getViewsTemplatePath("DeleteView.tmpl")
DETAIL_VIEW_TEMPLATE_PATH = getViewsTemplatePath("DetailView.tmpl")
LIST_VIEW_TEMPLATE_PATH = getViewsTemplatePath("ListView.tmpl")
UPDATE_VIEW_TEMPLATE_PATH = getViewsTemplatePath("UpdateView.tmpl")

CUSTOM_AUTH_APP_PATH = os.path.join(
    os.path.dirname(templates.__file__),
    "cheetah_templates",
    "custom_auth"
)

SVELTE_CARBON_MODEL_FORM = getTemplatePath("CarbonModelForm.svelte", "svelte")
SVELTE_DAISY_LIB = getSvelteDaisyTemplate("lib")
SVELTE_DAISY_LIB_SIDEBAR = os.path.join(
    SVELTE_DAISY_LIB, "Sidebar.svelte")
SVELTE_DAISY_ROUTES_PATH = getSvelteDaisyTemplate("routes")
SVELTE_DAISY_ROUTES_LIST_PATH = os.path.join(
    SVELTE_DAISY_ROUTES_PATH, "model_list.svelte.tmpl")
