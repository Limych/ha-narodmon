*Please :star: this repo if you find it useful*

# NarodMon.ru Cloud Integration Component for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE.md)

[![hacs][hacs-shield]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

[![Community Forum][forum-shield]][forum]

_Component to integrate with narodmon.ru cloud._

**This component will set up the following platforms.**

Platform | Description
-- | --
`binary_sensor` | Show something `True` or `False`.
`sensor` | Show info from blueprint API.
`switch` | Switch something `True` or `False`.

![NarodMon.ru Logo](narodmon-logo.png)

### Install from HACS (recommended)

1. Have [HACS][hacs] installed, this will allow you to easily manage and track updates.
1. Search for "Narodmon".
1. Click Install below the found integration.
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Narodmon".

### Manual installation

1. Configure integration via Home Assistant GUI or via your `configuration.yaml` file using the configuration instructions below.
1. Restart Home Assistant

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `narodmon`.
1. Download file `narodmon.zip` from the [latest release section][releases-latest] in this repository.
1. Extract _all_ files from this archive you downloaded in the directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Blueprint"

<p align="center">* * *</p>
I put a lot of work into making this repo and component available and updated to inspire and help others! I will be glad to receive thanks from you — it will give me new strength and add enthusiasm:
<p align="center"><br>
<a href="https://www.patreon.com/join/limych?" target="_blank"><img src="http://khrolenok.ru/support_patreon.png" alt="Patreon" width="250" height="48"></a>
<br>or&nbsp;support via Bitcoin or Etherium:<br>
<a href="https://sochain.com/a/mjz640g" target="_blank"><img src="http://khrolenok.ru/support_bitcoin.png" alt="Bitcoin" width="150"><br>
16yfCfz9dZ8y8yuSwBFVfiAa3CNYdMh7Ts</a>
</p>

### Configuration Examples

```yaml
# Example configuration.yaml entry
sensor:
  - platform: narodmon
    name: 'Average Temperature'
    entities:
      - weather.gismeteo
      - sensor.owm_temperature
      - sensor.dark_sky_temperature
```

<p align="center">* * *</p>
I put a lot of work into making this repo and component available and updated to inspire and help others! I will be glad to receive thanks from you — it will give me new strength and add enthusiasm:
<p align="center"><br>
<a href="https://www.patreon.com/join/limych?" target="_blank"><img src="http://khrolenok.ru/support_patreon.png" alt="Patreon" width="250" height="48"></a>
<br>or&nbsp;support via Bitcoin or Etherium:<br>
<a href="https://sochain.com/a/mjz640g" target="_blank"><img src="http://khrolenok.ru/support_bitcoin.png" alt="Bitcoin" width="150"><br>
16yfCfz9dZ8y8yuSwBFVfiAa3CNYdMh7Ts</a>
</p>

### Configuration Variables

**entities**:\
  _(list) (Required)_\
  A list of temperature sensor entity IDs.

> **_Note_**:\
> You can use weather provider, climate and water heater entities as a data source. For that entities sensor use values of current temperature.

> **_Note_**:\
> You can use groups of entities as a data source. These groups will be automatically expanded to individual entities.

**name**:\
  _(string) (Optional)_\
  Name to use in the frontend.\
  _Default value: "Average"_

**start**:\
  _(template) (Optional)_\
  When to start the measure (timestamp or datetime).

**end**:\
  _(template) (Optional)_\
  When to stop the measure (timestamp or datetime).

**duration**:\
  _(time) (Optional)_\
  Duration of the measure.

**precision**:\
  _(number) (Optional)_\
  The number of decimals to use when rounding the sensor state.\
  _Default value: 2_

**process_undef_as**:\
  _(number) (Optional)_\
  Process undefined values (unavailable, sensor undefined, etc.) as specified value.\
  \
  By default, undefined values are not included in the average calculation. Specifying this parameter allows you to calculate the average value taking into account the time intervals of the undefined sensor values.

> **_Note_**:\
> This parameter does not affect the calculation of the count, min and max attributes.

## Track updates

You can automatically track new versions of this component and update it by [HACS][hacs].

## Troubleshooting

To enable debug logs use this configuration:
```yaml
# Example configuration.yaml entry
logger:
  default: info
  logs:
    .: debug
```
... then restart HA.

## Contributions are welcome!

This is an active open-source project. We are always open to people who want to
use the code or contribute to it.

We have set up a separate document containing our
[contribution guidelines](CONTRIBUTING.md).

Thank you for being involved! :heart_eyes:

## Authors & contributors

The original setup of this component is by [Andrey "Limych" Khrolenok](https://github.com/Limych).

For a full list of all authors and contributors,
check [the contributor's page][contributors].

## License

creative commons Attribution-NonCommercial-ShareAlike 4.0 International License

See separate [license file](LICENSE.md) for full text.

***

[component]: https://github.com/Limych/ha-narodmon
[commits-shield]: https://img.shields.io/github/commit-activity/y/Limych/ha-narodmon.svg?style=popout
[commits]: https://github.com/Limych/ha-narodmon/commits/master
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=popout
[hacs]: https://hacs.xyz
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=popout
[forum]: https://community.home-assistant.io/
[license]: https://github.com/Limych/ha-narodmon/blob/main/LICENSE.md
[license-shield]: https://img.shields.io/badge/license-Creative_Commons_BY--NC--SA_License-lightgray.svg?style=popout
[maintenance-shield]: https://img.shields.io/badge/maintainer-Andrey%20Khrolenok%20%40Limych-blue.svg?style=popout
[releases-shield]: https://img.shields.io/github/release/Limych/ha-narodmon.svg?style=popout
[releases]: https://github.com/Limych/ha-narodmon/releases
[releases-latest]: https://github.com/Limych/ha-narodmon/releases/latest
[user_profile]: https://github.com/Limych
[report_bug]: https://github.com/Limych/ha-narodmon/issues/new?template=bug_report.md
[suggest_idea]: https://github.com/Limych/ha-narodmon/issues/new?template=feature_request.md
[contributors]: https://github.com/Limych/ha-narodmon/graphs/contributors
