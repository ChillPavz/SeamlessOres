# Seamless Ores

Ore blocks whose background matches the stone they generate in. Granite, diorite, andesite and tuff
variants for every overworld ore, basalt and blackstone in the Nether, and the same treatment for the
ores of eleven other mods.

**In the Overworld it adds no ore.** The same veins, in the same places, drawn to fit their
surroundings. The Nether variants are the one exception, and they are config gated.

| | |
|---|---|
| Minecraft | 1.21.11 |
| Loaders | Fabric, NeoForge, Forge, Quilt (untested) |
| Wiki | https://chillpavz.com/seamless-ores |
| Licence | PolyForm Shield 1.0.0, see `LICENSE` |

An original mod. Not a fork or a port of any other project.

Forge players need Cloth Config's unofficial Forge port, `cloth-config-forge`, because official
Cloth Config ships no Forge build at this Minecraft version. It carries the same mod id and the
same version number, so the config screen is identical on all three loaders.

Most of the third-party mods below skipped this Minecraft version, so their variants are inert
here until such a build appears. The block table further down lists, per loader, which of them a
player can actually see.

## Companion resource pack

**Seamless Glowing Ores** makes every ore glow, with an optional connected outline that joins
touching ore of the same type across different host stones.

## Block list

<!-- BEGIN GENERATED block-list -->
**209 blocks** in the game's own rock, in the `seamlessores` namespace.

**Vanilla, Overworld**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Coal | `granite_coal_ore` | `diorite_coal_ore` | `andesite_coal_ore` | `tuff_coal_ore` | `dripstone_coal_ore` |
| Iron | `granite_iron_ore` | `diorite_iron_ore` | `andesite_iron_ore` | `tuff_iron_ore` | `dripstone_iron_ore` |
| Copper | `granite_copper_ore` | `diorite_copper_ore` | `andesite_copper_ore` | `tuff_copper_ore` | `dripstone_copper_ore` |
| Gold | `granite_gold_ore` | `diorite_gold_ore` | `andesite_gold_ore` | `tuff_gold_ore` | `dripstone_gold_ore` |
| Lapis Lazuli | `granite_lapis_ore` | `diorite_lapis_ore` | `andesite_lapis_ore` | `tuff_lapis_ore` | `dripstone_lapis_ore` |
| Diamond | `granite_diamond_ore` | `diorite_diamond_ore` | `andesite_diamond_ore` | `tuff_diamond_ore` | `dripstone_diamond_ore` |
| Emerald | `granite_emerald_ore` | `diorite_emerald_ore` | `andesite_emerald_ore` | `tuff_emerald_ore` |   |
| Redstone | `granite_redstone_ore` | `diorite_redstone_ore` | `andesite_redstone_ore` | `tuff_redstone_ore` | `dripstone_redstone_ore` |

**Vanilla, Nether**

| | basalt | blackstone |
|---|---|---|
| Gold | `basalt_nether_gold_ore` | `blackstone_nether_gold_ore` |
| Quartz | `basalt_nether_quartz_ore` | `blackstone_nether_quartz_ore` |

