# Afvalwijzer

This plugin will give you an alert when the next garbage collection is for your postal code/housenumber.
Currently the following places/companies are supported:

- Afvalvrij/Circulus-Berkel 
- Alphen aan den RijnAvalex
- Berkelland
- Cranendonck
- Cure
- Cyclus NV
- Dar
- Den Haag
- GAD
- HVC
- Meerlanden
- Montfoort
- RMN
- Spaarnelanden
- Súdwest-Fryslân
- Venray
- Waalre
- ZRD

## Parameters
| Parameter             | Description
| :---                  | :---
| **Postal&nbsp;code&nbsp;(NL)**  | Enter your postal code in the format 1234AB
| **House&nbsp;number**      | Enter you house number
| **Alert&nbsp;days&nbsp;before** | Specify when you will get de highest alert (level 4 = red). "0" (default) will give you the alert on the collection day, "1" will be the day before, etc.
| **Debug**             | False (default) or True

## Devices
The following parameters are displayed:

| Name      | Description
| :---      | :---
| **Dates** | Displays the next dates for the garbage collection
| **Alert** | Gives you an alert for the next garbage collection