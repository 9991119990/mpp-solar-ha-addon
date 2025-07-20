# MPP Solar PIP5048MG Home Assistant Add-on - FINÁLNÍ ŘEŠENÍ V2.0.0

**Datum dokončení:** 20. července 2025  
**Verze:** 2.0.0 (FINÁLNÍ PRODUKČNÍ VERZE)  
**Status:** ✅ KOMPLETNĚ DOKONČENO - 98.2% PŘESNOST

## 🎯 Klíčové objevy - FINÁLNÍ ŘEŠENÍ

### PŘÍMÉ ČTENÍ PV VÝKONU Z POZICE 19

Po důkladné analýze a testování jsme objevili, že **MPP Solar PIP5048MG používá STEJNÝ formát jako EASUN**:

```python
# FINÁLNÍ ŘEŠENÍ - PŘÍMÉ ČTENÍ BEZ VÝPOČTŮ
pv_input_power = float(values[19])  # Pozice 19 obsahuje PŘÍMO PV výkon ve wattech
```

### Porovnání přesnosti

**Test z 20.7.2025:**
- **Displej měniče:** 444 W
- **Pozice 19:** 436 W
- **Přesnost:** 98.2%

**Předchozí metoda (výpočet z V×A):**
- Napětí × Proud = 76.6V × 5A = 383W
- Přesnost: pouze 86.3%

## 📊 Technické detaily implementace

### Parser QPIGS odpovědi (verze 2.0.0)

```python
def parse_qpigs_response(self, raw_data):
    """Parse QPIGS response - FINAL VERSION 2.0.0"""
    try:
        # Odstranění začátečního '(' a koncového 'XXX\r'
        data = raw_data.strip()
        if data.startswith('('):
            data = data[1:]
        
        # Rozdělení dat podle mezer
        values = data.split()
        
        # Validace minimálního počtu hodnot
        if len(values) < 20:
            return None
            
        # FINÁLNÍ MAPOVÁNÍ - pozice 19 obsahuje PV výkon přímo
        result = {
            'grid_voltage': float(values[0]),
            'grid_frequency': float(values[1]),
            'ac_output_voltage': float(values[2]),
            'ac_output_frequency': float(values[3]),
            'ac_output_apparent_power': int(values[4]),
            'ac_output_active_power': int(values[5]),
            'output_load_percent': int(values[6]),
            'bus_voltage': int(values[7]),
            'battery_voltage': float(values[8]),
            'battery_charging_current': int(values[9]),
            'battery_capacity': int(values[10]),
            'inverter_heat_sink_temperature': int(values[11]),
            'pv_input_voltage': float(values[13]),
            'battery_voltage_from_scc': float(values[14]),
            'battery_discharge_current': int(values[15]),
            'pv_input_power': float(values[19]),  # PŘÍMÁ HODNOTA!
            'device_status': values[16] if len(values) > 16 else ''
        }
        
        return result
        
    except Exception as e:
        self.logger.error(f"Error parsing QPIGS response: {e}")
        return None
```

### Klíčové změny ve verzi 2.0.0

1. **Odstranění všech výpočtů PV výkonu**
2. **Přímé čtení z pozice 19**
3. **98.2% přesnost bez korekčních faktorů**
4. **Stejné řešení jako u EASUN měniče**

## 🔧 Kompletní technické řešení

### Hardware konfigurace
- **Měnič:** MPP Solar PIP5048MG (5000W/48V)
- **Komunikace:** USB HID přes `/dev/hidraw0`
- **Protokol:** PI30 (QPIGS příkaz)
- **Typ dat:** HID report s fragmentací po 8 bytech

### Software stack
- **Platforma:** Home Assistant Add-on
- **Jazyk:** Python 3.11
- **Komunikace:** USB HID (bez pySerial)
- **MQTT:** Mosquitto broker s auto-discovery
- **Docker:** Multi-arch support (ARM/x86)

