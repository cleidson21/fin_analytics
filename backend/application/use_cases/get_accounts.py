from typing import List
from uuid import UUID

from backend.application.queries.get_accounts import GetAccountsQuery
from backend.application.ports.account_repository import IAccountRepository
from backend.application.ports.institution_repository import IInstitutionRepository
from backend.application.dtos.account_response_dto import AccountResponseDTO
from backend.application.dtos.institution_summary_dto import InstitutionSummaryDTO
from backend.domain.entities.account import Account

class GetAccountsUseCase:
    def __init__(
        self,
        account_repository: IAccountRepository,
        institution_repository: IInstitutionRepository
    ):
        self._account_repo = account_repository
        self._institution_repo = institution_repository

    async def execute(self, query: GetAccountsQuery) -> List[AccountResponseDTO]:
        accounts: List[Account] = await self._account_repo.list(query.user_id, query)
        
        response = []
        for acc in accounts:
            inst_dto = None
            if acc.institution_id:
                # We could optimize this by fetching all institutions at once or joining in the repo, 
                # but for now we fetch individually or rely on a map if we list all.
                # Since institutions are few, we might fetch all first.
                pass
            response.append(
                AccountResponseDTO(
                    id=acc.id,
                    external_id=acc.external_id,
                    provider=acc.provider,
                    name=acc.name,
                    type=acc.type,
                    subtype=acc.subtype,
                    currency_code=acc.currency_code,
                    balance=acc.balance,
                    balance_updated_at=acc.balance_updated_at,
                    is_active=acc.is_active,
                    institution=None # We will populate this below
                )
            )

        # Populate institutions
        institutions = await self._institution_repo.list()
        inst_map = {inst.id: inst for inst in institutions}
        
        for i, acc in enumerate(accounts):
            if acc.institution_id and acc.institution_id in inst_map:
                inst = inst_map[acc.institution_id]
                response[i].institution = InstitutionSummaryDTO(
                    id=inst.id,
                    name=inst.name,
                    code=inst.code,
                    logo_url=inst.logo_url
                )
                
        return response
