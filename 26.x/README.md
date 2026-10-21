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
**819 blocks** in the `seamlessores` namespace.

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
| Gold | `basalt_gold_ore` | `blackstone_gold_ore` |
| Quartz | `basalt_quartz_ore` | `blackstone_quartz_ore` |

**Create, Overworld, requires `create`**

| | granite | diorite | andesite | tuff | dripstone | cinnabar |
|---|---|---|---|---|---|---|
| Zinc | `granite_zinc_ore` | `diorite_zinc_ore` | `andesite_zinc_ore` | `tuff_zinc_ore` | `dripstone_zinc_ore` | `cinnabar_zinc_ore` |

**Create: New Age, Overworld, requires `create_new_age`**

| | granite |
|---|---|
| Thorium | `granite_thorium_ore` |

**Create: TFMG, Overworld, requires `tfmg`**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Lead | `granite_lead_ore` | `diorite_lead_ore` | `andesite_lead_ore` | `tuff_lead_ore` | `dripstone_lead_ore` |
| Lithium | `granite_lithium_ore` |   |   | `tuff_lithium_ore` |   |

**Dense Mekanism, Overworld, requires `densemekanism`**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Dense Fluorite | `granite_dense_fluorite_ore` |   |   | `tuff_dense_fluorite_ore` | `dripstone_dense_fluorite_ore` |
| Dense Lead | `granite_dense_lead_ore` | `diorite_dense_lead_ore` | `andesite_dense_lead_ore` | `tuff_dense_lead_ore` | `dripstone_dense_lead_ore` |
| Dense Tin | `granite_dense_tin_ore` |   |   |   |   |
| Dense Uranium | `granite_dense_uranium_ore` | `diorite_dense_uranium_ore` | `andesite_dense_uranium_ore` | `tuff_dense_uranium_ore` | `dripstone_dense_uranium_ore` |

**Energized Power, Overworld, requires `energizedpower`**

| | granite |
|---|---|
| Tin | `granite_energized_tin_ore` |

**Mythic Metals, Overworld, requires `mythicmetals`**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Adamantite | `granite_adamantite_ore` | `diorite_adamantite_ore` | `andesite_adamantite_ore` | `tuff_adamantite_ore` | `dripstone_adamantite_ore` |
| Carmot | `granite_carmot_ore` | `diorite_carmot_ore` | `andesite_carmot_ore` | `tuff_carmot_ore` | `dripstone_carmot_ore` |
| Morkite | `granite_morkite_ore` | `diorite_morkite_ore` | `andesite_morkite_ore` | `tuff_morkite_ore` | `dripstone_morkite_ore` |
| Mythril | `granite_mythril_ore` | `diorite_mythril_ore` | `andesite_mythril_ore` | `tuff_mythril_ore` | `dripstone_mythril_ore` |
| Prometheum | `granite_prometheum_ore` | `diorite_prometheum_ore` | `andesite_prometheum_ore` | `tuff_prometheum_ore` | `dripstone_prometheum_ore` |
| Runite | `granite_runite_ore` | `diorite_runite_ore` | `andesite_runite_ore` | `tuff_runite_ore` | `dripstone_runite_ore` |
| Unobtainium | `granite_unobtainium_ore` | `diorite_unobtainium_ore` | `andesite_unobtainium_ore` | `tuff_unobtainium_ore` | `dripstone_unobtainium_ore` |
| Aquarium | `granite_aquarium_ore` | `diorite_aquarium_ore` | `andesite_aquarium_ore` |   | `dripstone_aquarium_ore` |
| Banglum | `granite_banglum_ore` | `diorite_banglum_ore` | `andesite_banglum_ore` |   | `dripstone_banglum_ore` |
| Kyber | `granite_kyber_ore` | `diorite_kyber_ore` | `andesite_kyber_ore` |   | `dripstone_kyber_ore` |
| Manganese | `granite_manganese_ore` | `diorite_manganese_ore` | `andesite_manganese_ore` |   | `dripstone_manganese_ore` |
| Quadrillum | `granite_quadrillum_ore` | `diorite_quadrillum_ore` | `andesite_quadrillum_ore` |   | `dripstone_quadrillum_ore` |
| Silver | `granite_silver_ore` | `diorite_silver_ore` | `andesite_silver_ore` |   |   |
| Starrite | `granite_starrite_ore` | `diorite_starrite_ore` | `andesite_starrite_ore` |   | `dripstone_starrite_ore` |
| Tin | `granite_tin_ore` |   |   |   |   |
| Orichalcum | `granite_orichalcum_ore` | `diorite_orichalcum_ore` | `andesite_orichalcum_ore` |   | `dripstone_orichalcum_ore` |

