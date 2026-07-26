from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.asset_engine import (
    AssetDuplicateWrite,
    AssetRead,
    AssetReplacementRead,
    AssetSeriesRead,
    AssetSeriesWrite,
    AssetReplacementWrite,
    AssetStatus,
    AssetTypeRead,
    AssetTypeWrite,
    AssetWrite,
    LabelRead,
    LabelWrite,
    LocationMoveWrite,
    LocationRead,
    LocationTreeNode,
    LocationType,
    LocationWrite,
    Page,
    ProductImageImportWrite,
    ProductImageSearchRead,
    ProductImageUploadRead,
    ProductRead,
    ProductWrite,
    RelationshipRead,
    RelationshipWrite,
    SortOrder,
)
from app.services.asset_engine import (
    AssetService,
    AssetTypeService,
    CrudService,
    InvalidReferenceError,
    InvalidSortError,
    LabelService,
    LocationService,
    ProductService,
    RelationshipService,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.services.product_images import (
    ProductImageError,
    ProductImageSearchDisabledError,
    ProductImageService,
    ProductImageUnavailableError,
    ProductImageValidationError,
)

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
PageNumber = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]
AssetStatusFilter = Annotated[AssetStatus | None, Query(alias="status")]


def _translate_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ResourceNotFoundError):
        return HTTPException(status_code=404, detail="Resource not found")
    if isinstance(exc, InvalidReferenceError | InvalidSortError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, ResourceConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=500, detail="Unexpected asset engine error")


def _delete(service: CrudService[Any, Any], record_id: UUID) -> Response:
    try:
        service.delete(record_id)
    except (
        ResourceNotFoundError,
        InvalidReferenceError,
        InvalidSortError,
        ResourceConflictError,
    ) as exc:
        raise _translate_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


asset_types = APIRouter(prefix="/asset-types", tags=["asset-types"])


@asset_types.get("", response_model=Page[AssetTypeRead])
def list_asset_types(
    session: SessionDependency,
    page: PageNumber = 1,
    page_size: PageSize = 25,
    search: str | None = None,
    sort_by: str = "name",
    sort_order: SortOrder = SortOrder.ASC,
    include_deleted: bool = False,
) -> Page[AssetTypeRead]:
    service = AssetTypeService(session)
    try:
        result = service.list(
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            include_deleted=include_deleted,
        )
    except InvalidSortError as exc:
        raise _translate_error(exc) from exc
    return Page[AssetTypeRead].model_validate(result)


@asset_types.post("", response_model=AssetTypeRead, status_code=status.HTTP_201_CREATED)
def create_asset_type(payload: AssetTypeWrite, session: SessionDependency) -> AssetTypeRead:
    return AssetTypeRead.model_validate(AssetTypeService(session).create(payload))


@asset_types.get("/{record_id}", response_model=AssetTypeRead)
def get_asset_type(record_id: UUID, session: SessionDependency) -> AssetTypeRead:
    try:
        return AssetTypeRead.model_validate(AssetTypeService(session).get(record_id))
    except ResourceNotFoundError as exc:
        raise _translate_error(exc) from exc


@asset_types.put("/{record_id}", response_model=AssetTypeRead)
def update_asset_type(
    record_id: UUID, payload: AssetTypeWrite, session: SessionDependency
) -> AssetTypeRead:
    try:
        return AssetTypeRead.model_validate(AssetTypeService(session).update(record_id, payload))
    except ResourceNotFoundError as exc:
        raise _translate_error(exc) from exc


@asset_types.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_type(record_id: UUID, session: SessionDependency) -> Response:
    return _delete(AssetTypeService(session), record_id)


products = APIRouter(prefix="/products", tags=["products"])


@products.get("", response_model=Page[ProductRead])
def list_products(
    session: SessionDependency,
    page: PageNumber = 1,
    page_size: PageSize = 25,
    search: str | None = None,
    sort_by: str = "name",
    sort_order: SortOrder = SortOrder.ASC,
    include_deleted: bool = False,
    asset_type_id: UUID | None = None,
    manufacturer: str | None = None,
) -> Page[ProductRead]:
    service = ProductService(session)
    try:
        result = service.list(
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            include_deleted=include_deleted,
            filters={"asset_type_id": asset_type_id, "manufacturer": manufacturer},
        )
    except InvalidSortError as exc:
        raise _translate_error(exc) from exc
    return Page[ProductRead].model_validate(result)


