# Seamless Ores

Ore blocks whose background matches the stone they generate in. Granite, diorite, andesite and tuff
variants for every overworld ore, dripstone variants for the ore that dripstone caves wrap in their
walls, basalt and blackstone in the Nether, and the same treatment for the ores of thirteen other mods.

**It adds almost no ore.** The same veins, in the same places, drawn to fit their surroundings.
Two config gated exceptions add ore: the Nether variants, and a few rare ores in the cinnabar of the
Sulfur Caves (26.2 and up).
Lush Caves go the other way: ore left bare in a clay floor or a moss carpet becomes clay or moss,
which removes a little ore there. That is config gated too, and bone meal on moss works exactly as
in vanilla. The Sulfur Caves stay bare the same way: no ore, and none of the large copper and iron
veins, sits in or against their sulfur and cinnabar, which removes ore there (config gated, 26.2 and
up).

| | |
|---|---|
| Minecraft | 26.1, 26.1.1, 26.1.2, 26.2 and 26.3, one jar per loader |
| Loaders | Fabric, NeoForge, Quilt (untested) |
| Wiki | https://chillpavz.com/seamless-ores |
| Licence | PolyForm Shield 1.0.0, see `LICENSE` |

An original mod. Not a fork or a port of any other project.

Which third-party mods have a build differs between these Minecraft versions, and a mod's variants
stay inert until it is installed. The block table further down lists, per version and loader, which
of them a player can actually see.

## Companion resource pack

**Seamless Glowing Ores** makes every ore glow, with an optional connected outline that joins
touching ore of the same type across different host stones.

## Block list

<!-- BEGIN GENERATED block-list -->
**822 blocks** in the `seamlessores` namespace.

**Vanilla, Overworld**

| | granite | diorite | andesite | tuff | dripstone | cinnabar |
|---|---|---|---|---|---|---|
| Coal | `granite_coal_ore` | `diorite_coal_ore` | `andesite_coal_ore` | `tuff_coal_ore` | `dripstone_coal_ore` |   |
| Iron | `granite_iron_ore` | `diorite_iron_ore` | `andesite_iron_ore` | `tuff_iron_ore` | `dripstone_iron_ore` | `cinnabar_iron_ore` |
| Copper | `granite_copper_ore` | `diorite_copper_ore` | `andesite_copper_ore` | `tuff_copper_ore` | `dripstone_copper_ore` |   |
| Gold | `granite_gold_ore` | `diorite_gold_ore` | `andesite_gold_ore` | `tuff_gold_ore` | `dripstone_gold_ore` | `cinnabar_gold_ore` |
| Lapis Lazuli | `granite_lapis_ore` | `diorite_lapis_ore` | `andesite_lapis_ore` | `tuff_lapis_ore` | `dripstone_lapis_ore` |   |
| Diamond | `granite_diamond_ore` | `diorite_diamond_ore` | `andesite_diamond_ore` | `tuff_diamond_ore` | `dripstone_diamond_ore` |   |
| Emerald | `granite_emerald_ore` | `diorite_emerald_ore` | `andesite_emerald_ore` | `tuff_emerald_ore` | `dripstone_emerald_ore` |   |
| Redstone | `granite_redstone_ore` | `diorite_redstone_ore` | `andesite_redstone_ore` | `tuff_redstone_ore` | `dripstone_redstone_ore` | `cinnabar_redstone_ore` |

**Vanilla, Nether**

| | basalt | blackstone |
|---|---|---|
| Gold | `basalt_nether_gold_ore` | `blackstone_nether_gold_ore` |
| Quartz | `basalt_nether_quartz_ore` | `blackstone_nether_quartz_ore` |

**Create, Overworld, requires `create`**

| | granite | diorite | andesite | tuff | dripstone | cinnabar |
|---|---|---|---|---|---|---|
| Zinc | `granite_create_zinc_ore` | `diorite_create_zinc_ore` | `andesite_create_zinc_ore` | `tuff_create_zinc_ore` | `dripstone_create_zinc_ore` | `cinnabar_create_zinc_ore` |

**Create: New Age, Overworld, requires `create_new_age`**

| | granite |
|---|---|
| Thorium | `granite_create_new_age_thorium_ore` |

**Create: TFMG, Overworld, requires `tfmg`**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Lead | `granite_tfmg_lead_ore` | `diorite_tfmg_lead_ore` | `andesite_tfmg_lead_ore` | `tuff_tfmg_lead_ore` | `dripstone_tfmg_lead_ore` |
| Lithium | `granite_tfmg_lithium_ore` |   |   | `tuff_tfmg_lithium_ore` |   |

**Dense Mekanism, Overworld, requires `densemekanism`**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Dense Fluorite | `granite_densemekanism_dense_fluorite_ore` |   |   | `tuff_densemekanism_dense_fluorite_ore` | `dripstone_densemekanism_dense_fluorite_ore` |
| Dense Lead | `granite_densemekanism_dense_lead_ore` | `diorite_densemekanism_dense_lead_ore` | `andesite_densemekanism_dense_lead_ore` | `tuff_densemekanism_dense_lead_ore` | `dripstone_densemekanism_dense_lead_ore` |
| Dense Tin | `granite_densemekanism_dense_tin_ore` |   |   |   |   |
| Dense Uranium | `granite_densemekanism_dense_uranium_ore` | `diorite_densemekanism_dense_uranium_ore` | `andesite_densemekanism_dense_uranium_ore` | `tuff_densemekanism_dense_uranium_ore` | `dripstone_densemekanism_dense_uranium_ore` |

**Energized Power, Overworld, requires `energizedpower`**

| | granite |
|---|---|
| Tin | `granite_energizedpower_tin_ore` |

**Mythic Metals, Overworld, requires `mythicmetals`**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Adamantite | `granite_mythicmetals_adamantite_ore` | `diorite_mythicmetals_adamantite_ore` |   | `tuff_mythicmetals_adamantite_ore` |   |
| Carmot | `granite_mythicmetals_carmot_ore` | `diorite_mythicmetals_carmot_ore` |   |   |   |
| Morkite | `granite_mythicmetals_morkite_ore` |   |   | `tuff_mythicmetals_morkite_ore` |   |
| Mythril | `granite_mythicmetals_mythril_ore` | `diorite_mythicmetals_mythril_ore` |   | `tuff_mythicmetals_mythril_ore` |   |
| Runite | `granite_mythicmetals_runite_ore` | `diorite_mythicmetals_runite_ore` |   |   |   |
| Manganese | `granite_mythicmetals_manganese_ore` | `diorite_mythicmetals_manganese_ore` | `andesite_mythicmetals_manganese_ore` |   | `dripstone_mythicmetals_manganese_ore` |
| Quadrillum | `granite_mythicmetals_quadrillum_ore` | `diorite_mythicmetals_quadrillum_ore` |   |   |   |
| Silver | `granite_mythicmetals_silver_ore` | `diorite_mythicmetals_silver_ore` | `andesite_mythicmetals_silver_ore` |   |   |
| Starrite | `granite_mythicmetals_starrite_ore` | `diorite_mythicmetals_starrite_ore` |   |   |   |
| Tin | `granite_mythicmetals_tin_ore` |   |   |   |   |
| Aquarium |   |   | `andesite_mythicmetals_aquarium_ore` |   |   |
| Banglum |   |   | `andesite_mythicmetals_banglum_ore` |   |   |
| Kyber |   |   | `andesite_mythicmetals_kyber_ore` |   | `dripstone_mythicmetals_kyber_ore` |
| Orichalcum |   |   | `andesite_mythicmetals_orichalcum_ore` |   |   |
| Prometheum |   |   |   | `tuff_mythicmetals_prometheum_ore` |   |
| Unobtainium |   |   |   | `tuff_mythicmetals_unobtainium_ore` |   |

