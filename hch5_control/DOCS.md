# HCH5 Control

Lokal styring af et Dantherm HCH5, med WebUI i Home Assistant. Appen kører
controlleren fra
[Silkjaer/dantherm-control](https://github.com/Silkjaer/dantherm-control),
som bygger på [MRDonnii/dantherm-control](https://github.com/MRDonnii/dantherm-control).

| Anlæg | Forbindelse |
|---|---|
| **HCH5 MK1** (med eller uden HAC1) | RS485-bussen via en RS485-til-Ethernet-adapter i transparent TCP-tilstand (fx Waveshare, 19200 8E1) eller en USB-RS485-adapter i Home Assistant-maskinen |
| **HCH5 MKII** | Anlæggets egen Modbus, over TCP (port 502) eller RTU via USB |

> Uofficielt community-projekt. Ikke udviklet, godkendt eller supporteret af
> Dantherm. Ændringer af anlæggets styring sker på eget ansvar. Behold HCP4
> (MK1), så anlægget kan føres tilbage.

## Sådan virker det

WebUI'en åbner i Home Assistant via *Åbn web-UI* eller **Ventilation** i
sidemenuen. Du er logget ind som WebUI'ens administrator, fordi Home Assistant
allerede har logget dig ind; panelet vises kun for Home Assistant-administratorer.
Port 8088 bruges af Home Assistant-integrationens controller-API; dér kræver
WebUI'en stadig sit eget login.

Controlleren har sin egen sikkerhed: på et MK1 overtager den kun bussen, når
HCP4 har været stille i 10 sekunder, og trækker sig, så snart HCP4 skriver
igen. Den finder selv ud af, om der er en HAC1, og sender kun verificerede
kommandoer. For aktiv styring af et MK1 skal HCP4 være koblet fra RS485-ledningen.

## Indstillinger

| Indstilling | Betydning |
|---|---|
| `unit` | `mk1` eller `mk2` |
| `connection` | `tcp` (netværk) eller `serial` (USB-adapter i Home Assistant-maskinen) |
| `adapter_host`, `adapter_port` | Ved `tcp`: RS485-adapterens IP og port (MK1, ofte 4196) eller anlæggets IP (MKII, port 502). Tom port vælger standarden |
| `serial_device` | Ved `serial`: USB-RS485-adapteren |
| `mk2_unit_id` | MKII's Modbus-adresse, standard 1 |
| `read_only` | Kun læsning, til at prøve appen ved siden af en anden styring. Se nedenfor |
| `controller_token` | Valgfri fast nøgle til Home Assistant-integrationen. Tom: lav den i WebUI'en |
| `log_level` | Logniveau, standard `info` |

**`read_only`** findes kun for et MK1 bag en TCP-adapter. Så sidder en lille
"bus guard" mellem controlleren og adapteren og sender intet videre; alt, den
afviser, logges i `state/bus-guard.log`. Controlleren viser data og sine
beslutninger, men styrer ikke. Med USB eller MKII afviser appen `read_only`.

## Kun én controller ad gangen

En RS485-til-Ethernet-adapter sender ikke det, den selv udsender på bussen,
videre til andre TCP-klienter. To controllere gennem samme adapter kan derfor
**ikke se hinanden**, og begge vil tro, de er master. Stop altid andre
controllere, før denne app styrer, eller kør den med `read_only`.

## Data og backup

Al tilstand ligger i appens config-mappe, `addon_configs/<id>_hch5_control/state`
(via Samba eller SSH), og kommer med i Home Assistants backups: indstillinger,
rum og indregulering, brugere, historik og logs.

**Flyt fra en anden installation:** læg filerne fra den gamle
`/var/lib/dantherm-hch5-ha` (eller `docker/data`) i mappen
`share/hch5_control_import` og start (eller genstart) appen. Den flytter dem ind
i `state` og omdøber importmappen til `hch5_control_import.done-<tidspunkt>`,
så det kun sker én gang. Du kan også kopiere direkte ind i `state`, hvis du kan
se `addon_configs`.

## Home Assistant-integrationen

Brug [dantherm-control-ha](https://github.com/Silkjaer/dantherm-control-ha):

- **Data:** sæt en værtsport for `4196/tcp` i appens netværksindstillinger, og
  peg integrationens "RS485 over TCP" på Home Assistants IP og den port. Spejlet
  gentager controllerens læsninger med spørgsmål og svar, som integrationen ikke
  kan se direkte fra adapteren, når controlleren er master.
- **Styring:** slå "Connect to the controller API" til med Home Assistants IP,
  port 8088 og nøglen fra WebUI'en (*Home Assistant → Forbindelse fra Home
  Assistant*) eller `controller_token`.

## Tilbage til HCP4

Stop appen (eller slå `read_only` til) og sæt HCP4 i igen.
Anlægget beholder de sidste ventilator- og bypassværdier, indtil HCP4 skriver.