**Create, Overworld, requires `create`**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Zinc | `granite_create_zinc_ore` | `diorite_create_zinc_ore` | `andesite_create_zinc_ore` | `tuff_create_zinc_ore` | `dripstone_create_zinc_ore` |

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
| Adamantite | `granite_mythicmetals_adamantite_ore` | `diorite_mythicmetals_adamantite_ore` | `andesite_mythicmetals_adamantite_ore` | `tuff_mythicmetals_adamantite_ore` | `dripstone_mythicmetals_adamantite_ore` |
| Carmot | `granite_mythicmetals_carmot_ore` | `diorite_mythicmetals_carmot_ore` | `andesite_mythicmetals_carmot_ore` | `tuff_mythicmetals_carmot_ore` | `dripstone_mythicmetals_carmot_ore` |
| Morkite | `granite_mythicmetals_morkite_ore` | `diorite_mythicmetals_morkite_ore` | `andesite_mythicmetals_morkite_ore` | `tuff_mythicmetals_morkite_ore` | `dripstone_mythicmetals_morkite_ore` |
| Mythril | `granite_mythicmetals_mythril_ore` | `diorite_mythicmetals_mythril_ore` | `andesite_mythicmetals_mythril_ore` | `tuff_mythicmetals_mythril_ore` | `dripstone_mythicmetals_mythril_ore` |
| Prometheum | `granite_mythicmetals_prometheum_ore` | `diorite_mythicmetals_prometheum_ore` | `andesite_mythicmetals_prometheum_ore` | `tuff_mythicmetals_prometheum_ore` | `dripstone_mythicmetals_prometheum_ore` |
| Runite | `granite_mythicmetals_runite_ore` | `diorite_mythicmetals_runite_ore` | `andesite_mythicmetals_runite_ore` | `tuff_mythicmetals_runite_ore` | `dripstone_mythicmetals_runite_ore` |
| Unobtainium | `granite_mythicmetals_unobtainium_ore` | `diorite_mythicmetals_unobtainium_ore` | `andesite_mythicmetals_unobtainium_ore` | `tuff_mythicmetals_unobtainium_ore` | `dripstone_mythicmetals_unobtainium_ore` |
| Aquarium | `granite_mythicmetals_aquarium_ore` | `diorite_mythicmetals_aquarium_ore` | `andesite_mythicmetals_aquarium_ore` |   | `dripstone_mythicmetals_aquarium_ore` |
| Banglum | `granite_mythicmetals_banglum_ore` | `diorite_mythicmetals_banglum_ore` | `andesite_mythicmetals_banglum_ore` |   | `dripstone_mythicmetals_banglum_ore` |
| Kyber | `granite_mythicmetals_kyber_ore` | `diorite_mythicmetals_kyber_ore` | `andesite_mythicmetals_kyber_ore` |   | `dripstone_mythicmetals_kyber_ore` |
| Manganese | `granite_mythicmetals_manganese_ore` | `diorite_mythicmetals_manganese_ore` | `andesite_mythicmetals_manganese_ore` |   | `dripstone_mythicmetals_manganese_ore` |
| Quadrillum | `granite_mythicmetals_quadrillum_ore` | `diorite_mythicmetals_quadrillum_ore` | `andesite_mythicmetals_quadrillum_ore` |   | `dripstone_mythicmetals_quadrillum_ore` |
| Silver | `granite_mythicmetals_silver_ore` | `diorite_mythicmetals_silver_ore` | `andesite_mythicmetals_silver_ore` |   |   |
| Starrite | `granite_mythicmetals_starrite_ore` | `diorite_mythicmetals_starrite_ore` | `andesite_mythicmetals_starrite_ore` |   | `dripstone_mythicmetals_starrite_ore` |
| Tin | `granite_mythicmetals_tin_ore` |   |   |   |   |
| Orichalcum | `granite_mythicmetals_orichalcum_ore` | `diorite_mythicmetals_orichalcum_ore` | `andesite_mythicmetals_orichalcum_ore` |   | `dripstone_mythicmetals_orichalcum_ore` |

**Mythic Metals, Nether, requires `mythicmetals`**

| | basalt | blackstone |
|---|---|---|
| Banglum | `basalt_mythicmetals_nether_banglum_ore` | `blackstone_mythicmetals_nether_banglum_ore` |
| Midas Gold | `basalt_mythicmetals_midas_gold_ore` | `blackstone_mythicmetals_midas_gold_ore` |
| Palladium | `basalt_mythicmetals_palladium_ore` | `blackstone_mythicmetals_palladium_ore` |
| Stormyx | `basalt_mythicmetals_stormyx_ore` |   |

