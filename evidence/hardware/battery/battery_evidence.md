# Battery And Charger Seller Evidence

## Evidence Boundary

The three images in this directory were supplied by the user on 2026-07-23.
They are seller/product-page evidence, not laboratory measurements and not a
manufacturer datasheet. Values visible in the images are classified as
`SELLER_DOCUMENTED`; calculations based on those values are classified as
`CALCULATED_FROM_SELLER_DATA`.

## Files

| File | SHA-256 | Image size | What it documents |
| --- | --- | --- | --- |
| `battery_11v1_7800mah_5c.jpg` | `907E21846D85E6D0B023D40B91DEEF6E9BC1DE6B1251C1810CE1E0AD6E1F0637` | 1200 x 1200 | Exact advertised 7800 mAh variant |
| `charger_12v6_1a.jpg` | `63AF86B1FAF7196361CFDA1855188206D48571AF69044431EF8949909A710F25` | 1440 x 1440 | Advertised matching charger |
| `battery_product_family_specs.jpg` | `E307C973BDA8243D19EB9A35E712D6329CC82BD456A1B9234F328D105466B6F7` | 1264 x 2780 | Product-family table and protection claims |

## Exact 7800 mAh Variant

`battery_11v1_7800mah_5c.jpg` visibly states:

- Li-ion battery;
- 11.1 V nominal voltage;
- 7800 mAh / 7.8 Ah advertised capacity;
- 5C advertised discharge rate;
- 12.6 V fully charged voltage;
- 70 x 55 x 23 mm advertised dimensions; and
- DC 5.5 x 2.5 mm male barrel connector.

The nominal stored energy is `11.1 V x 7.8 Ah = 86.58 Wh`. The advertised 5C
rate implies `7.8 Ah x 5 = 39 A`. Both are calculations, not measured pack
results. The 39 A figure must not be treated as the BMS continuous-current or
peak-current rating because the seller image does not separately state either
BMS threshold.

## Charger

`charger_12v6_1a.jpg` visibly states:

- 110-240 VAC, 50/60 Hz input;
- 12.6 V, 1 A output;
- DC 5.5 x 2.5 mm female connector; and
- 100 cm cable length including the plug.

The charger is for charging the disconnected battery. It is not the rover's
power supply and must not be connected while the battery remains connected to
the rover. An ideal `7.8 Ah / 1 A` calculation gives 7.8 hours; actual charging
will take longer and must follow the charger's indication and pack protection.

## Product-Family Claims

`battery_product_family_specs.jpg` shows 11.1 V nominal, 12.6 V maximum, 3S1P,
and overcharge, overdischarge, overcurrent, and short-circuit protection for the
displayed product family. Its comparison table visibly lists 2600 mAh and
5000 mAh variants, not the exact 7800 mAh variant. Therefore the protection and
3S1P statements are retained as `SELLER_FAMILY_DOCUMENTED`, not proof of the
internal construction or BMS thresholds of this exact pack.

## Still Unverified

- Actual barrel polarity, including whether the centre contact is positive.
- Actual no-load and fully charged voltage measured with a multimeter.
- Actual capacity, internal resistance, age, cell balance, and condition.
- BMS continuous-current, peak-current, overcurrent-trip, and recovery values.
- Charger regulation, connector polarity, cutoff behavior, and charge time.
- Actual dimensions, connector fit, cable current capacity, and pack mass.

Measure polarity and voltage before making an adapter. Do not infer polarity
from connector gender, cable appearance, or common barrel-plug convention.
