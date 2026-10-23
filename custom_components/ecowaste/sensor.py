"""Capteurs EcoWaste (WIPE)."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import CONF_CLIENT, DOMAIN

CURRENCY_CHF = "CHF"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        EcoWasteTotalWeight(coordinator, entry),
        EcoWasteTotalAmount(coordinator, entry),
        EcoWasteCount(coordinator, entry),
        EcoWasteLast(coordinator, entry),
        EcoWasteLastTimestamp(coordinator, entry),
        EcoWasteAvgWeight(coordinator, entry),
        EcoWasteAvgAmount(coordinator, entry),
        EcoWastePricePerKg(coordinator, entry),
        EcoWasteMonthWeight(coordinator, entry),
        EcoWasteMonthAmount(coordinator, entry),
    ]
    # Un couple poids/coût par carte détectée.
    for label in sorted((coordinator.data or {}).get("cards", {})):
        entities.append(EcoWasteCardWeight(coordinator, entry, label))
        entities.append(EcoWasteCardAmount(coordinator, entry, label))

    async_add_entities(entities)


class _Base(CoordinatorEntity, SensorEntity):
    """Base commune : rattache les capteurs à un même appareil."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"EcoWaste {entry.data[CONF_CLIENT]}",
            manufacturer="OptiWaste SA",
            model="WIPE",
        )

    @property
    def _data(self) -> dict:
        return self.coordinator.data or {}


class EcoWasteTotalWeight(_Base):
    _attr_name = "Poids total"
    _attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:scale"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_total_weight"

    @property
    def native_value(self):
        return self._data.get("total_weight")


class EcoWasteTotalAmount(_Base):
    _attr_name = "Coût total"
    _attr_native_unit_of_measurement = CURRENCY_CHF
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:cash"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_total_amount"

    @property
    def native_value(self):
        return self._data.get("total_amount")


class EcoWasteCount(_Base):
    _attr_name = "Nombre de dépôts"
    _attr_native_unit_of_measurement = "dépôts"
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:trash-can"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_count"

    @property
    def native_value(self):
        return self._data.get("count")


class EcoWasteLast(_Base):
    _attr_name = "Dernière pesée"
    _attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_icon = "mdi:weight-kilogram"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_last"

    @property
    def native_value(self):
        last = self._data.get("last")
        return last.get("weight") if last else None

    @property
    def extra_state_attributes(self):
        last = self._data.get("last")
        if not last:
            return None
        return {
            "timestamp": last.get("timestamp"),
            "amount": last.get("amount"),
            "card": (last.get("card") or {}).get("label"),
            "container": (last.get("container") or {}).get("identifier"),
            "flow_type": (last.get("flowType") or {}).get("name"),
        }


class EcoWasteLastTimestamp(_Base):
    _attr_name = "Dernier dépôt (date)"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_last_timestamp"

    @property
    def native_value(self):
        ts = self._data.get("last_timestamp")
        if not ts:
            return None
        parsed = dt_util.parse_datetime(ts)
        if parsed is None:
            return None
        if parsed.tzinfo is None:  # l'API renvoie une heure locale naïve
            parsed = parsed.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
        return parsed


class EcoWasteAvgWeight(_Base):
    _attr_name = "Poids moyen par dépôt"
    _attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:scale-balance"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_avg_weight"

    @property
    def native_value(self):
        return self._data.get("avg_weight")


class EcoWasteAvgAmount(_Base):
    _attr_name = "Coût moyen par dépôt"
    _attr_native_unit_of_measurement = CURRENCY_CHF
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:cash"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_avg_amount"

    @property
    def native_value(self):
        return self._data.get("avg_amount")


class EcoWastePricePerKg(_Base):
    _attr_name = "Prix moyen au kg"
    _attr_native_unit_of_measurement = "CHF/kg"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:cash-multiple"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_price_per_kg"

    @property
    def native_value(self):
        return self._data.get("price_per_kg")


class EcoWasteMonthWeight(_Base):
    _attr_name = "Poids ce mois-ci"
    _attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:calendar-month"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_month_weight"

    @property
    def native_value(self):
        return self._data.get("month_weight")


class EcoWasteMonthAmount(_Base):
    _attr_name = "Coût ce mois-ci"
    _attr_native_unit_of_measurement = CURRENCY_CHF
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:calendar-month"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_month_amount"

    @property
    def native_value(self):
        return self._data.get("month_amount")

    @property
    def extra_state_attributes(self):
        return {"depots": self._data.get("month_count")}


class _CardBase(_Base):
    def __init__(self, coordinator, entry, label: str) -> None:
        super().__init__(coordinator, entry)
        self._label = label

    def _card(self) -> dict:
        return self._data.get("cards", {}).get(self._label) or {}


class EcoWasteCardWeight(_CardBase):
    _attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:scale"

    def __init__(self, coordinator, entry, label):
        super().__init__(coordinator, entry, label)
        self._attr_name = f"Poids carte {label}"
        self._attr_unique_id = f"{entry.entry_id}_{label}_weight"

    @property
    def native_value(self):
        return self._card().get("weight")


class EcoWasteCardAmount(_CardBase):
    _attr_native_unit_of_measurement = CURRENCY_CHF
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:cash"

    def __init__(self, coordinator, entry, label):
        super().__init__(coordinator, entry, label)
        self._attr_name = f"Coût carte {label}"
        self._attr_unique_id = f"{entry.entry_id}_{label}_amount"

    @property
    def native_value(self):
        return self._card().get("amount")