**Mythic Upgrades, Overworld, requires `mythicupgrades`**

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Aquamarine | `granite_mythicupgrades_aquamarine_ore` |   |   |   |   |
| Citrine | `granite_mythicupgrades_citrine_ore` | `diorite_mythicupgrades_citrine_ore` | `andesite_mythicupgrades_citrine_ore` | `tuff_mythicupgrades_citrine_ore` |   |
| Topaz | `granite_mythicupgrades_topaz_ore` |   |   |   |   |
| Necoium | `granite_mythicupgrades_necoium_ore` | `diorite_mythicupgrades_necoium_ore` | `andesite_mythicupgrades_necoium_ore` | `tuff_mythicupgrades_necoium_ore` | `dripstone_mythicupgrades_necoium_ore` |

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

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Chaos | `granite_silentgems_chaos_ore` | `diorite_silentgems_chaos_ore` | `andesite_silentgems_chaos_ore` | `tuff_silentgems_chaos_ore` | `dripstone_silentgems_chaos_ore` |
| Garnet | `granite_silentgems_garnet_ore` |   |   |   |   |
| Heliodor | `granite_silentgems_heliodor_ore` |   |   |   |   |
| Aquamarine | `granite_silentgems_aquamarine_ore` |   |   |   |   |
| Citrine | `granite_silentgems_citrine_ore` | `diorite_silentgems_citrine_ore` | `andesite_silentgems_citrine_ore` | `tuff_silentgems_citrine_ore` |   |
| Topaz | `granite_silentgems_topaz_ore` |   |   |   |   |
| Silver | `granite_silentgems_silver_ore` | `diorite_silentgems_silver_ore` | `andesite_silentgems_silver_ore` | `tuff_silentgems_silver_ore` |   |
| Carnelian |   |   | `andesite_silentgems_carnelian_ore` | `tuff_silentgems_carnelian_ore` |   |
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

| | granite | diorite | andesite | tuff | dripstone |
|---|---|---|---|---|---|
| Gleaming | `granite_things_gleaming_ore` | `diorite_things_gleaming_ore` | `andesite_things_gleaming_ore` | `tuff_things_gleaming_ore` | `dripstone_things_gleaming_ore` |

A variant is registered only when the mod that owns its ore is installed, so how many of
these you can actually see depends on which mods have a build for your loader at this
Minecraft version:

| Loader | Blocks | Supported mods available here |
|---|---|---|
| Fabric | 49 | Create, Energized Power |
| NeoForge | 73 | Energized Power, Silent Gear, Silent's Gems |
| Forge | 43 | none at this Minecraft version |

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
ores and swallow them. These blocks give that ore the look of the stone around it.

An ore that could never form in a stone (coal in marble, diamond in limestone) gets no block there:
that ore becomes the stone instead, so no seam is left. Create's asurine, crimsite, ochrum and
veridium each keep only the ore Create ties them to.

<!-- BEGIN GENERATED modded-stone-list -->
**377 blocks**, plus the dripstone ones listed above. Each exists only when the mod that places its stone is installed, and one of another mod's ore only with that mod as well. A block's id is `<stone>_<ore>_ore`, from the two columns below: `blockus_limestone` and `iron` make `blockus_limestone_iron_ore`.

**Terralith** (its mod or datapack, Fabric, NeoForge and Forge)

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
| Dense Lead | `dense_lead` | Dense Mekanism `densemekanism` | Deep Blackstone |
| Lead | `lead` | Create: TFMG `tfmg` | Deep Blackstone |
| Gleaming | `gleaming` | Things `things` | Deep Blackstone |

**Blockus, requires `blockus`** (Fabric)

Stones: Limestone `blockus_limestone`, Marble `blockus_marble`, Bluestone `blockus_bluestone`, Viridite `blockus_viridite`