@products.post(
    "/images/upload",
    response_model=ProductImageUploadRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_product_image(
    session: SessionDependency,
    image: UploadFile = File(...),
) -> ProductImageUploadRead:
    try:
        return await ProductImageService(session).upload(image)
    except ProductImageValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@products.get("/images/search", response_model=ProductImageSearchRead)
def search_product_images(
    session: SessionDependency,
    query: str = Query(min_length=2, max_length=200),
    limit: int = Query(default=12, ge=1, le=24),
) -> ProductImageSearchRead:
    try:
        return ProductImageService(session).search_online(query, limit=limit)
    except ProductImageSearchDisabledError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ProductImageValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ProductImageUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@products.post(
    "/images/import",
    response_model=ProductImageUploadRead,
    status_code=status.HTTP_201_CREATED,
)
def import_product_image(
    payload: ProductImageImportWrite,
    session: SessionDependency,
) -> ProductImageUploadRead:
    try:
        return ProductImageService(session).import_online(
            payload.image_url, source_url=payload.source_url
        )
    except ProductImageSearchDisabledError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ProductImageValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ProductImageUnavailableError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@products.get("/images/{reference}", response_class=FileResponse)
def product_image(reference: str, session: SessionDependency) -> FileResponse:
    try:
        path = ProductImageService(session).resolve(reference)
    except ProductImageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(path, headers={"Cache-Control": "private, max-age=86400"})


@products.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductWrite, session: SessionDependency) -> ProductRead:
    try:
        return ProductRead.model_validate(ProductService(session).create(payload))
    except InvalidReferenceError as exc:
        raise _translate_error(exc) from exc


@products.get("/{record_id}", response_model=ProductRead)
def get_product(record_id: UUID, session: SessionDependency) -> ProductRead:
    try:
        return ProductRead.model_validate(ProductService(session).get(record_id))
    except ResourceNotFoundError as exc:
        raise _translate_error(exc) from exc


@products.put("/{record_id}", response_model=ProductRead)
def update_product(
    record_id: UUID, payload: ProductWrite, session: SessionDependency
) -> ProductRead:
    try:
        return ProductRead.model_validate(ProductService(session).update(record_id, payload))
    except (ResourceNotFoundError, InvalidReferenceError, ResourceConflictError) as exc:
        raise _translate_error(exc) from exc


@products.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(record_id: UUID, session: SessionDependency) -> Response:
    return _delete(ProductService(session), record_id)


locations = APIRouter(prefix="/locations", tags=["locations"])


@locations.get("", response_model=Page[LocationRead])
def list_locations(
    session: SessionDependency,
    page: PageNumber = 1,
    page_size: PageSize = 25,
    search: str | None = None,
    sort_by: str = "name",
    sort_order: SortOrder = SortOrder.ASC,
    include_deleted: bool = False,
    parent_id: UUID | None = None,
    location_type: LocationType | None = None,
) -> Page[LocationRead]:
    service = LocationService(session)
    try:
        return service.list_read(
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            include_deleted=include_deleted,
            parent_id=parent_id,
            location_type=location_type,
        )
    except (InvalidSortError, InvalidReferenceError) as exc:
        raise _translate_error(exc) from exc


@locations.get("/tree", response_model=list[LocationTreeNode])
def location_tree(
    session: SessionDependency,
    include_deleted: bool = False,
) -> list[LocationTreeNode]:
    try:
        return LocationService(session).tree_read(include_deleted=include_deleted)
    except InvalidReferenceError as exc:
        raise _translate_error(exc) from exc


@locations.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED)
def create_location(payload: LocationWrite, session: SessionDependency) -> LocationRead:
    try:
        return LocationService(session).create(payload)
    except (InvalidReferenceError, ResourceConflictError) as exc:
        raise _translate_error(exc) from exc


@locations.get("/{record_id}", response_model=LocationRead)
def get_location(
    record_id: UUID,
    session: SessionDependency,
    include_deleted: bool = False,
) -> LocationRead:
    try:
        return LocationService(session).get_read(record_id, include_deleted=include_deleted)
    except (ResourceNotFoundError, InvalidReferenceError) as exc:
        raise _translate_error(exc) from exc