**Mythic Metals, Nether, requires `mythicmetals`**

| | basalt | blackstone |
|---|---|---|
| Banglum | `basalt_banglum_ore` | `blackstone_banglum_ore` |
| Midas Gold | `basalt_midas_gold_ore` | `blackstone_midas_gold_ore` |
| Palladium | `basalt_palladium_ore` | `blackstone_palladium_ore` |
| Stormyx | `basalt_stormyx_ore` |   |

**Mythic Upgrades, Overworld, requires `mythicupgrades`**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Aquamarine | `granite_aquamarine_ore` |   |   |   |   |
| Citrine | `granite_citrine_ore` | `diorite_citrine_ore` | `andesite_citrine_ore` | `tuff_citrine_ore` |   |
| Topaz | `granite_topaz_ore` |   |   |   |   |
| Necoium | `granite_necoium_ore` | `diorite_necoium_ore` | `andesite_necoium_ore` | `tuff_necoium_ore` | `dripstone_necoium_ore` |

**Mythic Upgrades, Nether, requires `mythicupgrades`**

| | basalt | blackstone |
|---|---|---|
| Ruby | `basalt_ruby_ore` | `blackstone_ruby_ore` |
| Sapphire | `basalt_sapphire_ore` | `blackstone_sapphire_ore` |

**Powah, Overworld, requires `powah`**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Uraninite | `granite_uraninite_ore` | `diorite_uraninite_ore` | `andesite_uraninite_ore` | `tuff_uraninite_ore` | `dripstone_uraninite_ore` |
| Uraninite Poor | `granite_uraninite_poor_ore` | `diorite_uraninite_poor_ore` | `andesite_uraninite_poor_ore` | `tuff_uraninite_poor_ore` | `dripstone_uraninite_poor_ore` |
| Uraninite Dense | `granite_uraninite_dense_ore` | `diorite_uraninite_dense_ore` | `andesite_uraninite_dense_ore` | `tuff_uraninite_dense_ore` | `dripstone_uraninite_dense_ore` |

**Silent Gear, Overworld, requires `silentgear`**

| | tuff |
|---|---|
| Bort | `tuff_bort_ore` |

**Silent's Gems, Overworld, requires `silentgems`**

| | granite | diorite | andesite | tuff | dripstone | cinnabar |
|---|---|---|---|---|---|---|
| Chaos | `granite_chaos_ore` | `diorite_chaos_ore` | `andesite_chaos_ore` | `tuff_chaos_ore` | `dripstone_chaos_ore` |   |
| Garnet | `granite_garnet_ore` |   |   |   |   |   |
| Heliodor | `granite_heliodor_ore` |   |   |   |   |   |
| Aquamarine | `granite_silents_aquamarine_ore` |   |   |   |   |   |
| Citrine | `granite_silents_citrine_ore` | `diorite_silents_citrine_ore` | `andesite_silents_citrine_ore` | `tuff_silents_citrine_ore` |   |   |
| Topaz | `granite_silents_topaz_ore` |   |   |   |   |   |
| Silver | `granite_silents_silver_ore` | `diorite_silents_silver_ore` | `andesite_silents_silver_ore` | `tuff_silents_silver_ore` |   | `cinnabar_silents_silver_ore` |
| Carnelian |   |   | `andesite_carnelian_ore` | `tuff_carnelian_ore` |   |   |
| Turquoise |   |   | `andesite_turquoise_ore` | `tuff_turquoise_ore` |   |   |
| Black Diamond |   |   |   | `tuff_black_diamond_ore` |   |   |
| White Diamond |   |   |   | `tuff_white_diamond_ore` |   |   |
| Opal |   |   |   | `tuff_opal_ore` |   |   |

