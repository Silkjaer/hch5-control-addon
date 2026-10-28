# HCH5 Control

Lokal styring af et Dantherm HCH5 MK1 gennem en RS485-til-Ethernet-adapter
(fx Waveshare RS485 TO POE ETH i transparent TCP-tilstand, 19200 8E1).
Appen kører controlleren og WebUI'en fra
[Silkjaer/dantherm-control](https://github.com/Silkjaer/dantherm-control),
som bygger på [MRDonnii/dantherm-control](https://github.com/MRDonnii/dantherm-control).

> Uofficielt community-projekt. Ikke udviklet, godkendt eller supporteret af
> Dantherm. Ændringer af anlæggets styring sker på eget ansvar. Behold HCP4,
> så anlægget kan føres tilbage.

## Sådan virker det

```text
RS485-adapter (adapter_host:adapter_port)
      │
bus guard  ── sender kun det, bus_access tillader; logger alt andet
      │
controller ── WebUI i Home Assistants sidemenu (Ventilation)
                controller-API på port 8088 til integrationen
```

WebUI'en åbner i Home Assistant via *Åbn web-UI* eller **Ventilation** i
sidemenuen. Du er logget ind som WebUI'ens administrator, fordi Home Assistant
allerede har logget dig ind; panelet vises kun for Home Assistant-administratorer.
På port 8088 kræver WebUI'en stadig sit eget login.

Controlleren overtager kun bussen, når HCP4 har været stille i 10 sekunder,
og trækker sig, så snart HCP4 skriver igen. For aktiv styring skal HCP4
derfor være koblet fra RS485-ledningen.

## Indstillinger

| Indstilling | Betydning |
|---|---|
| `adapter_host`, `adapter_port` | RS485-adapterens IP og TCP-port |
| `bus_access` | Hvad controlleren må sende på bussen (se nedenfor) |
| `controller_token` | Valgfri fast nøgle til Home Assistant-integrationen. Tom: lav den i WebUI'en |
| `log_level` | Logniveau, standard `info` |

`bus_access` åbnes trin for trin:

| Værdi | Sendes på bussen |
|---|---|
| `read_only` | Intet. Standard ved første start |
| `read` | Kun læsninger (FC03/FC04) |
| `fans` | Læsninger og ventilatorer (register 66/67) |
| `fans_bypass` | Læsninger, ventilatorer og bypass (register 68) |
| `direct` | Alt, uden guard. Pejs, standby og eftervarme kræver dette |

Alt, guarden afviser, og alle skrivninger logges i `state/bus-guard.log`.

## Kun én controller ad gangen

En RS485-til-Ethernet-adapter sender ikke det, den selv udsender på bussen,
videre til andre TCP-klienter. To controllere gennem samme adapter kan derfor
**ikke se hinanden**, og begge vil tro, de er master. Stop altid andre
controllere (fx en test i Docker), før denne app får andet end `read_only`.

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

Sæt `bus_access` til `read_only` eller stop appen, og sæt HCP4 i igen.
Anlægget beholder de sidste ventilator- og bypassværdier, indtil HCP4 skriver.