| Ore | `<ore>` | Also requires | In |
|---|---|---|---|
| Coal | `coal` |  | Limestone |
| Iron | `iron` |  | every stone |
| Copper | `copper` |  | every stone |
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
| Gleaming | `gleaming` | Things `things` | every stone |

**Create, requires `create`** (Create Fly, Fabric)

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
| Gleaming | `gleaming` | Things `things` | Asurine, Crimsite, Limestone, Ochrum, Scoria, Veridium, Calcite, Smooth Basalt |

**Promenade, requires `promenade`** (Fabric)

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
| Gleaming | `gleaming` | Things `things` | every stone |

**Wilder Wild, requires `wilderwild`** (Fabric)

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
| Gleaming | `gleaming` | Things `things` | Gabbro |
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
Every variant of one ore shares a single overlay texture, so covering all 586 blocks takes **69 PNG files**:

```
assets/seamlessores/textures/block/<ore>_overlay.png
```

where `<ore>` is one of:

`adamantite` `aquamarine` `aquarium` `banglum` `black_diamond` `bort` `carmot` `carnelian` `chaos` `citrine` `coal` `copper` `dense_fluorite` `dense_lead` `dense_tin` `dense_uranium` `diamond` `emerald` `energized_tin` `garnet` `gleaming` `gold` `heliodor` `iron` `kyber` `lapis` `lead` `lithium` `manganese` `midas_gold` `morkite` `mythril` `necoium` `nether_banglum` `nether_gold` `opal_tuff` `orichalcum` `osmium` `palladium` `peridot` `platinum` `prometheum` `quadrillum` `quartz` `redstone` `ruby` `runite` `sapphire` `silents_aquamarine` `silents_citrine` `silents_peridot` `silents_ruby` `silents_sapphire` `silents_silver` `silents_topaz` `silver` `starrite` `stormyx` `thorium` `tin` `topaz` `turquoise` `unobtainium` `unobtainium_deepslate` `uraninite` `uraninite_dense` `uraninite_poor` `white_diamond` `zinc`
<!-- END GENERATED overlay-list -->

Each file is the ore layer only, blobs on transparency. The host stone is the vanilla texture at its
usual path, so you do not supply it. A pack that replaces that texture restyles the stone of these
blocks too.

## Building

Requires JDK 24. Gradle 8.14.3 and ForgeGradle 6 cannot run on a newer one.

```
./gradlew build
```

Jars land in `fabric/build/libs`, `neoforge/build/libs` and `forge/build/libs`. Take the plain jar,
not the `-sources` or `-javadoc` one. Fabric Loader rejects the sources jar, because its metadata
still holds unexpanded build placeholders.

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
| `fabric/`, `neoforge/`, `forge/` | Loader entry points, the Cloth Config data class and screen |
| `tools/generate_assets.py` | Generates blockstates, models, lang, loot tables, tags and the block list above |

The Cloth Config classes are duplicated across the three loader modules on purpose and must stay
identical. They cannot live in `common`, because loader dependencies are not on its classpath.

## How it works, briefly

Seamless Ores does not add worldgen features. At server start it extends the target lists of the ore
features that already exist, adding one entry per host stone ahead of vanilla's. The game then picks
the ore texture from the block that was actually at each position, which is why distribution is
unchanged and why veins blend across a stone boundary by themselves.

Patching the live registry rather than shipping replacement JSON files is deliberate: it composes
with worldgen overhauls and ore datapacks instead of overwriting them.

The exceptions, all config gated and all stated on the store page: basalt and blackstone gold and
quartz add ore, because vanilla's Nether features match netherrack only; Silent's Gems' nether gems
do the same, because that mod targets netherrack only as well; and Mythic Upgrades' ruby and sapphire
in basalt deltas are placed by a feature this mod adds, because Mythic Upgrades restricts its own ore
to a single biome and there was nothing to extend.

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
<!-- END GENERATED credits -->

Built on [MultiLoader Template](https://github.com/jaredlll08/MultiLoader-Template) by jaredlll08.