**Silent's Gems, Nether, requires `silentgems`**

| | basalt | blackstone |
|---|---|---|
| Carnelian | `basalt_carnelian_ore` | `blackstone_carnelian_ore` |
| Citrine | `basalt_silents_citrine_ore` | `blackstone_silents_citrine_ore` |

**Things, Overworld, requires `things`**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Gleaming | `granite_gleaming_ore` | `diorite_gleaming_ore` | `andesite_gleaming_ore` | `tuff_gleaming_ore` | `dripstone_gleaming_ore` |

**Tech Reborn, Overworld, requires `techreborn`**

| | granite | diorite | andesite | tuff | dripstone | cinnabar |
|---|---|---|---|---|---|---|
| Bauxite | `granite_techreborn_bauxite_ore` | `diorite_techreborn_bauxite_ore` | `andesite_techreborn_bauxite_ore` | `tuff_techreborn_bauxite_ore` | `dripstone_techreborn_bauxite_ore` |   |
| Galena | `granite_galena_ore` | `diorite_galena_ore` | `andesite_galena_ore` | `tuff_galena_ore` | `dripstone_galena_ore` | `cinnabar_galena_ore` |
| Lead | `granite_techreborn_lead_ore` | `diorite_techreborn_lead_ore` | `andesite_techreborn_lead_ore` | `tuff_techreborn_lead_ore` | `dripstone_techreborn_lead_ore` | `cinnabar_techreborn_lead_ore` |
| Silver | `granite_techreborn_silver_ore` | `diorite_techreborn_silver_ore` | `andesite_techreborn_silver_ore` | `tuff_techreborn_silver_ore` |   | `cinnabar_techreborn_silver_ore` |
| Tin | `granite_techreborn_tin_ore` |   |   |   |   |   |
| Uranium | `granite_techreborn_uranium_ore` | `diorite_techreborn_uranium_ore` | `andesite_techreborn_uranium_ore` | `tuff_techreborn_uranium_ore` | `dripstone_techreborn_uranium_ore` |   |
| Pyrite |   |   |   |   |   | `cinnabar_pyrite_ore` |
| Sphalerite |   |   |   |   |   | `cinnabar_sphalerite_ore` |

**Tech Reborn, Nether, requires `techreborn`**

| | basalt | blackstone |
|---|---|---|
| Pyrite | `basalt_pyrite_ore` | `blackstone_pyrite_ore` |
| Sphalerite | `basalt_sphalerite_ore` | `blackstone_sphalerite_ore` |
| Cinnabar | `basalt_cinnabar_ore` | `blackstone_cinnabar_ore` |

**Occultism, Overworld, requires `occultism`**

| | granite | diorite | andesite | tuff | cinnabar |
|---|---|---|---|---|---|
| Silver | `granite_occultism_silver_ore` | `diorite_occultism_silver_ore` | `andesite_occultism_silver_ore` | `tuff_occultism_silver_ore` | `cinnabar_occultism_silver_ore` |

**Ice and Fire, Overworld, requires `iceandfire`**

| | granite | diorite | andesite | tuff |
|---|---|---|---|---|
| Iceandfire Silver | `granite_iceandfire_silver_ore` | `diorite_iceandfire_silver_ore` | `andesite_iceandfire_silver_ore` | `tuff_iceandfire_silver_ore` |

**Mystical Agriculture, Overworld, requires `mysticalagriculture`**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Inferium | `granite_inferium_ore` | `diorite_inferium_ore` | `andesite_inferium_ore` | `tuff_inferium_ore` | `dripstone_inferium_ore` |
| Prosperity | `granite_prosperity_ore` | `diorite_prosperity_ore` | `andesite_prosperity_ore` | `tuff_prosperity_ore` | `dripstone_prosperity_ore` |