@locations.put("/{record_id}", response_model=LocationRead)
def update_location(
    record_id: UUID, payload: LocationWrite, session: SessionDependency
) -> LocationRead:
    try:
        return LocationService(session).update(record_id, payload)
    except (ResourceNotFoundError, InvalidReferenceError, ResourceConflictError) as exc:
        raise _translate_error(exc) from exc


@locations.post("/{record_id}/move", response_model=LocationRead)
def move_location(
    record_id: UUID,
    payload: LocationMoveWrite,
    session: SessionDependency,
) -> LocationRead:
    try:
        return LocationService(session).move(record_id, payload)
    except (ResourceNotFoundError, InvalidReferenceError, ResourceConflictError) as exc:
        raise _translate_error(exc) from exc


@locations.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(record_id: UUID, session: SessionDependency) -> Response:
    return _delete(LocationService(session), record_id)


labels = APIRouter(prefix="/labels", tags=["labels"])


@labels.get("", response_model=Page[LabelRead])
def list_labels(
    session: SessionDependency,
    page: PageNumber = 1,
    page_size: PageSize = 25,
    search: str | None = None,
    sort_by: str = "name",
    sort_order: SortOrder = SortOrder.ASC,
    include_deleted: bool = False,
) -> Page[LabelRead]:
    service = LabelService(session)
    try:
        result = service.list(
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            include_deleted=include_deleted,
        )
    except InvalidSortError as exc:
        raise _translate_error(exc) from exc
    return Page[LabelRead].model_validate(result)


@labels.post("", response_model=LabelRead, status_code=status.HTTP_201_CREATED)
def create_label(payload: LabelWrite, session: SessionDependency) -> LabelRead:
    try:
        return LabelRead.model_validate(LabelService(session).create(payload))
    except ResourceConflictError as exc:
        raise _translate_error(exc) from exc


@labels.get("/{record_id}", response_model=LabelRead)
def get_label(record_id: UUID, session: SessionDependency) -> LabelRead:
    try:
        return LabelRead.model_validate(LabelService(session).get(record_id))
    except ResourceNotFoundError as exc:
        raise _translate_error(exc) from exc


@labels.put("/{record_id}", response_model=LabelRead)
def update_label(record_id: UUID, payload: LabelWrite, session: SessionDependency) -> LabelRead:
    try:
        return LabelRead.model_validate(LabelService(session).update(record_id, payload))
    except (ResourceNotFoundError, ResourceConflictError) as exc:
        raise _translate_error(exc) from exc


@labels.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_label(record_id: UUID, session: SessionDependency) -> Response:
    return _delete(LabelService(session), record_id)


assets = APIRouter(prefix="/assets", tags=["assets"])


@assets.get("", response_model=Page[AssetRead])
def list_assets(
    session: SessionDependency,
    page: PageNumber = 1,
    page_size: PageSize = 25,
    search: str | None = None,
    sort_by: str = "name",
    sort_order: SortOrder = SortOrder.ASC,
    include_deleted: bool = False,
    asset_type_id: UUID | None = None,
    product_id: UUID | None = None,
    location_id: UUID | None = None,
    label_id: UUID | None = None,
    asset_status: AssetStatusFilter = None,
) -> Page[AssetRead]:
    try:
        return AssetService(session).list_read(
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            include_deleted=include_deleted,
            filters={
                "asset_type_id": asset_type_id,
                "product_id": product_id,
                "location_id": location_id,
                "status": asset_status.value if asset_status else None,
            },
            label_id=label_id,
        )
    except InvalidSortError as exc:
        raise _translate_error(exc) from exc