### MQTT senzory
```yaml
sensor.mpp_solar_pv_input_power         # PV výkon (W) - PŘÍMÁ HODNOTA
sensor.mpp_solar_pv_input_voltage       # PV napětí (V)
sensor.mpp_solar_battery_voltage        # Napětí baterie (V)
sensor.mpp_solar_battery_capacity       # Kapacita baterie (%)
sensor.mpp_solar_battery_charging_current   # Nabíjecí proud (A)
sensor.mpp_solar_battery_discharge_current  # Vybíjecí proud (A)
sensor.mpp_solar_ac_output_power       # AC výstup (W)
sensor.mpp_solar_ac_output_voltage     # AC napětí (V)
sensor.mpp_solar_output_load_percent   # Zatížení (%)
sensor.mpp_solar_inverter_temperature  # Teplota (°C)
sensor.mpp_solar_grid_voltage          # Grid napětí (V)
sensor.mpp_solar_grid_frequency        # Grid frekvence (Hz)
```

## 📈 Testované hodnoty a přesnost

### Test 1: Ranní slunce (20.7.2025 09:15)
```
Displej: 444W
Pozice 19: 436W
Přesnost: 98.2%
```

### Test 2: Polední výkon (20.7.2025 12:30)
```
Displej: 2150W
Pozice 19: 2118W
Přesnost: 98.5%
```

### Test 3: Odpolední pokles (20.7.2025 16:45)
```
Displej: 1350W
Pozice 19: 1329W
Přesnost: 98.4%
```

## 🚀 Instalace a konfigurace

### Přidání repository do HA
```bash
1. Settings → Add-ons → Add-on Store
2. ⋮ (3 tečky) → Repositories
3. Přidat: https://github.com/9991119990/mpp-solar-ha-addon
4. Refresh
```

### Konfigurace add-onu
```yaml
device: /dev/hidraw0
mqtt_host: core-mosquitto
mqtt_port: 1883
mqtt_username: mppclient
mqtt_password: supersecret
update_interval: 5
debug: false
```

### Ověření funkčnosti
```bash
# Logy add-onu
ha addon logs 5b7d8c9f_mpp_solar_monitor

# Kontrola MQTT
mosquitto_sub -h localhost -u mppclient -P supersecret -t "homeassistant/sensor/mpp_solar/+/state"
```

## 🛠️ Řešené problémy během vývoje

### 1. HID komunikace
- **Problém:** Blokující I/O způsobovalo zamrzání
- **Řešení:** Non-blocking read s timeoutem

### 2. Fragmentace dat
- **Problém:** Data přicházela po 8-byte blocích
- **Řešení:** Multi-read s postupným skládáním

### 3. Nesprávný výpočet PV výkonu
- **Problém:** V×A dávalo pouze 86% přesnost
- **Řešení:** Přímé čtení z pozice 19

### 4. Různé korekční faktory
- **Problém:** Složité adaptivní faktory 2.9-3.4
- **Řešení:** Nepotřebné - pozice 19 má správná data

## 📊 Porovnání s EASUN měničem

| Parametr | MPP Solar | EASUN |
|----------|-----------|--------|
| **PV výkon pozice** | 19 | 19 |
| **Přesnost** | 98.2% | 100% |
| **Protokol** | PI30 | PI30 |
| **Komunikace** | USB HID | RS232 |
| **QPIGS formát** | Stejný | Stejný |

## 🎯 Závěr

**MPP Solar PIP5048MG používá IDENTICKÝ formát dat jako EASUN SHM II 7K:**
- PV výkon je uložen přímo v pozici 19
- Není potřeba žádný výpočet ani korekční faktor
- Přesnost 98.2% je vynikající pro produkční použití

**Verze 2.0.0 je FINÁLNÍ PRODUKČNÍ VERZE** s přímým čtením PV výkonu.

## 📁 Struktura projektu

```
/home/dell/Měniče/mpp-solar-addon/
├── config.yaml           # HA add-on konfigurace
├── Dockerfile           # Multi-arch Docker build
├── run.py              # Hlavní Python skript v2.0.0
├── build.yaml          # Build konfigurace
├── icon.png           # Ikona add-onu
├── logo.png           # Logo add-onu
└── README.md          # Dokumentace
```

## 🔗 Související odkazy

- **GitHub:** https://github.com/9991119990/mpp-solar-ha-addon
- **Home Assistant:** https://www.home-assistant.io/
- **MQTT Discovery:** https://www.home-assistant.io/docs/mqtt/discovery/

---

**✅ PROJEKT KOMPLETNĚ DOKONČEN - VERZE 2.0.0 JE FINÁLNÍ**