A variant is registered only when the mod that owns its ore is installed, so how many of
these (in the game's own rock) you can actually see depends on which mods have a build for
your loader at your Minecraft version:

| Minecraft | Loader | Blocks | Supported mods available here |
|---|---|---|---|
| 26.1 to 26.1.2 | Fabric | 155 | Create, Energized Power, Mythic Metals, Tech Reborn |
| 26.1 to 26.1.2 | NeoForge | 107 | Energized Power, Ice and Fire, Mystical Agriculture, Occultism, Powah, Silent Gear, Silent's Gems |
| 26.2 | Fabric | 105 | Create, Energized Power, Mythic Upgrades, Tech Reborn |
| 26.2 | NeoForge | 98 | Energized Power, Mythic Upgrades, Occultism, Silent Gear, Silent's Gems |
| 26.3 | Fabric | 99 | Energized Power, Mythic Upgrades, Tech Reborn |
| 26.3 | NeoForge | 68 | Energized Power, Mythic Upgrades, Occultism |

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
| Necoium | `necoium` | Mythic Upgrades `mythicupgrades` | Deep Blackstone |
| Adamantite | `adamantite` | Mythic Metals `mythicmetals` | Deep Blackstone |
| Carmot | `carmot` | Mythic Metals `mythicmetals` | Deep Blackstone |
| Morkite | `morkite` | Mythic Metals `mythicmetals` | Deep Blackstone |
| Mythril | `mythril` | Mythic Metals `mythicmetals` | Deep Blackstone |
| Prometheum | `prometheum` | Mythic Metals `mythicmetals` | Deep Blackstone |
| Runite | `runite` | Mythic Metals `mythicmetals` | Deep Blackstone |
| Unobtainium | `unobtainium` | Mythic Metals `mythicmetals` | Deep Blackstone |
| Aquarium | `aquarium` | Mythic Metals `mythicmetals` | Deep Blackstone |
| Manganese | `manganese` | Mythic Metals `mythicmetals` | Deep Blackstone |
| Quadrillum | `quadrillum` | Mythic Metals `mythicmetals` | Deep Blackstone |
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
| Iceandfire Sapphire | `iceandfire_sapphire` | Ice and Fire `iceandfire` | Deep Blackstone |
| Iceandfire Silver | `iceandfire_silver` | Ice and Fire `iceandfire` | Deep Blackstone |
| Inferium | `inferium` | Mystical Agriculture `mysticalagriculture` | Deep Blackstone |
| Prosperity | `prosperity` | Mystical Agriculture `mysticalagriculture` | Deep Blackstone |

**Blockus, requires `blockus`** (Fabric, 26.1.x to 26.3)

Stones: Limestone `blockus_limestone`, Marble `blockus_marble`, Bluestone `blockus_bluestone`, Viridite `blockus_viridite`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Coal | `coal` |  | Limestone |
| Iron | `iron` |  | every stone |
| Copper | `copper` |  | Limestone, Marble, Bluestone |
| Gold | `gold` |  | every stone |
| Lapis Lazuli | `lapis` |  | Marble, Viridite |
| Diamond | `diamond` |  | Viridite |
| Emerald | `emerald` |  | Limestone, Marble |
| Redstone | `redstone` |  | every stone |
| Zinc | `zinc` | Create `create` | Limestone, Marble, Viridite |
| Aquamarine | `aquamarine` | Mythic Upgrades `mythicupgrades` | Viridite |
| Citrine | `citrine` | Mythic Upgrades `mythicupgrades` | every stone |
| Peridot | `peridot` | Mythic Upgrades `mythicupgrades` | Bluestone, Viridite |
| Topaz | `topaz` | Mythic Upgrades `mythicupgrades` | Viridite |
| Necoium | `necoium` | Mythic Upgrades `mythicupgrades` | every stone |
| Adamantite | `adamantite` | Mythic Metals `mythicmetals` | Bluestone, Viridite |
| Carmot | `carmot` | Mythic Metals `mythicmetals` | every stone |
| Morkite | `morkite` | Mythic Metals `mythicmetals` | every stone |
| Mythril | `mythril` | Mythic Metals `mythicmetals` | every stone |
| Prometheum | `prometheum` | Mythic Metals `mythicmetals` | every stone |
| Runite | `runite` | Mythic Metals `mythicmetals` | every stone |
| Unobtainium | `unobtainium` | Mythic Metals `mythicmetals` | every stone |
| Aquarium | `aquarium` | Mythic Metals `mythicmetals` | Limestone, Marble |
| Banglum | `banglum` | Mythic Metals `mythicmetals` | Limestone, Marble |
| Kyber | `kyber` | Mythic Metals `mythicmetals` | Limestone, Marble |
| Manganese | `manganese` | Mythic Metals `mythicmetals` | Limestone, Marble |
| Quadrillum | `quadrillum` | Mythic Metals `mythicmetals` | Limestone, Marble |
| Silver | `silver` | Mythic Metals `mythicmetals` | Limestone, Marble |
| Starrite | `starrite` | Mythic Metals `mythicmetals` | Limestone |
| Tin | `tin` | Mythic Metals `mythicmetals` | Limestone, Marble |
| Orichalcum | `orichalcum` | Mythic Metals `mythicmetals` | every stone |
| Tin | `energized_tin` | Energized Power `energizedpower` | Limestone, Marble |
| Bauxite | `techreborn_bauxite` | Tech Reborn `techreborn` | every stone |
| Galena | `galena` | Tech Reborn `techreborn` | Limestone, Marble, Viridite |
| Iridium | `iridium` | Tech Reborn `techreborn` | Bluestone, Viridite |
| Lead | `techreborn_lead` | Tech Reborn `techreborn` | Limestone, Marble, Viridite |
| Ruby | `techreborn_ruby` | Tech Reborn `techreborn` | Marble |
| Sapphire | `techreborn_sapphire` | Tech Reborn `techreborn` | Marble |
| Silver | `techreborn_silver` | Tech Reborn `techreborn` | every stone |
| Tin | `techreborn_tin` | Tech Reborn `techreborn` | Limestone, Marble |
| Uranium | `techreborn_uranium` | Tech Reborn `techreborn` | Limestone, Marble, Viridite |

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
| Redstone | `redstone` |  | Asurine, Crimsite, Limestone, Ochrum, Scoria, Veridium, Calcite, Smooth Basalt |
| Nether Gold | `nether_gold` |  | Scorchia, Scoria, Smooth Basalt |
| Quartz | `quartz` |  | Scorchia, Scoria, Smooth Basalt |
| Zinc | `zinc` |  | Asurine, Limestone, Scoria, Calcite, Smooth Basalt |
| Citrine | `citrine` | Mythic Upgrades `mythicupgrades` | Limestone, Scoria, Calcite, Smooth Basalt |
| Peridot | `peridot` | Mythic Upgrades `mythicupgrades` | Scoria, Smooth Basalt |
| Necoium | `necoium` | Mythic Upgrades `mythicupgrades` | Asurine, Crimsite, Limestone, Ochrum, Scoria, Veridium, Calcite, Smooth Basalt |
| Ruby | `ruby` | Mythic Upgrades `mythicupgrades` | Scorchia, Scoria, Smooth Basalt |
| Sapphire | `sapphire` | Mythic Upgrades `mythicupgrades` | Scorchia, Scoria, Smooth Basalt |
| Adamantite | `adamantite` | Mythic Metals `mythicmetals` | Asurine, Crimsite, Limestone, Ochrum, Scoria, Veridium, Calcite, Smooth Basalt |
| Carmot | `carmot` | Mythic Metals `mythicmetals` | Asurine, Crimsite, Limestone, Ochrum, Scoria, Veridium, Calcite, Smooth Basalt |
| Morkite | `morkite` | Mythic Metals `mythicmetals` | Asurine, Crimsite, Limestone, Ochrum, Scoria, Veridium, Calcite, Smooth Basalt |
| Mythril | `mythril` | Mythic Metals `mythicmetals` | Asurine, Crimsite, Limestone, Ochrum, Scoria, Veridium, Calcite, Smooth Basalt |
| Prometheum | `prometheum` | Mythic Metals `mythicmetals` | Asurine, Crimsite, Limestone, Ochrum, Scoria, Veridium, Calcite, Smooth Basalt |
| Runite | `runite` | Mythic Metals `mythicmetals` | Asurine, Crimsite, Limestone, Ochrum, Scoria, Veridium, Calcite, Smooth Basalt |
| Unobtainium | `unobtainium` | Mythic Metals `mythicmetals` | Asurine, Crimsite, Limestone, Ochrum, Scoria, Veridium, Calcite, Smooth Basalt |
| Aquarium | `aquarium` | Mythic Metals `mythicmetals` | Asurine, Crimsite, Limestone, Ochrum, Scoria, Veridium, Calcite, Smooth Basalt |
| Banglum | `banglum` | Mythic Metals `mythicmetals` | Asurine, Crimsite, Limestone, Ochrum, Scoria, Veridium, Calcite, Smooth Basalt |
| Kyber | `kyber` | Mythic Metals `mythicmetals` | Asurine, Crimsite, Limestone, Ochrum, Scoria, Veridium, Calcite, Smooth Basalt |
| Manganese | `manganese` | Mythic Metals `mythicmetals` | Limestone, Scoria, Calcite, Smooth Basalt |
| Quadrillum | `quadrillum` | Mythic Metals `mythicmetals` | Asurine, Crimsite, Limestone, Ochrum, Scoria, Veridium, Calcite, Smooth Basalt |
| Silver | `silver` | Mythic Metals `mythicmetals` | Limestone, Scoria, Calcite, Smooth Basalt |
| Tin | `tin` | Mythic Metals `mythicmetals` | Limestone |
| Orichalcum | `orichalcum` | Mythic Metals `mythicmetals` | Asurine, Crimsite, Limestone, Ochrum, Scoria, Veridium, Calcite, Smooth Basalt |
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

**Forbidden and Arcanus, requires `forbidden_arcanus`** (NeoForge, 26.1.2)

Stones: Darkstone `forbidden_arcanus_darkstone`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Iron | `iron` |  | Darkstone |
| Gold | `gold` |  | Darkstone |
| Lapis Lazuli | `lapis` |  | Darkstone |
| Diamond | `diamond` |  | Darkstone |
| Redstone | `redstone` |  | Darkstone |
| Alexandrite | `alexandrite` | Silent's Gems `silentgems` | Darkstone |
| Chaos | `chaos` | Silent's Gems `silentgems` | Darkstone |
| Garnet | `garnet` | Silent's Gems `silentgems` | Darkstone |
| Heliodor | `heliodor` | Silent's Gems `silentgems` | Darkstone |
| Iolite | `iolite` | Silent's Gems `silentgems` | Darkstone |
| Ruby | `silents_ruby` | Silent's Gems `silentgems` | Darkstone |
| Sapphire | `silents_sapphire` | Silent's Gems `silentgems` | Darkstone |
| Turquoise | `turquoise` | Silent's Gems `silentgems` | Darkstone |
| Aquamarine | `silents_aquamarine` | Silent's Gems `silentgems` | Darkstone |
| Peridot | `silents_peridot` | Silent's Gems `silentgems` | Darkstone |
| Topaz | `silents_topaz` | Silent's Gems `silentgems` | Darkstone |
| Silver | `silents_silver` | Silent's Gems `silentgems` | Darkstone |
| Uraninite | `uraninite` | Powah `powah` | Darkstone |
| Uraninite Poor | `uraninite_poor` | Powah `powah` | Darkstone |
| Uraninite Dense | `uraninite_dense` | Powah `powah` | Darkstone |
| Bort | `bort` | Silent Gear `silentgear` | Darkstone |
| Silver | `occultism_silver` | Occultism `occultism` | Darkstone |
| Prosperity | `prosperity` | Mystical Agriculture `mysticalagriculture` | Darkstone |
| Opal | `opal` | Silent's Gems `silentgems` | Darkstone |

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
| Redstone | `redstone` |  | Argillite |
| Zinc | `zinc` | Create `create` | Mossy Stone, Argillite |
| Morkite | `morkite` | Mythic Metals `mythicmetals` | Argillite |
| Prometheum | `prometheum` | Mythic Metals `mythicmetals` | Argillite |
| Aquarium | `aquarium` | Mythic Metals `mythicmetals` | Mossy Stone, Argillite |
| Banglum | `banglum` | Mythic Metals `mythicmetals` | Mossy Stone |
| Manganese | `manganese` | Mythic Metals `mythicmetals` | Argillite |
| Osmium | `osmium` | Mythic Metals `mythicmetals` | Mossy Stone |
| Quadrillum | `quadrillum` | Mythic Metals `mythicmetals` | Argillite |
| Silver | `silver` | Mythic Metals `mythicmetals` | Argillite |
| Starrite | `starrite` | Mythic Metals `mythicmetals` | Mossy Stone, Chalk |
| Tin | `tin` | Mythic Metals `mythicmetals` | Mossy Stone, Chalk |
| Chaos | `chaos` | Silent's Gems `silentgems` | Argillite |
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
| Iceandfire Sapphire | `iceandfire_sapphire` | Ice and Fire `iceandfire` | Mossy Stone |
| Iceandfire Silver | `iceandfire_silver` | Ice and Fire `iceandfire` | every stone |
| Inferium | `inferium` | Mystical Agriculture `mysticalagriculture` | Mossy Stone, Argillite |
| Prosperity | `prosperity` | Mystical Agriculture `mysticalagriculture` | Argillite |

**Promenade, requires `promenade`** (Fabric on every 26.x version, NeoForge on 26.3)

Stones: Asphalt `promenade_asphalt`, Blunite `promenade_blunite`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Coal | `coal` |  | every stone |
| Iron | `iron` |  | every stone |
| Copper | `copper` |  | every stone |
| Gold | `gold` |  | every stone |
| Lapis Lazuli | `lapis` |  | Blunite |
| Diamond | `diamond` |  | Blunite |
| Emerald | `emerald` |  | Blunite |
| Redstone | `redstone` |  | every stone |
| Zinc | `zinc` | Create `create` | every stone |
| Aquamarine | `aquamarine` | Mythic Upgrades `mythicupgrades` | Blunite |
| Citrine | `citrine` | Mythic Upgrades `mythicupgrades` | every stone |
| Peridot | `peridot` | Mythic Upgrades `mythicupgrades` | Blunite |
| Topaz | `topaz` | Mythic Upgrades `mythicupgrades` | Blunite |
| Necoium | `necoium` | Mythic Upgrades `mythicupgrades` | every stone |
| Carmot | `carmot` | Mythic Metals `mythicmetals` | every stone |
| Morkite | `morkite` | Mythic Metals `mythicmetals` | every stone |
| Mythril | `mythril` | Mythic Metals `mythicmetals` | every stone |
| Prometheum | `prometheum` | Mythic Metals `mythicmetals` | every stone |
| Runite | `runite` | Mythic Metals `mythicmetals` | every stone |
| Unobtainium | `unobtainium` | Mythic Metals `mythicmetals` | every stone |
| Aquarium | `aquarium` | Mythic Metals `mythicmetals` | every stone |
| Banglum | `banglum` | Mythic Metals `mythicmetals` | every stone |
| Kyber | `kyber` | Mythic Metals `mythicmetals` | every stone |
| Manganese | `manganese` | Mythic Metals `mythicmetals` | every stone |
| Osmium | `osmium` | Mythic Metals `mythicmetals` | Blunite |
| Platinum | `platinum` | Mythic Metals `mythicmetals` | Blunite |
| Quadrillum | `quadrillum` | Mythic Metals `mythicmetals` | every stone |
| Silver | `silver` | Mythic Metals `mythicmetals` | every stone |
| Starrite | `starrite` | Mythic Metals `mythicmetals` | every stone |
| Tin | `tin` | Mythic Metals `mythicmetals` | Blunite |
| Orichalcum | `orichalcum` | Mythic Metals `mythicmetals` | every stone |
| Tin | `energized_tin` | Energized Power `energizedpower` | Blunite |
| Bauxite | `techreborn_bauxite` | Tech Reborn `techreborn` | every stone |
| Galena | `galena` | Tech Reborn `techreborn` | every stone |
| Iridium | `iridium` | Tech Reborn `techreborn` | Blunite |
| Lead | `techreborn_lead` | Tech Reborn `techreborn` | every stone |
| Ruby | `techreborn_ruby` | Tech Reborn `techreborn` | Blunite |
| Sapphire | `techreborn_sapphire` | Tech Reborn `techreborn` | Blunite |
| Silver | `techreborn_silver` | Tech Reborn `techreborn` | every stone |
| Tin | `techreborn_tin` | Tech Reborn `techreborn` | Blunite |
| Uranium | `techreborn_uranium` | Tech Reborn `techreborn` | every stone |
| Silver | `occultism_silver` | Occultism `occultism` | every stone |

**Wilder Wild, requires `wilderwild`** (Fabric 26.1.x to 26.3, NeoForge 26.2 and 26.3)

Stones: Gabbro `wilderwild_gabbro`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Iron | `iron` |  | Gabbro |
| Copper | `copper` |  | Gabbro |
| Gold | `gold` |  | Gabbro |
| Redstone | `redstone` |  | Gabbro |
| Necoium | `necoium` | Mythic Upgrades `mythicupgrades` | Gabbro |
| Adamantite | `adamantite` | Mythic Metals `mythicmetals` | Gabbro |
| Carmot | `carmot` | Mythic Metals `mythicmetals` | Gabbro |
| Morkite | `morkite` | Mythic Metals `mythicmetals` | Gabbro |
| Mythril | `mythril` | Mythic Metals `mythicmetals` | Gabbro |
| Prometheum | `prometheum` | Mythic Metals `mythicmetals` | Gabbro |
| Runite | `runite` | Mythic Metals `mythicmetals` | Gabbro |
| Unobtainium | `unobtainium` | Mythic Metals `mythicmetals` | Gabbro |
| Aquarium | `aquarium` | Mythic Metals `mythicmetals` | Gabbro |
| Banglum | `banglum` | Mythic Metals `mythicmetals` | Gabbro |
| Kyber | `kyber` | Mythic Metals `mythicmetals` | Gabbro |
| Osmium | `osmium` | Mythic Metals `mythicmetals` | Gabbro |
| Platinum | `platinum` | Mythic Metals `mythicmetals` | Gabbro |
| Quadrillum | `quadrillum` | Mythic Metals `mythicmetals` | Gabbro |
| Silver | `silver` | Mythic Metals `mythicmetals` | Gabbro |
| Orichalcum | `orichalcum` | Mythic Metals `mythicmetals` | Gabbro |
| Bauxite | `techreborn_bauxite` | Tech Reborn `techreborn` | Gabbro |
| Iridium | `iridium` | Tech Reborn `techreborn` | Gabbro |
| Silver | `techreborn_silver` | Tech Reborn `techreborn` | Gabbro |
| Silver | `occultism_silver` | Occultism `occultism` | Gabbro |
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
Every variant of one ore shares a single overlay texture, so covering all 819 blocks takes **91 PNG files**:

```
assets/seamlessores/textures/block/<ore>_overlay.png
```

where `<ore>` is one of:

`adamantite` `alexandrite` `ametrine` `aquamarine` `aquarium` `banglum` `black_diamond` `bort` `carmot` `carnelian` `chaos` `cinnabar` `citrine` `coal` `copper` `dense_fluorite` `dense_lead` `dense_tin` `dense_uranium` `diamond` `emerald` `energized_tin` `galena` `garnet` `gleaming` `gold` `heliodor` `iceandfire_deepslate_silver` `iceandfire_sapphire` `iceandfire_silver` `inferium` `iolite` `iridium` `iron` `kyber` `lapis` `lead` `lithium` `manganese` `midas_gold` `morkite` `mythril` `necoium` `nether_banglum` `nether_gold` `occultism_silver` `opal_darkstone` `opal_tuff` `orichalcum` `osmium` `palladium` `peridot` `platinum` `prometheum` `prosperity` `pyrite` `quadrillum` `quartz` `redstone` `ruby` `runite` `sapphire` `silents_aquamarine` `silents_citrine` `silents_peridot` `silents_ruby` `silents_sapphire` `silents_silver` `silents_topaz` `silver` `sphalerite` `starrite` `stormyx` `techreborn_bauxite` `techreborn_lead` `techreborn_ruby` `techreborn_sapphire` `techreborn_silver` `techreborn_tin` `techreborn_uranium` `thorium` `tin` `topaz` `turquoise` `unobtainium` `unobtainium_deepslate` `uraninite` `uraninite_dense` `uraninite_poor` `white_diamond` `zinc`
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
<!-- END GENERATED credits -->

Built on [MultiLoader Template](https://github.com/jaredlll08/MultiLoader-Template) by jaredlll08.
