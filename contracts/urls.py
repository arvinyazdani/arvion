from django.urls import path

from .views import contract_accept, contract_access, contract_document, contract_request_otp, contract_settings, contract_verify_otp, proposal_clauses, proposal_create, proposal_delete, proposal_detail, proposal_edit, proposal_list, proposal_preview, proposal_publish, proposal_revoke, public_contract

urlpatterns = [
    path("manage/", proposal_list, name="proposal_list"),
    path("manage/settings/", contract_settings, name="contract_settings"),
    path("manage/new/", proposal_create, name="proposal_create"),
    path("manage/<int:proposal_id>/", proposal_detail, name="proposal_detail"),
    path("manage/<int:proposal_id>/edit/", proposal_edit, name="proposal_edit"),
    path("manage/<int:proposal_id>/preview/", proposal_preview, name="proposal_preview"),
    path("manage/<int:proposal_id>/revoke/", proposal_revoke, name="proposal_revoke"),
    path("manage/<int:proposal_id>/delete/", proposal_delete, name="proposal_delete"),
    path("manage/<int:proposal_id>/clauses/", proposal_clauses, name="proposal_clauses"),
    path("manage/<int:proposal_id>/publish/", proposal_publish, name="proposal_publish"),
    path("<str:token>/", public_contract, name="public_contract"),
    path("<str:token>/document/", contract_document, name="contract_document"),
    path("<str:token>/access/", contract_access, name="contract_access"),
    path("<str:token>/accept/", contract_accept, name="contract_accept"),
    path("<str:token>/accept/request-code/", contract_request_otp, name="contract_request_otp"),
    path("<str:token>/accept/verify/", contract_verify_otp, name="contract_verify_otp"),
]
