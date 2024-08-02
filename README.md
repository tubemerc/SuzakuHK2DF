# SuzakuHK2DF
Convert housekeeping data (FITS file format) from the Suzaku into a DataFrame.

## Housekeeping data of Suzaku
- About Suzaku: https://www.isas.jaxa.jp/missions/spacecraft/past/suzaku.html
- Housekeeping data from the Suzaku is available on Data ARchives and Transmission System (DARTS).
  - DARTS/Suzaku: https://darts.isas.jaxa.jp/astro/suzaku/
  - Suzaku/ver3.0: https://data.darts.isas.jaxa.jp/pub/suzaku/ver3.0/

## `filters.py`
### `exclude_unit_filter`
- Ignore data with physical units in this list.
### `data_name_filter`
- Only data with data names that contain strings in this list are extracted. If this list is - empty, all data are extracted.
### `calibration_filter`
- If `true`, only calibrated data is extracted.