**Mythic Metals, Nether, requires `mythicmetals`**

| | basalt | blackstone |
|---|---|---|
| Banglum | `basalt_mythicmetals_nether_banglum_ore` | `blackstone_mythicmetals_nether_banglum_ore` |
| Midas Gold | `basalt_mythicmetals_midas_gold_ore` | `blackstone_mythicmetals_midas_gold_ore` |
| Palladium | `basalt_mythicmetals_palladium_ore` | `blackstone_mythicmetals_palladium_ore` |
| Stormyx | `basalt_mythicmetals_stormyx_ore` |   |

**Mythic Upgrades, Overworld, requires `mythicupgrades`**

| | granite | diorite | andesite | tuff |
|---|---|---|---|---|
| Aquamarine | `granite_mythicupgrades_aquamarine_ore` |   |   |   |
| Citrine | `granite_mythicupgrades_citrine_ore` | `diorite_mythicupgrades_citrine_ore` | `andesite_mythicupgrades_citrine_ore` | `tuff_mythicupgrades_citrine_ore` |
| Topaz | `granite_mythicupgrades_topaz_ore` |   |   |   |
| Necoium | `granite_mythicupgrades_necoium_ore` |   |   | `tuff_mythicupgrades_necoium_ore` |

**Mythic Upgrades, Nether, requires `mythicupgrades`**

| | basalt | blackstone |
|---|---|---|
| Ruby | `basalt_mythicupgrades_ruby_ore` | `blackstone_mythicupgrades_ruby_ore` |
| Sapphire | `basalt_mythicupgrades_sapphire_ore` | `blackstone_mythicupgrades_sapphire_ore` |

**Powah, Overworld, requires `powah`**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Uraninite | `granite_powah_uraninite_ore` | `diorite_powah_uraninite_ore` | `andesite_powah_uraninite_ore` | `tuff_powah_uraninite_ore` | `dripstone_powah_uraninite_ore` |
| Uraninite Poor | `granite_powah_uraninite_poor_ore` | `diorite_powah_uraninite_poor_ore` | `andesite_powah_uraninite_poor_ore` | `tuff_powah_uraninite_poor_ore` | `dripstone_powah_uraninite_poor_ore` |
| Uraninite Dense | `granite_powah_uraninite_dense_ore` | `diorite_powah_uraninite_dense_ore` | `andesite_powah_uraninite_dense_ore` | `tuff_powah_uraninite_dense_ore` | `dripstone_powah_uraninite_dense_ore` |

**Silent Gear, Overworld, requires `silentgear`**

| | tuff |
|---|---|
| Bort | `tuff_silentgear_bort_ore` |

**Silent's Gems, Overworld, requires `silentgems`**

| | granite | diorite | andesite | tuff | cinnabar |
|---|---|---|---|---|---|
| Garnet | `granite_silentgems_garnet_ore` |   |   |   |   |
| Heliodor | `granite_silentgems_heliodor_ore` |   |   |   |   |
| Aquamarine | `granite_silentgems_aquamarine_ore` |   |   |   |   |
| Citrine | `granite_silentgems_citrine_ore` | `diorite_silentgems_citrine_ore` | `andesite_silentgems_citrine_ore` | `tuff_silentgems_citrine_ore` |   |
| Topaz | `granite_silentgems_topaz_ore` |   |   |   |   |
| Silver | `granite_silentgems_silver_ore` | `diorite_silentgems_silver_ore` | `andesite_silentgems_silver_ore` | `tuff_silentgems_silver_ore` | `cinnabar_silentgems_silver_ore` |
| Carnelian |   |   | `andesite_silentgems_carnelian_ore` | `tuff_silentgems_carnelian_ore` |   |
| Chaos |   |   | `andesite_silentgems_chaos_ore` | `tuff_silentgems_chaos_ore` |   |
| Turquoise |   |   | `andesite_silentgems_turquoise_ore` | `tuff_silentgems_turquoise_ore` |   |
| Black Diamond |   |   |   | `tuff_silentgems_black_diamond_ore` |   |
| White Diamond |   |   |   | `tuff_silentgems_white_diamond_ore` |   |
| Opal |   |   |   | `tuff_silentgems_opal_ore` |   |

**Silent's Gems, Nether, requires `silentgems`**

| | basalt | blackstone |
|---|---|---|
| Carnelian | `basalt_silentgems_nether_carnelian_ore` | `blackstone_silentgems_nether_carnelian_ore` |
| Citrine | `basalt_silentgems_nether_citrine_ore` | `blackstone_silentgems_nether_citrine_ore` |

**Things, Overworld, requires `things`**

| | diorite | tuff |
|---|---|---|
| Gleaming | `diorite_things_gleaming_ore` | `tuff_things_gleaming_ore` |

**Tech Reborn, Overworld, requires `techreborn`**

| | granite | diorite | andesite | tuff | dripstone | cinnabar |
|---|---|---|---|---|---|---|
| Bauxite | `granite_techreborn_bauxite_ore` | `diorite_techreborn_bauxite_ore` | `andesite_techreborn_bauxite_ore` | `tuff_techreborn_bauxite_ore` | `dripstone_techreborn_bauxite_ore` |   |
| Galena | `granite_techreborn_galena_ore` | `diorite_techreborn_galena_ore` | `andesite_techreborn_galena_ore` | `tuff_techreborn_galena_ore` | `dripstone_techreborn_galena_ore` | `cinnabar_techreborn_galena_ore` |
| Lead | `granite_techreborn_lead_ore` | `diorite_techreborn_lead_ore` | `andesite_techreborn_lead_ore` | `tuff_techreborn_lead_ore` | `dripstone_techreborn_lead_ore` | `cinnabar_techreborn_lead_ore` |
| Silver | `granite_techreborn_silver_ore` | `diorite_techreborn_silver_ore` | `andesite_techreborn_silver_ore` | `tuff_techreborn_silver_ore` |   | `cinnabar_techreborn_silver_ore` |
| Tin | `granite_techreborn_tin_ore` |   |   |   |   |   |
| Uranium | `granite_techreborn_uranium_ore` | `diorite_techreborn_uranium_ore` | `andesite_techreborn_uranium_ore` | `tuff_techreborn_uranium_ore` | `dripstone_techreborn_uranium_ore` |   |
| Pyrite |   |   |   |   |   | `cinnabar_techreborn_pyrite_ore` |
| Sphalerite |   |   |   |   |   | `cinnabar_techreborn_sphalerite_ore` |

**Tech Reborn, Nether, requires `techreborn`**

| | basalt | blackstone |
|---|---|---|
| Pyrite | `basalt_techreborn_pyrite_ore` | `blackstone_techreborn_pyrite_ore` |
| Sphalerite | `basalt_techreborn_sphalerite_ore` | `blackstone_techreborn_sphalerite_ore` |
| Cinnabar | `basalt_techreborn_cinnabar_ore` | `blackstone_techreborn_cinnabar_ore` |

**Occultism, Overworld, requires `occultism`**

| | granite | diorite | andesite | tuff | cinnabar |
|---|---|---|---|---|---|
| Silver | `granite_occultism_silver_ore` | `diorite_occultism_silver_ore` | `andesite_occultism_silver_ore` | `tuff_occultism_silver_ore` | `cinnabar_occultism_silver_ore` |

**Ice and Fire, Overworld, requires `iceandfire`**

| | granite | diorite | andesite | tuff |
|---|---|---|---|---|
| Silver | `granite_iceandfire_silver_ore` | `diorite_iceandfire_silver_ore` | `andesite_iceandfire_silver_ore` | `tuff_iceandfire_silver_ore` |

