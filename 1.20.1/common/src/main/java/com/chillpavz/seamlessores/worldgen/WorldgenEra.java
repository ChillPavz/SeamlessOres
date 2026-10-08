package com.chillpavz.seamlessores.worldgen;

import net.minecraft.core.RegistryAccess;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.structure.templatesystem.RuleTest;

import java.util.List;

/**
 * The worldgen code whose Minecraft API differs from band to band, behind one interface, so the two
 * injectors are the same file on every band. Each band has its own {@code BandWorldgen}.
 */
public interface WorldgenEra {

    /** Every ore site, freshly read: an injector may have rebound some since the last call. */
    List<OreSite> oreSites(RegistryAccess registries);

    /**
     * Whether the ore side should add "this stone" next to {@code original}. These versions have no
     * all-of rule test, so the added target is a bare block match on the stone, which is only right where
     * the original target would have matched that stone anyway.
     */
    boolean receives(RuleTest original, Block stone);
}
