from django.urls import path

from .views import proposal_clauses, proposal_create, proposal_detail, proposal_list, proposal_publish, public_contract

urlpatterns = [
    path("manage/", proposal_list, name="proposal_list"),
    path("manage/new/", proposal_create, name="proposal_create"),
    path("manage/<int:proposal_id>/", proposal_detail, name="proposal_detail"),
    path("manage/<int:proposal_id>/clauses/", proposal_clauses, name="proposal_clauses"),
    path("manage/<int:proposal_id>/publish/", proposal_publish, name="proposal_publish"),
    path("<str:token>/", public_contract, name="public_contract"),
]
