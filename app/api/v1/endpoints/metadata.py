from fastapi import APIRouter

from app.schemas.catalog import MetadataListResponse
from app.services.catalog_service import CatalogService


router = APIRouter()
service = CatalogService()


@router.get("/elements", response_model=MetadataListResponse)
def get_elements() -> MetadataListResponse:
    return service.get_elements_metadata()


@router.get("/genders", response_model=MetadataListResponse)
def get_genders() -> MetadataListResponse:
    return service.get_genders_metadata()