@assets.post("", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_asset(payload: AssetWrite, session: SessionDependency) -> AssetRead:
    try:
        return AssetService(session).create(payload)
    except (InvalidReferenceError, ResourceConflictError) as exc:
        raise _translate_error(exc) from exc


@assets.get("/next-inventory-number", response_model=dict[str, str])
def next_inventory_number(session: SessionDependency) -> dict[str, str]:
    return {"inventory_number": AssetService(session).next_inventory_number()}


@assets.post(
    "/{record_id}/duplicate",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
)
def duplicate_asset(
    record_id: UUID,
    payload: AssetDuplicateWrite,
    session: SessionDependency,
) -> AssetRead:
    try:
        return AssetService(session).duplicate(record_id, payload)
    except (ResourceNotFoundError, InvalidReferenceError, ResourceConflictError) as exc:
        raise _translate_error(exc) from exc


@assets.post(
    "/{record_id}/series",
    response_model=AssetSeriesRead,
    status_code=status.HTTP_201_CREATED,
)
def create_asset_series(
    record_id: UUID,
    payload: AssetSeriesWrite,
    session: SessionDependency,
) -> AssetSeriesRead:
    try:
        return AssetService(session).create_series(record_id, payload)
    except (ResourceNotFoundError, InvalidReferenceError, ResourceConflictError) as exc:
        raise _translate_error(exc) from exc


@assets.get("/{record_id}", response_model=AssetRead)
def get_asset(record_id: UUID, session: SessionDependency) -> AssetRead:
    try:
        return AssetService(session).get_read(record_id)
    except (ResourceNotFoundError, InvalidReferenceError) as exc:
        raise _translate_error(exc) from exc


@assets.put("/{record_id}", response_model=AssetRead)
def update_asset(record_id: UUID, payload: AssetWrite, session: SessionDependency) -> AssetRead:
    try:
        return AssetService(session).update(record_id, payload)
    except (ResourceNotFoundError, InvalidReferenceError, ResourceConflictError) as exc:
        raise _translate_error(exc) from exc


@assets.post(
    "/{record_id}/replacement",
    response_model=AssetReplacementRead,
    status_code=status.HTTP_201_CREATED,
)
def replace_asset(
    record_id: UUID,
    payload: AssetReplacementWrite,
    session: SessionDependency,
) -> AssetReplacementRead:
    try:
        return AssetService(session).replace(record_id, payload.replacement, payload.reason)
    except (ResourceNotFoundError, InvalidReferenceError, ResourceConflictError) as exc:
        raise _translate_error(exc) from exc


@assets.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(record_id: UUID, session: SessionDependency) -> Response:
    return _delete(AssetService(session), record_id)


relationships = APIRouter(prefix="/relationships", tags=["relationships"])


@relationships.get("", response_model=Page[RelationshipRead])
def list_relationships(
    session: SessionDependency,
    page: PageNumber = 1,
    page_size: PageSize = 25,
    search: str | None = None,
    sort_by: str = "relationship_type",
    sort_order: SortOrder = SortOrder.ASC,
    include_deleted: bool = False,
    source_asset_id: UUID | None = None,
    target_asset_id: UUID | None = None,
    relationship_type: str | None = None,
) -> Page[RelationshipRead]:
    service = RelationshipService(session)
    try:
        result = service.list(
            page=page,
            page_size=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            include_deleted=include_deleted,
            filters={
                "source_asset_id": source_asset_id,
                "target_asset_id": target_asset_id,
                "relationship_type": relationship_type,
            },
        )
    except InvalidSortError as exc:
        raise _translate_error(exc) from exc
    return Page[RelationshipRead].model_validate(result)


@relationships.post("", response_model=RelationshipRead, status_code=status.HTTP_201_CREATED)
def create_relationship(payload: RelationshipWrite, session: SessionDependency) -> RelationshipRead:
    try:
        return RelationshipRead.model_validate(RelationshipService(session).create(payload))
    except (InvalidReferenceError, ResourceConflictError) as exc:
        raise _translate_error(exc) from exc


@relationships.get("/{record_id}", response_model=RelationshipRead)
def get_relationship(record_id: UUID, session: SessionDependency) -> RelationshipRead:
    try:
        return RelationshipRead.model_validate(RelationshipService(session).get(record_id))
    except ResourceNotFoundError as exc:
        raise _translate_error(exc) from exc


@relationships.put("/{record_id}", response_model=RelationshipRead)
def update_relationship(
    record_id: UUID, payload: RelationshipWrite, session: SessionDependency
) -> RelationshipRead:
    try:
        return RelationshipRead.model_validate(
            RelationshipService(session).update(record_id, payload)
        )
    except (ResourceNotFoundError, InvalidReferenceError, ResourceConflictError) as exc:
        raise _translate_error(exc) from exc


@relationships.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_relationship(record_id: UUID, session: SessionDependency) -> Response:
    return _delete(RelationshipService(session), record_id)


for resource_router in (assets, products, asset_types, locations, labels, relationships):
    router.include_router(resource_router)
