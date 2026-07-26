from sqlmodel import Session

from app.models.asset_engine import Asset, AssetType, Product


def effective_asset_module_width(session: Session, asset: Asset) -> int | None:
    """Return the DIN width inherited by an asset.

    Direct asset data has priority, followed by a DIN-compatible product and
    finally the asset type default.
    """
    if asset.module_width is not None:
        return asset.module_width
    if asset.product_id is not None:
        product = session.get(Product, asset.product_id)
        if (
            product is not None
            and product.deleted_at is None
            and product.din_rail_mount
            and product.module_width is not None
        ):
            return product.module_width
    asset_type = session.get(AssetType, asset.asset_type_id)
    if asset_type is not None and asset_type.deleted_at is None:
        return asset_type.module_width
    return None