**Mystical Agriculture, Overworld, requires `mysticalagriculture`**

| | granite | diorite | tuff |
|---|---|---|---|
| Prosperity | `granite_mysticalagriculture_prosperity_ore` | `diorite_mysticalagriculture_prosperity_ore` |   |
| Inferium |   |   | `tuff_mysticalagriculture_inferium_ore` |

**Theurgy, Overworld, requires `theurgy`**

| | andesite | tuff |
|---|---|---|
| Sal Ammoniac | `andesite_theurgy_sal_ammoniac_ore` | `tuff_theurgy_sal_ammoniac_ore` |

**EvilCraft, Overworld, requires `evilcraft`**

| | andesite | tuff |
|---|---|---|
| Dark | `andesite_evilcraft_dark_ore` | `tuff_evilcraft_dark_ore` |

**BetterNether, Nether, requires `betternether`**

| | basalt | blackstone |
|---|---|---|
| Betternether Cincinnasite | `basalt_betternether_cincinnasite_ore` | `blackstone_betternether_cincinnasite_ore` |
| Betternether Nether Ruby | `basalt_betternether_nether_ruby_ore` | `blackstone_betternether_nether_ruby_ore` |

**Dense Ores, Overworld, requires `denseores`**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Denseores Copper | `granite_denseores_dense_copper_ore` | `diorite_denseores_dense_copper_ore` | `andesite_denseores_dense_copper_ore` | `tuff_denseores_dense_copper_ore` | `dripstone_denseores_dense_copper_ore` |
| Denseores Iron | `granite_denseores_dense_iron_ore` | `diorite_denseores_dense_iron_ore` | `andesite_denseores_dense_iron_ore` | `tuff_denseores_dense_iron_ore` | `dripstone_denseores_dense_iron_ore` |
| Denseores Gold | `granite_denseores_dense_gold_ore` | `diorite_denseores_dense_gold_ore` | `andesite_denseores_dense_gold_ore` | `tuff_denseores_dense_gold_ore` |   |
| Denseores Lapis Lazuli | `granite_denseores_dense_lapis_ore` | `diorite_denseores_dense_lapis_ore` |   |   |   |
| Denseores Redstone | `granite_denseores_dense_redstone_ore` | `diorite_denseores_dense_redstone_ore` | `andesite_denseores_dense_redstone_ore` | `tuff_denseores_dense_redstone_ore` |   |
| Denseores Emerald | `granite_denseores_dense_emerald_ore` | `diorite_denseores_dense_emerald_ore` |   |   |   |
| Denseores Coal |   |   |   | `tuff_denseores_dense_coal_ore` |   |
| Denseores Diamond |   |   |   | `tuff_denseores_dense_diamond_ore` |   |

**Dense Ores, Nether, requires `denseores`**

| | basalt | blackstone |
|---|---|---|
| Denseores Nether Gold | `basalt_denseores_dense_nether_gold_ore` | `blackstone_denseores_dense_nether_gold_ore` |
| Denseores Nether Quartz | `basalt_denseores_dense_nether_quartz_ore` | `blackstone_denseores_dense_nether_quartz_ore` |
| Denseores Ancient Nether | `basalt_denseores_ancient_nether_ore` | `blackstone_denseores_ancient_nether_ore` |

**Railcraft Reborn, Overworld, requires `railcraft`**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Lead | `granite_railcraft_lead_ore` | `diorite_railcraft_lead_ore` | `andesite_railcraft_lead_ore` | `tuff_railcraft_lead_ore` | `dripstone_railcraft_lead_ore` |
| Silver | `granite_railcraft_silver_ore` | `diorite_railcraft_silver_ore` | `andesite_railcraft_silver_ore` | `tuff_railcraft_silver_ore` |   |
| Tin | `granite_railcraft_tin_ore` |   |   |   |   |
| Zinc | `granite_railcraft_zinc_ore` | `diorite_railcraft_zinc_ore` | `andesite_railcraft_zinc_ore` | `tuff_railcraft_zinc_ore` | `dripstone_railcraft_zinc_ore` |
| Sulfur |   |   | `andesite_railcraft_sulfur_ore` | `tuff_railcraft_sulfur_ore` |   |

