package com.chillpavz.seamlessores.matrix.worldgen;

import com.chillpavz.seamlessores.Constants;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.levelgen.structure.templatesystem.RuleTest;

import java.util.List;
import java.util.Map;

/**
 * The ore sites of the Minecraft that is running.
 *
 * <p>Where an ore feature keeps its targets changed shape at 26.3, so each shape has a class of its own,
 * compiled against its own version: {@code Era261} for 26.1.x and 26.2, {@code Era263} for 26.3. One
 * jar carries both. Neither is named here, so neither is linked: the one that matches is loaded by name,
 * and the other, which names classes this game does not have, is never touched.
 */
final class OreSites {

    private OreSites() {}

    /** One era's way of finding and rebuilding ore features. */
    interface Era {

        /** Every ore site, freshly read: the other injector may have rebound some since the last call. */
        List<OreSite> find(RegistryAccess registries);

        /** Whether the ore side should add "this stone" next to {@code original}. */
        boolean receives(RuleTest original, Block stone);
    }

    /** Null when neither era could be loaded; the injectors then find no sites and do nothing. */
    private static final Era ERA = load();

    private static Era load() {
        // The configured feature registry is what 26.3 removed; its presence is the era.
        boolean configured;
        try {
            Registries.class.getField("CONFIGURED_FEATURE");
            configured = true;
        } catch (NoSuchFieldException e) {
            configured = false;
        }
        final String name = configured ? "Era261" : "Era263";
        try {
            final Era era = (Era) Class.forName(OreSites.class.getPackageName() + "." + name)
                    .getDeclaredConstructor().newInstance();
            Constants.LOG.info("Ore sites: {} ({})", name, configured ? "configured features" : "features");
            return era;
        } catch (ReflectiveOperationException | LinkageError | ClassCastException e) {
            Constants.LOG.error("Could not load the ore sites for this Minecraft ({}); ore keeps its usual"
                    + " look in every stone this session", name, e);
            return null;
        }
    }

    static List<OreSite> find(RegistryAccess registries) {
        return ERA == null ? List.of() : ERA.find(registries);
    }

    static boolean receives(RuleTest original, Block stone) {
        return ERA != null && ERA.receives(original, stone);
    }

    static boolean placesAny(List<OreSite.Target> targets, Map<Block, ?> blocks) {
        for (OreSite.Target target : targets) {
            if (blocks.containsKey(target.state().getBlock())) {
                return true;
            }
        }
        return false;
    }
}
