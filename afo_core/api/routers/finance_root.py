# Trinity Score: 90.0 (Established by Chancellor)
from fastapi import APIRouter, Depends, HTTPException
from starlette.requests import Request

from AFO.api.routers.finance import (
    FinanceDashboardResponse,
    JulieService,
    get_finance_dashboard,
    get_julie_service,
)
from AFO.utils.standard_shield import shield

# Separate router without prefix, or specific path
router = APIRouter(tags=["finance_root"])


@router.get("/finance/dashboard")
@shield(pillar="", log_error=True, reraise=False)
async def get_finance_dashboard_root(
    request: Request,
    julie: JulieService = Depends(get_julie_service),
):
    """Alias for /api/finance/dashboard to support root-level access."""
    return await get_finance_dashboard(julie)


from pydantic import BaseModel


class TaxRequest(BaseModel):
    income: float
    filing_status: str


@router.post("/api/julie/calculate-tax")
@shield(pillar="", log_error=True, reraise=False)
async def calculate_tax(
    request: Request,
    req: TaxRequest,
    julie: JulieService = Depends(get_julie_service),
):
    """Calculate tax scenario for Julie Tax Widget."""
    result = await julie.calculate_tax_scenario(req.income, req.filing_status)
    return result
