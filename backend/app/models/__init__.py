"""Import all SQLModel table models so metadata and migrations can discover them."""

from app.models.application_setting import ApplicationSetting
from app.models.asset_engine import (
    Asset,
    AssetCodeCounter,
    AssetLabelLink,
    AssetType,
    Label,
    Location,
    Product,
    Relationship,
)
from app.models.consumption import (
    ConsumptionMeter,
    ConsumptionNote,
    ConsumptionReading,
    ConsumptionSetting,
)
from app.models.document_link import DocumentLink
from app.models.electrical import (
    ElectricalAssetPlacement,
    ElectricalCabinetComponent,
    ElectricalComponent,
    ElectricalDistribution,
    ElectricalDistributionArea,
    ElectricalDistributionSection,
    ElectricalMeterPlacement,
    ElectricalProtectiveDevice,
)
from app.models.electrical_circuit import (
    ElectricalCircuit,
    ElectricalCircuitAssetLink,
)
from app.models.electrical_topology import ElectricalConnection
from app.models.energy import EnergyComponent, EnergyConfiguration
from app.models.home_assistant import (
    HomeAssistantAssetLink,
    HomeAssistantEntitySelection,
    HomeAssistantSelectionSetting,
)
from app.models.immich import ImmichAssetLink
from app.models.integration_setting import IntegrationSetting
from app.models.knowledge import DomainNote, WikiPage
from app.models.network import (
    NetworkAddress,
    NetworkConnection,
    NetworkDevice,
    NetworkInterface,
    NetworkSegment,
)
from app.models.quality import QualityIssue, QualityRun
from app.models.release import (
    AuditEvent,
    DashboardSetting,
    GuidedSetupDraft,
    ServiceWorkload,
)
from app.models.smart_meter import (
    SmartMeterMeasurementEntity,
    SmartMeterMeasurementPoint,
)
from app.models.system_setting import SystemSetting
from app.models.work import WorkItem, WorkItemEvent

__all__ = [
    "ApplicationSetting",
    "AuditEvent",
    "Asset",
    "AssetCodeCounter",
    "AssetLabelLink",
    "AssetType",
    "ElectricalAssetPlacement",
    "ElectricalCabinetComponent",
    "ElectricalComponent",
    "ElectricalDistribution",
    "ElectricalDistributionArea",
    "ElectricalDistributionSection",
    "ElectricalMeterPlacement",
    "ElectricalProtectiveDevice",
    "ElectricalCircuit",
    "ElectricalCircuitAssetLink",
    "ElectricalConnection",
    "EnergyComponent",
    "EnergyConfiguration",
    "ConsumptionMeter",
    "ConsumptionNote",
    "ConsumptionReading",
    "ConsumptionSetting",
    "DocumentLink",
    "DashboardSetting",
    "DomainNote",
    "HomeAssistantAssetLink",
    "HomeAssistantEntitySelection",
    "HomeAssistantSelectionSetting",
    "IntegrationSetting",
    "ImmichAssetLink",
    "Label",
    "NetworkAddress",
    "NetworkConnection",
    "NetworkDevice",
    "NetworkInterface",
    "NetworkSegment",
    "Location",
    "Product",
    "Relationship",
    "QualityIssue",
    "QualityRun",
    "GuidedSetupDraft",
    "ServiceWorkload",
    "SmartMeterMeasurementEntity",
    "SmartMeterMeasurementPoint",
    "SystemSetting",
    "WikiPage",
    "WorkItem",
    "WorkItemEvent",
]