A variant is registered only when the mod that owns its ore is installed, so how many of
these (in the game's own rock) you can actually see depends on which mods have a build for
your loader at your Minecraft version:

| Minecraft | Loader | Blocks | Supported mods available here |
|---|---|---|---|
| 26.1 to 26.1.2 | Fabric | 153 | BetterNether, Create, Dense Ores, Energized Power, Mythic Metals, Tech Reborn |
| 26.1 to 26.1.2 | NeoForge | 148 | Dense Ores, Energized Power, EvilCraft, Ice and Fire, Mystical Agriculture, Occultism, Powah, Railcraft Reborn, Silent Gear, Silent's Gems, Theurgy |
| 26.2 | Fabric | 136 | BetterNether, Create, Dense Ores, Energized Power, Mythic Upgrades, Tech Reborn |
| 26.2 | NeoForge | 126 | Dense Ores, Energized Power, EvilCraft, Mythic Upgrades, Occultism, Silent Gear, Silent's Gems, Theurgy |
| 26.3 | Fabric | 100 | BetterNether, Energized Power, Mythic Upgrades, Tech Reborn |
| 26.3 | NeoForge | 69 | Energized Power, EvilCraft, Mythic Upgrades, Occultism, Theurgy |

The registered block set is derived from which mods are loaded rather than from config, so
a client and a server running the same mods always agree and nobody is kicked on join.
<!-- END GENERATED block-list -->

Some ores are deliberately absent rather than overlooked. Mythic Upgrades' ametrine and jade, and
Silent's Gems' end gems, are `block_match end_stone`: the End has no second stone type, so there is
nothing to be seamless with. Thirteen of Silent's Gems' nether gems have a placement count of zero,
so they are registered by that mod but never generate, and a variant would invent ore that does not
exist. Ten of Mythic Metals' ores never generate in tuff, so they get three host stones rather than
four.

Mekanism itself is not supported. It registers its own `mekanism:ore` feature type whose
configuration is not an `OreConfiguration`, so the target list this mod extends is not there to
extend. Dense Mekanism uses a plain `minecraft:ore` and works normally.

## Ores in modded stones

Stones that other mods add, such as Blockus' limestone or Create's layers, are placed after the
ores and swallow them. These blocks give that ore the look of the stone around it. They were a
separate mod, Seamless Ores: Matrix, until it became part of this one; its old block ids convert to
these on load.

An ore that could never form in a stone (coal in marble, diamond in limestone) gets no block there:
that ore becomes the stone instead, so no seam is left. Create's asurine, crimsite, ochrum and
veridium each keep only the ore Create ties them to.

<!-- BEGIN GENERATED modded-stone-list -->
**549 blocks**, plus the dripstone ones listed above. Each exists only when the mod that places its stone is installed, and one of another mod's ore only with that mod as well. A block's id is `<stone>_<ore>_ore`, from the two columns below: `blockus_limestone` and `iron` make `blockus_limestone_iron_ore`.

**Terralith** (its mod or datapack, every 26.x version, both loaders)

Stones: Deep Blackstone `minecraft_blackstone`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Iron | `iron` |  | Deep Blackstone |
| Copper | `copper` |  | Deep Blackstone |
| Gold | `gold` |  | Deep Blackstone |
| Redstone | `redstone` |  | Deep Blackstone |
| Zinc | `zinc` | Create `create` | Deep Blackstone |
| Citrine | `citrine` | Mythic Upgrades `mythicupgrades` | Deep Blackstone |
| Peridot | `peridot` | Mythic Upgrades `mythicupgrades` | Deep Blackstone |
| Morkite | `morkite` | Mythic Metals `mythicmetals` | Deep Blackstone |
| Aquarium | `aquarium` | Mythic Metals `mythicmetals` | Deep Blackstone |
| Manganese | `manganese` | Mythic Metals `mythicmetals` | Deep Blackstone |
| Silver | `silver` | Mythic Metals `mythicmetals` | Deep Blackstone |
| Orichalcum | `orichalcum` | Mythic Metals `mythicmetals` | Deep Blackstone |
| Chaos | `chaos` | Silent's Gems `silentgems` | Deep Blackstone |
| Ruby | `silents_ruby` | Silent's Gems `silentgems` | Deep Blackstone |
| Sapphire | `silents_sapphire` | Silent's Gems `silentgems` | Deep Blackstone |
| Peridot | `silents_peridot` | Silent's Gems `silentgems` | Deep Blackstone |
| Silver | `silents_silver` | Silent's Gems `silentgems` | Deep Blackstone |
| Bauxite | `techreborn_bauxite` | Tech Reborn `techreborn` | Deep Blackstone |
| Galena | `galena` | Tech Reborn `techreborn` | Deep Blackstone |
| Lead | `techreborn_lead` | Tech Reborn `techreborn` | Deep Blackstone |
| Ruby | `techreborn_ruby` | Tech Reborn `techreborn` | Deep Blackstone |
| Sapphire | `techreborn_sapphire` | Tech Reborn `techreborn` | Deep Blackstone |
| Silver | `techreborn_silver` | Tech Reborn `techreborn` | Deep Blackstone |
| Silver | `occultism_silver` | Occultism `occultism` | Deep Blackstone |
| Sapphire | `iceandfire_sapphire` | Ice and Fire `iceandfire` | Deep Blackstone |
| Silver | `iceandfire_silver` | Ice and Fire `iceandfire` | Deep Blackstone |
| Sal Ammoniac | `sal_ammoniac` | Theurgy `theurgy` | Deep Blackstone |
| Dark | `dark` | EvilCraft `evilcraft` | Deep Blackstone |
| Denseores Copper | `denseores_copper` | Dense Ores `denseores` | Deep Blackstone |
| Denseores Iron | `denseores_iron` | Dense Ores `denseores` | Deep Blackstone |
| Denseores Redstone | `denseores_redstone` | Dense Ores `denseores` | Deep Blackstone |
| Lead | `railcraft_lead` | Railcraft Reborn `railcraft` | Deep Blackstone |
| Silver | `railcraft_silver` | Railcraft Reborn `railcraft` | Deep Blackstone |
| Sulfur | `railcraft_sulfur` | Railcraft Reborn `railcraft` | Deep Blackstone |
| Zinc | `railcraft_zinc` | Railcraft Reborn `railcraft` | Deep Blackstone |

**Blockus, requires `blockus`** (Fabric, 26.1.x to 26.3)

Stones: Limestone `blockus_limestone`, Marble `blockus_marble`, Bluestone `blockus_bluestone`, Viridite `blockus_viridite`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Coal | `coal` |  | Limestone |
| Iron | `iron` |  | every stone |
| Copper | `copper` |  | Limestone, Marble, Bluestone |
| Gold | `gold` |  | every stone |
| Lapis Lazuli | `lapis` |  | Marble |
| Emerald | `emerald` |  | Limestone, Marble |
| Redstone | `redstone` |  | Bluestone |
| Zinc | `zinc` | Create `create` | Limestone, Marble |
| Citrine | `citrine` | Mythic Upgrades `mythicupgrades` | every stone |
| Peridot | `peridot` | Mythic Upgrades `mythicupgrades` | Bluestone, Viridite |
| Adamantite | `adamantite` | Mythic Metals `mythicmetals` | Bluestone |
| Morkite | `morkite` | Mythic Metals `mythicmetals` | Bluestone |
| Mythril | `mythril` | Mythic Metals `mythicmetals` | Marble, Bluestone |
| Prometheum | `prometheum` | Mythic Metals `mythicmetals` | Limestone |
| Runite | `runite` | Mythic Metals `mythicmetals` | Marble, Bluestone |
| Aquarium | `aquarium` | Mythic Metals `mythicmetals` | Limestone |
| Banglum | `banglum` | Mythic Metals `mythicmetals` | Limestone |
| Manganese | `manganese` | Mythic Metals `mythicmetals` | Limestone, Marble |
| Silver | `silver` | Mythic Metals `mythicmetals` | Limestone, Marble |
| Tin | `tin` | Mythic Metals `mythicmetals` | Limestone, Marble |
| Tin | `energized_tin` | Energized Power `energizedpower` | Limestone, Marble |
| Bauxite | `techreborn_bauxite` | Tech Reborn `techreborn` | every stone |
| Galena | `galena` | Tech Reborn `techreborn` | Limestone, Marble |
| Iridium | `iridium` | Tech Reborn `techreborn` | Bluestone, Viridite |
| Lead | `techreborn_lead` | Tech Reborn `techreborn` | Limestone, Marble |
| Ruby | `techreborn_ruby` | Tech Reborn `techreborn` | Marble |
| Sapphire | `techreborn_sapphire` | Tech Reborn `techreborn` | Marble |
| Silver | `techreborn_silver` | Tech Reborn `techreborn` | every stone |
| Tin | `techreborn_tin` | Tech Reborn `techreborn` | Limestone, Marble |
| Uranium | `techreborn_uranium` | Tech Reborn `techreborn` | Limestone, Marble |
| Denseores Coal | `denseores_coal` | Dense Ores `denseores` | Limestone |
| Denseores Copper | `denseores_copper` | Dense Ores `denseores` | every stone |
| Denseores Iron | `denseores_iron` | Dense Ores `denseores` | every stone |
| Denseores Lapis Lazuli | `denseores_lapis` | Dense Ores `denseores` | Marble |
| Denseores Redstone | `denseores_redstone` | Dense Ores `denseores` | Bluestone |
| Denseores Emerald | `denseores_emerald` | Dense Ores `denseores` | Limestone, Marble |

**Create, requires `create`** (Create Fly, Fabric, 26.1.2 and 26.2)

Stones: Asurine `create_asurine`, Crimsite `create_crimsite`, Limestone `create_limestone`, Ochrum `create_ochrum`, Scorchia `create_scorchia`, Scoria `create_scoria`, Veridium `create_veridium`, Calcite `minecraft_calcite`, Smooth Basalt `minecraft_smooth_basalt`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Coal | `coal` |  | Limestone |
| Iron | `iron` |  | Crimsite, Limestone, Scoria, Calcite, Smooth Basalt |
| Copper | `copper` |  | Limestone, Scoria, Veridium, Calcite, Smooth Basalt |
| Gold | `gold` |  | Limestone, Ochrum, Scoria, Calcite, Smooth Basalt |
| Lapis Lazuli | `lapis` |  | Calcite |
| Emerald | `emerald` |  | Limestone, Calcite |
| Redstone | `redstone` |  | Crimsite, Scoria, Smooth Basalt |
| Nether Gold | `nether_gold` |  | Scorchia, Scoria, Smooth Basalt |
| Quartz | `quartz` |  | Scorchia, Scoria, Smooth Basalt |
| Zinc | `zinc` |  | Asurine, Limestone, Scoria, Calcite, Smooth Basalt |
| Citrine | `citrine` | Mythic Upgrades `mythicupgrades` | Limestone, Scoria, Calcite, Smooth Basalt |
| Peridot | `peridot` | Mythic Upgrades `mythicupgrades` | Scoria, Smooth Basalt |
| Necoium | `necoium` | Mythic Upgrades `mythicupgrades` | Crimsite |
| Ruby | `ruby` | Mythic Upgrades `mythicupgrades` | Scorchia, Scoria, Smooth Basalt |
| Sapphire | `sapphire` | Mythic Upgrades `mythicupgrades` | Scorchia, Scoria, Smooth Basalt |
| Adamantite | `adamantite` | Mythic Metals `mythicmetals` | Crimsite |
| Carmot | `carmot` | Mythic Metals `mythicmetals` | Crimsite |
| Morkite | `morkite` | Mythic Metals `mythicmetals` | Asurine, Scoria, Smooth Basalt |
| Mythril | `mythril` | Mythic Metals `mythicmetals` | Asurine |
| Prometheum | `prometheum` | Mythic Metals `mythicmetals` | Limestone, Veridium |
| Aquarium | `aquarium` | Mythic Metals `mythicmetals` | Asurine, Limestone, Scoria, Smooth Basalt |
| Banglum | `banglum` | Mythic Metals `mythicmetals` | Limestone, Scoria, Smooth Basalt |
| Kyber | `kyber` | Mythic Metals `mythicmetals` | Asurine, Scoria, Calcite, Smooth Basalt |
| Manganese | `manganese` | Mythic Metals `mythicmetals` | Limestone, Scoria, Calcite, Smooth Basalt |
| Quadrillum | `quadrillum` | Mythic Metals `mythicmetals` | Crimsite |
| Silver | `silver` | Mythic Metals `mythicmetals` | Limestone, Scoria, Calcite, Smooth Basalt |
| Tin | `tin` | Mythic Metals `mythicmetals` | Limestone |
| Orichalcum | `orichalcum` | Mythic Metals `mythicmetals` | Scoria, Veridium, Smooth Basalt |
| Nether Banglum | `nether_banglum` | Mythic Metals `mythicmetals` | Scorchia, Scoria, Smooth Basalt |
| Midas Gold | `midas_gold` | Mythic Metals `mythicmetals` | Scorchia, Scoria, Smooth Basalt |
| Palladium | `palladium` | Mythic Metals `mythicmetals` | Scorchia, Scoria, Smooth Basalt |
| Stormyx | `stormyx` | Mythic Metals `mythicmetals` | Scorchia, Scoria, Smooth Basalt |
| Tin | `energized_tin` | Energized Power `energizedpower` | Limestone |
| Bauxite | `techreborn_bauxite` | Tech Reborn `techreborn` | Limestone, Scoria, Calcite, Smooth Basalt |
| Galena | `galena` | Tech Reborn `techreborn` | Limestone, Scoria, Calcite, Smooth Basalt |
| Lead | `techreborn_lead` | Tech Reborn `techreborn` | Limestone, Scoria, Calcite, Smooth Basalt |
| Ruby | `techreborn_ruby` | Tech Reborn `techreborn` | Scoria, Smooth Basalt |
| Sapphire | `techreborn_sapphire` | Tech Reborn `techreborn` | Scoria, Smooth Basalt |
| Silver | `techreborn_silver` | Tech Reborn `techreborn` | Limestone, Scoria, Calcite, Smooth Basalt |
| Tin | `techreborn_tin` | Tech Reborn `techreborn` | Limestone |
| Uranium | `techreborn_uranium` | Tech Reborn `techreborn` | Limestone, Calcite |
| Cinnabar | `cinnabar` | Tech Reborn `techreborn` | Scorchia, Scoria, Smooth Basalt |
| Pyrite | `pyrite` | Tech Reborn `techreborn` | Scorchia, Scoria, Smooth Basalt |
| Sphalerite | `sphalerite` | Tech Reborn `techreborn` | Scorchia, Scoria, Smooth Basalt |
| Betternether Cincinnasite | `betternether_cincinnasite` | BetterNether `betternether` | Scorchia, Scoria, Smooth Basalt |
| Betternether Nether Ruby | `betternether_nether_ruby` | BetterNether `betternether` | Scorchia, Scoria, Smooth Basalt |
| Denseores Coal | `denseores_coal` | Dense Ores `denseores` | Limestone |
| Denseores Copper | `denseores_copper` | Dense Ores `denseores` | Limestone, Scoria, Calcite, Smooth Basalt |
| Denseores Iron | `denseores_iron` | Dense Ores `denseores` | Limestone, Scoria, Calcite, Smooth Basalt |
| Denseores Gold | `denseores_gold` | Dense Ores `denseores` | Scorchia, Scoria, Smooth Basalt |
| Denseores Lapis Lazuli | `denseores_lapis` | Dense Ores `denseores` | Calcite |
| Denseores Redstone | `denseores_redstone` | Dense Ores `denseores` | Crimsite, Scoria, Smooth Basalt |
| Denseores Emerald | `denseores_emerald` | Dense Ores `denseores` | Limestone, Calcite |
| Denseores Nether Gold | `denseores_nether_gold` | Dense Ores `denseores` | Scorchia, Scoria, Smooth Basalt |
| Denseores Nether Quartz | `denseores_nether_quartz` | Dense Ores `denseores` | Scorchia, Scoria, Smooth Basalt |
| Denseores Ancient Nether | `denseores_ancient_nether` | Dense Ores `denseores` | Scorchia, Scoria, Smooth Basalt |

**Forbidden and Arcanus, requires `forbidden_arcanus`** (NeoForge, 26.1.2)

Stones: Darkstone `forbidden_arcanus_darkstone`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Iron | `iron` |  | Darkstone |
| Gold | `gold` |  | Darkstone |
| Redstone | `redstone` |  | Darkstone |
| Peridot | `silents_peridot` | Silent's Gems `silentgems` | Darkstone |
| Silver | `silents_silver` | Silent's Gems `silentgems` | Darkstone |
| Silver | `occultism_silver` | Occultism `occultism` | Darkstone |
| Dark | `dark` | EvilCraft `evilcraft` | Darkstone |
| Denseores Iron | `denseores_iron` | Dense Ores `denseores` | Darkstone |
| Denseores Redstone | `denseores_redstone` | Dense Ores `denseores` | Darkstone |
| Nickel | `railcraft_nickel` | Railcraft Reborn `railcraft` | Darkstone |
| Silver | `railcraft_silver` | Railcraft Reborn `railcraft` | Darkstone |

**Mythic Upgrades, requires `mythicupgrades`** (Fabric and NeoForge, 26.2 and 26.3)

Stones: Aquamarine Schist `mythicupgrades_aquamarine_schist`, Citrine Schist `mythicupgrades_citrine_schist`, Peridot Schist `mythicupgrades_peridot_schist`, Topaz Schist `mythicupgrades_topaz_schist`, Sapphire Schist `mythicupgrades_sapphire_schist`, Jade Schist `mythicupgrades_jade_schist`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Iron | `iron` |  | Aquamarine Schist, Citrine Schist, Peridot Schist, Topaz Schist |
| Copper | `copper` |  | Aquamarine Schist, Citrine Schist, Peridot Schist, Topaz Schist |
| Gold | `gold` |  | Aquamarine Schist, Citrine Schist, Peridot Schist, Topaz Schist |
| Redstone | `redstone` |  | Aquamarine Schist, Citrine Schist, Peridot Schist, Topaz Schist |
| Aquamarine | `aquamarine` |  | Peridot Schist |
| Citrine | `citrine` |  | Topaz Schist |
| Necoium | `necoium` |  | Aquamarine Schist, Citrine Schist, Peridot Schist, Topaz Schist |
| Ruby | `ruby` |  | Sapphire Schist |
| Ametrine | `ametrine` |  | Jade Schist |

**Regions Unexplored, requires `regions_unexplored`** (Fabric and NeoForge, 26.1.x)

Stones: Mossy Stone `regions_unexplored_mossy_stone`, Argillite `regions_unexplored_argillite`, Chalk `regions_unexplored_chalk`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Coal | `coal` |  | every stone |
| Iron | `iron` |  | every stone |
| Copper | `copper` |  | every stone |
| Gold | `gold` |  | every stone |
| Lapis Lazuli | `lapis` |  | Mossy Stone |
| Emerald | `emerald` |  | Mossy Stone, Chalk |
| Zinc | `zinc` | Create `create` | Mossy Stone, Argillite |
| Prometheum | `prometheum` | Mythic Metals `mythicmetals` | Argillite |
| Aquarium | `aquarium` | Mythic Metals `mythicmetals` | Mossy Stone, Argillite |
| Banglum | `banglum` | Mythic Metals `mythicmetals` | Mossy Stone |
| Manganese | `manganese` | Mythic Metals `mythicmetals` | Argillite |
| Osmium | `osmium` | Mythic Metals `mythicmetals` | Mossy Stone |
| Silver | `silver` | Mythic Metals `mythicmetals` | Argillite |
| Starrite | `starrite` | Mythic Metals `mythicmetals` | Mossy Stone |
| Tin | `tin` | Mythic Metals `mythicmetals` | Mossy Stone, Chalk |
| Silver | `silents_silver` | Silent's Gems `silentgems` | Argillite |
| Uraninite | `uraninite` | Powah `powah` | Argillite |
| Uraninite Poor | `uraninite_poor` | Powah `powah` | Mossy Stone, Argillite |
| Tin | `energized_tin` | Energized Power `energizedpower` | Mossy Stone, Chalk |
| Bauxite | `techreborn_bauxite` | Tech Reborn `techreborn` | Argillite |
| Galena | `galena` | Tech Reborn `techreborn` | Argillite |
| Lead | `techreborn_lead` | Tech Reborn `techreborn` | Argillite |
| Ruby | `techreborn_ruby` | Tech Reborn `techreborn` | Mossy Stone |
| Sapphire | `techreborn_sapphire` | Tech Reborn `techreborn` | Mossy Stone |
| Silver | `techreborn_silver` | Tech Reborn `techreborn` | Argillite |
| Tin | `techreborn_tin` | Tech Reborn `techreborn` | Mossy Stone, Chalk |
| Uranium | `techreborn_uranium` | Tech Reborn `techreborn` | Argillite |
| Silver | `occultism_silver` | Occultism `occultism` | every stone |
| Sapphire | `iceandfire_sapphire` | Ice and Fire `iceandfire` | Mossy Stone |
| Silver | `iceandfire_silver` | Ice and Fire `iceandfire` | every stone |
| Inferium | `inferium` | Mystical Agriculture `mysticalagriculture` | Mossy Stone, Argillite |
| Sal Ammoniac | `sal_ammoniac` | Theurgy `theurgy` | Mossy Stone, Argillite |
| Dark | `dark` | EvilCraft `evilcraft` | Mossy Stone, Argillite |
| Denseores Coal | `denseores_coal` | Dense Ores `denseores` | every stone |
| Denseores Copper | `denseores_copper` | Dense Ores `denseores` | every stone |
| Denseores Iron | `denseores_iron` | Dense Ores `denseores` | every stone |
| Denseores Emerald | `denseores_emerald` | Dense Ores `denseores` | every stone |
| Lead | `railcraft_lead` | Railcraft Reborn `railcraft` | Argillite |
| Nickel | `railcraft_nickel` | Railcraft Reborn `railcraft` | Mossy Stone |
| Silver | `railcraft_silver` | Railcraft Reborn `railcraft` | Argillite |
| Sulfur | `railcraft_sulfur` | Railcraft Reborn `railcraft` | Mossy Stone, Chalk |
| Tin | `railcraft_tin` | Railcraft Reborn `railcraft` | Mossy Stone, Chalk |
| Zinc | `railcraft_zinc` | Railcraft Reborn `railcraft` | Argillite |

**Promenade, requires `promenade`** (Fabric on every 26.x version, NeoForge on 26.3)

Stones: Asphalt `promenade_asphalt`, Blunite `promenade_blunite`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Coal | `coal` |  | Asphalt |
| Iron | `iron` |  | every stone |
| Copper | `copper` |  | every stone |
| Gold | `gold` |  | every stone |
| Redstone | `redstone` |  | Blunite |
| Zinc | `zinc` | Create `create` | Asphalt |
| Citrine | `citrine` | Mythic Upgrades `mythicupgrades` | every stone |
| Peridot | `peridot` | Mythic Upgrades `mythicupgrades` | Blunite |
| Morkite | `morkite` | Mythic Metals `mythicmetals` | Blunite |
| Mythril | `mythril` | Mythic Metals `mythicmetals` | Blunite |
| Prometheum | `prometheum` | Mythic Metals `mythicmetals` | Asphalt |
| Runite | `runite` | Mythic Metals `mythicmetals` | Blunite |
| Banglum | `banglum` | Mythic Metals `mythicmetals` | Asphalt |
| Manganese | `manganese` | Mythic Metals `mythicmetals` | Asphalt |
| Osmium | `osmium` | Mythic Metals `mythicmetals` | Blunite |
| Platinum | `platinum` | Mythic Metals `mythicmetals` | Blunite |
| Quadrillum | `quadrillum` | Mythic Metals `mythicmetals` | Blunite |
| Silver | `silver` | Mythic Metals `mythicmetals` | every stone |
| Bauxite | `techreborn_bauxite` | Tech Reborn `techreborn` | every stone |
| Galena | `galena` | Tech Reborn `techreborn` | Asphalt |
| Iridium | `iridium` | Tech Reborn `techreborn` | Blunite |
| Lead | `techreborn_lead` | Tech Reborn `techreborn` | Asphalt |
| Silver | `techreborn_silver` | Tech Reborn `techreborn` | every stone |
| Uranium | `techreborn_uranium` | Tech Reborn `techreborn` | Asphalt |
| Silver | `occultism_silver` | Occultism `occultism` | every stone |
| Sal Ammoniac | `sal_ammoniac` | Theurgy `theurgy` | Asphalt |
| Dark | `dark` | EvilCraft `evilcraft` | every stone |
| Denseores Coal | `denseores_coal` | Dense Ores `denseores` | Asphalt |
| Denseores Copper | `denseores_copper` | Dense Ores `denseores` | every stone |
| Denseores Iron | `denseores_iron` | Dense Ores `denseores` | every stone |
| Denseores Redstone | `denseores_redstone` | Dense Ores `denseores` | Blunite |

**Wilder Wild, requires `wilderwild`** (Fabric 26.1.x to 26.3, NeoForge 26.2 and 26.3)

Stones: Gabbro `wilderwild_gabbro`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Iron | `iron` |  | Gabbro |
| Copper | `copper` |  | Gabbro |
| Gold | `gold` |  | Gabbro |
| Redstone | `redstone` |  | Gabbro |
| Adamantite | `adamantite` | Mythic Metals `mythicmetals` | Gabbro |
| Morkite | `morkite` | Mythic Metals `mythicmetals` | Gabbro |
| Mythril | `mythril` | Mythic Metals `mythicmetals` | Gabbro |
| Runite | `runite` | Mythic Metals `mythicmetals` | Gabbro |
| Osmium | `osmium` | Mythic Metals `mythicmetals` | Gabbro |
| Platinum | `platinum` | Mythic Metals `mythicmetals` | Gabbro |
| Quadrillum | `quadrillum` | Mythic Metals `mythicmetals` | Gabbro |
| Silver | `silver` | Mythic Metals `mythicmetals` | Gabbro |
| Bauxite | `techreborn_bauxite` | Tech Reborn `techreborn` | Gabbro |
| Iridium | `iridium` | Tech Reborn `techreborn` | Gabbro |
| Silver | `techreborn_silver` | Tech Reborn `techreborn` | Gabbro |
| Silver | `occultism_silver` | Occultism `occultism` | Gabbro |
| Dark | `dark` | EvilCraft `evilcraft` | Gabbro |
| Denseores Copper | `denseores_copper` | Dense Ores `denseores` | Gabbro |
| Denseores Iron | `denseores_iron` | Dense Ores `denseores` | Gabbro |
| Denseores Redstone | `denseores_redstone` | Dense Ores `denseores` | Gabbro |

**YUNG's Cave Biomes, requires `yungscavebiomes`** (Fabric and NeoForge, 26.1.x)

Stones: Ancient Sandstone `yungscavebiomes_ancient_sandstone`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Iron | `iron` |  | Ancient Sandstone |
| Copper | `copper` |  | Ancient Sandstone |
| Gold | `gold` |  | Ancient Sandstone |
| Zinc | `zinc` | Create `create` | Ancient Sandstone |
| Silver | `silver` | Mythic Metals `mythicmetals` | Ancient Sandstone |
| Silver | `silents_silver` | Silent's Gems `silentgems` | Ancient Sandstone |
| Uraninite | `uraninite` | Powah `powah` | Ancient Sandstone |
| Uraninite Poor | `uraninite_poor` | Powah `powah` | Ancient Sandstone |
| Uraninite Dense | `uraninite_dense` | Powah `powah` | Ancient Sandstone |
| Bauxite | `techreborn_bauxite` | Tech Reborn `techreborn` | Ancient Sandstone |
| Galena | `galena` | Tech Reborn `techreborn` | Ancient Sandstone |
| Lead | `techreborn_lead` | Tech Reborn `techreborn` | Ancient Sandstone |
| Silver | `techreborn_silver` | Tech Reborn `techreborn` | Ancient Sandstone |
| Uranium | `techreborn_uranium` | Tech Reborn `techreborn` | Ancient Sandstone |
| Silver | `occultism_silver` | Occultism `occultism` | Ancient Sandstone |
| Silver | `iceandfire_silver` | Ice and Fire `iceandfire` | Ancient Sandstone |
| Denseores Copper | `denseores_copper` | Dense Ores `denseores` | Ancient Sandstone |
| Denseores Iron | `denseores_iron` | Dense Ores `denseores` | Ancient Sandstone |
| Lead | `railcraft_lead` | Railcraft Reborn `railcraft` | Ancient Sandstone |
| Silver | `railcraft_silver` | Railcraft Reborn `railcraft` | Ancient Sandstone |
| Zinc | `railcraft_zinc` | Railcraft Reborn `railcraft` | Ancient Sandstone |

**Nature's Spirit, requires `natures_spirit`** (Fabric and NeoForge, 26.1.x)

Stones: Chert `natures_spirit_chert`, Travertine `natures_spirit_travertine`, White Chalk `natures_spirit_white_chalk`, Pink Sandstone `natures_spirit_pink_sandstone`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Coal | `coal` |  | Travertine, White Chalk |
| Iron | `iron` |  | Travertine, White Chalk, Pink Sandstone |
| Copper | `copper` |  | Travertine, White Chalk, Pink Sandstone |
| Gold | `gold` |  | Travertine, White Chalk, Pink Sandstone |
| Zinc | `zinc` | Create `create` | every stone |
| Aquarium | `aquarium` | Mythic Metals `mythicmetals` | Chert, Travertine, White Chalk |
| Banglum | `banglum` | Mythic Metals `mythicmetals` | Travertine, White Chalk |
| Manganese | `manganese` | Mythic Metals `mythicmetals` | Chert |
| Silver | `silver` | Mythic Metals `mythicmetals` | Chert |
| Tin | `tin` | Mythic Metals `mythicmetals` | Travertine, White Chalk |
| Silver | `silents_silver` | Silent's Gems `silentgems` | Chert |
| Uraninite Poor | `uraninite_poor` | Powah `powah` | Travertine, Pink Sandstone |
| Tin | `energized_tin` | Energized Power `energizedpower` | Travertine, White Chalk |
| Galena | `galena` | Tech Reborn `techreborn` | Chert |
| Lead | `techreborn_lead` | Tech Reborn `techreborn` | Chert |
| Silver | `techreborn_silver` | Tech Reborn `techreborn` | Chert |
| Tin | `techreborn_tin` | Tech Reborn `techreborn` | Travertine, White Chalk |
| Silver | `occultism_silver` | Occultism `occultism` | every stone |
| Silver | `iceandfire_silver` | Ice and Fire `iceandfire` | every stone |
| Inferium | `inferium` | Mystical Agriculture `mysticalagriculture` | Travertine, White Chalk |
| Denseores Coal | `denseores_coal` | Dense Ores `denseores` | Travertine, White Chalk |
| Denseores Copper | `denseores_copper` | Dense Ores `denseores` | every stone |
| Denseores Iron | `denseores_iron` | Dense Ores `denseores` | every stone |
| Denseores Emerald | `denseores_emerald` | Dense Ores `denseores` | Travertine, White Chalk |
| Lead | `railcraft_lead` | Railcraft Reborn `railcraft` | Chert |
| Silver | `railcraft_silver` | Railcraft Reborn `railcraft` | Chert |
| Sulfur | `railcraft_sulfur` | Railcraft Reborn `railcraft` | Travertine, White Chalk |
| Tin | `railcraft_tin` | Railcraft Reborn `railcraft` | Travertine, White Chalk |
| Zinc | `railcraft_zinc` | Railcraft Reborn `railcraft` | Chert |

**BetterEnd, requires `betterend`** (Fabric, 26.1.x to 26.3)

Stones: Flavolite `betterend_flavolite`, Violecite `betterend_violecite`, Sulphuric Rock `betterend_sulphuric_rock`, Brimstone `betterend_brimstone`, Umbralith `betterend_umbralith`, Azure Jadestone `betterend_azure_jadestone`, Sandy Jadestone `betterend_sandy_jadestone`, Virid Jadestone `betterend_virid_jadestone`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Ametrine | `ametrine` | Mythic Upgrades `mythicupgrades` | Flavolite, Violecite, Azure Jadestone, Sandy Jadestone, Virid Jadestone |
| Peridot | `techreborn_peridot` | Tech Reborn `techreborn` | Flavolite, Violecite, Azure Jadestone, Sandy Jadestone, Virid Jadestone |
| Sheldonite | `sheldonite` | Tech Reborn `techreborn` | Flavolite, Sulphuric Rock, Brimstone, Umbralith |
| Sodalite | `sodalite` | Tech Reborn `techreborn` | Flavolite, Violecite, Azure Jadestone, Sandy Jadestone, Virid Jadestone |
| Tungsten | `techreborn_tungsten` | Tech Reborn `techreborn` | Flavolite, Sulphuric Rock, Brimstone, Umbralith |
| Jade | `jade` | Mythic Upgrades `mythicupgrades` | Flavolite, Violecite, Azure Jadestone, Sandy Jadestone, Virid Jadestone |
<!-- END GENERATED modded-stone-list -->

## Configuration

Every setting gates **worldgen only, never registration**, which is what makes a client and a server
structurally unable to disagree. Disabling something means it stops generating; the blocks still
exist, in the creative tab and in every tag, and chunks that already generated never change.

Each supported mod has its own category with a single switch, and the category is hidden when the
mod is not installed. Silent's Gems is the exception and gets four settings, because its overworld
gems restyle ore that already generates while its nether gems add ore that does not, so the two
halves are switched and tuned separately.

Settings take effect the next time a world is loaded, because the injection runs at server start.

## For resource pack authors

<!-- BEGIN GENERATED overlay-list -->
Every variant of one ore shares a single overlay texture, so covering all 822 blocks takes **114 PNG files**:

```
assets/seamlessores/textures/block/<ore>_overlay.png
```

where `<ore>` is one of:

`adamantite` `ametrine` `aquamarine` `aquarium` `banglum` `betternether_cincinnasite` `betternether_nether_ruby` `black_diamond` `bort` `carmot` `carnelian` `chaos` `cinnabar` `citrine` `coal` `copper` `dark` `dense_fluorite` `dense_lead` `dense_tin` `dense_uranium` `denseores_ancient_nether` `denseores_coal` `denseores_coal_deepslate` `denseores_copper` `denseores_diamond` `denseores_emerald` `denseores_gold` `denseores_iron` `denseores_lapis` `denseores_nether_gold` `denseores_nether_quartz` `denseores_redstone` `diamond` `emerald` `energized_tin` `galena` `garnet` `gleaming` `gold` `heliodor` `iceandfire_deepslate_silver` `iceandfire_sapphire` `iceandfire_silver` `inferium` `iridium` `iron` `jade` `kyber` `lapis` `lead` `lithium` `manganese` `midas_gold` `morkite` `mythril` `necoium` `nether_banglum` `nether_gold` `occultism_silver` `opal_tuff` `orichalcum` `osmium` `palladium` `peridot` `platinum` `prometheum` `prosperity` `pyrite` `quadrillum` `quartz` `railcraft_lead` `railcraft_nickel` `railcraft_silver` `railcraft_sulfur` `railcraft_tin` `railcraft_zinc` `redstone` `ruby` `runite` `sal_ammoniac` `sapphire` `sheldonite` `silents_aquamarine` `silents_citrine` `silents_peridot` `silents_ruby` `silents_sapphire` `silents_silver` `silents_topaz` `silver` `sodalite` `sphalerite` `starrite` `stormyx` `techreborn_bauxite` `techreborn_lead` `techreborn_peridot` `techreborn_ruby` `techreborn_sapphire` `techreborn_silver` `techreborn_tin` `techreborn_tungsten` `techreborn_uranium` `thorium` `tin` `topaz` `turquoise` `unobtainium_deepslate` `uraninite` `uraninite_dense` `uraninite_poor` `white_diamond` `zinc`
<!-- END GENERATED overlay-list -->

Each file is the ore layer only, blobs on transparency. The host stone is the vanilla texture at its
usual path, so you do not supply it. A pack that replaces that texture restyles the stone of these
blocks too.

## Building

Requires JDK 25 and Python 3.

One jar per loader serves every 26.x version. It is made from two builds, one against the oldest
version and one against 26.3, joined by a script:

```
./gradlew build -Pmc=26.3
./gradlew build -Pmc=26.1.x
python tools/merge_bands.py
```

`-Pmc` picks a file in `versions/`, which holds everything that changes with the Minecraft version.
The script leaves `seamlessores-<loader>-26.x-<version>.jar` in `fabric/build/libs` and
`neoforge/build/libs` and removes the two per-version jars; it stops if the builds differ anywhere
they should not. Take the plain jar, not the `-sources` or `-javadoc` one. Fabric Loader rejects the
sources jar, because its metadata still holds unexpanded build placeholders.

Assets, loot tables, tags and this README's block list are generated rather than hand written:

```
py -3.14 tools/generate_assets.py
```

It is idempotent and does not touch textures unless you pass `--textures`, which overwrites the hand
cleaned overlays.

## Project layout

| Path | What it holds |
|---|---|
| `common/` | Everything shared: content registration, worldgen injection, config holder |
| `common/src/era261`, `common/src/era263` | The worldgen code whose Minecraft API changed at 26.3, one folder per side |
| `*/src/main/resources/mc26.1`, `mc26.2`, `mc26.3` | Each version's loot tables, as pack overlays chosen by data format |
| `fabric/`, `neoforge/` | Loader entry points |
| `cloth-config/` | The Cloth Config data class and screen, one copy compiled by both loaders |
| `versions/` | Minecraft, loader and dependency versions per build |
| `tools/generate_assets.py` | Generates blockstates, models, lang, loot tables, tags and the block list above |
| `tools/merge_bands.py` | Joins the two builds into the one jar per loader |

The Cloth Config classes sit in `cloth-config/`, outside `common`, because loader dependencies are not
on its classpath; both loader modules compile that one copy.

## How it works, briefly

Seamless Ores does not add worldgen features. At server start it extends the target lists of the ore
features that already exist, adding one entry per host stone ahead of vanilla's. The game then picks
the ore texture from the block that was actually at each position, which is why distribution is
unchanged and why veins blend across a stone boundary by themselves.

Patching the live registry rather than shipping replacement JSON files is deliberate: it composes
with worldgen overhauls and ore datapacks instead of overwriting them.

Dripstone variants are a one for one swap: an ore that a dripstone cave's wall surrounds becomes the
dripstone variant of the same ore, so the amount of ore stays the same.

The exceptions, all config gated and all stated on the store page: Lush Caves clay and moss take the
ore stranded in them, which removes it; the Sulfur Caves keep ore and the large veins out of their
sulfur and cinnabar, which removes it too; the cinnabar ores add ore, because nothing in vanilla
generates in cinnabar; basalt and blackstone gold and
quartz add ore, because vanilla's Nether features match netherrack only; Silent's Gems' nether gems
and Tech Reborn's cinnabar, pyrite and sphalerite do the same, because those mods target netherrack
only as well; and Mythic Upgrades' ruby and sapphire in basalt deltas are placed by a feature this
mod adds, because Mythic Upgrades restricts its own ore to a single biome and there was nothing to
extend.

Full detail is on the wiki.

## Credits

<!-- BEGIN GENERATED credits -->
The vanilla ore overlays are derived from Minecraft's own textures and remain Mojang's
property. Each supported mod's overlay is derived from that mod's own ore texture, so it
is theirs and is used under the licence shown:

| Mod | Author | Licence |
|---|---|---|
| Create | - | MIT |
| Create: New Age | Antarctic Gardens | BSD-3-Clause |
| Create: TFMG | DrMangoTea, Pepa, Luna | MIT |
| Dense Mekanism | - | MIT |
| Energized Power | JDDev0 | MIT |
| Mythic Metals | Noaaan | MIT |
| Mythic Upgrades | TriQue | MIT |
| Powah | owmii, Technici4n, shartte | LGPL-3.0 |
| Silent Gear | SilentChaos512 | MIT |
| Silent's Gems | SilentChaos512 | MIT |
| Things | glisco | MIT |
| Tech Reborn | Team Reborn, modmuss50, drcrazy | MIT |
| Occultism | Kli Kli | MIT |
| Ice and Fire | Alexthe666, the Community Edition by IAFEnvoy | LGPL-3.0 |
| Mystical Agriculture | BlakeBr0 | MIT |
| Theurgy | Kli Kli | CC BY-SA 4.0 (art) |
| EvilCraft | rubensworks | CC BY 4.0 (art) |
| BetterNether | quiqueck, paulevs | MIT |
| Dense Ores | NewJumperr | AGPL-3.0 (art, as its Modrinth page) |
| Railcraft Reborn | Sm0keySa1m0n, Edivad99 | Railcraft Reborn License |
<!-- END GENERATED credits -->

Built on [MultiLoader Template](https://github.com/jaredlll08/MultiLoader-Template) by jaredlll08.
