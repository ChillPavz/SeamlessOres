package com.chillpavz.seamlessores.worldgen;

import com.chillpavz.seamlessores.Constants;
import com.chillpavz.seamlessores.SeamlessOresConfig;
import com.chillpavz.seamlessores.content.HostStone;
import com.chillpavz.seamlessores.content.OreType;
import com.chillpavz.seamlessores.content.OreVariant;
import com.chillpavz.seamlessores.content.SeamlessOresContent;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.OreVeinifier;

/**
 * Fixes the ore that {@link OreVeinifier} places in the large copper and iron veins.
 *
 * <h2>Why this exists as a separate thing from {@link OreTargetInjector}</h2>
 * There are <b>two</b> ore systems in Minecraft, not one. Configured features are the familiar one.
 * The other is {@code OreVeinifier}, which builds the big copper and iron veins during <i>noise</i>
 * generation, before any feature runs, and which is not registered anywhere - so patching the
 * CONFIGURED_FEATURE registry cannot reach it. It is hardcoded as an enum:
 *
 * <pre>
 *   COPPER(copper_ore,           raw_copper_block, GRANITE, y   0 .. 50)
 *   IRON  (deepslate_iron_ore,   raw_iron_block,   TUFF,    y -60 .. -8)
 * </pre>
 *
 * The third value is the <b>filler</b> - the stone the vein is packed with. So vanilla itself builds
 * "copper ore embedded in granite" and "deepslate-textured iron ore embedded in tuff". Those are the
 * two most visible mismatches in the entire game, they are large and dense, and before this fix the
 * mod missed both of them entirely.
 *
 * <h2>Balance</h2>
 * Unchanged, exactly. This swaps which block state is placed at positions that were already going to
 * be ore. No position, count or vein shape is touched.
 *
 * <h2>Why a field write rather than a mixin</h2>
 * The alternative is mixing into the lambda inside {@code OreVeinifier.create}, which depends on how
 * that lambda happens to be compiled. Reassigning the enum field is stable and readable. The field is
 * private final, so it is opened by the access widener / access transformer.
 *
 * <p>Note this is global process state rather than per-world, which is fine because the registered
 * block set is itself fixed for the session. The method is idempotent.
 */
public final class VeinOreInjector {

    private VeinOreInjector() {}

    public static void inject() {

        if (!SeamlessOresConfig.oreVeins) {
            return;
        }
        // The vein's filler stone decides the host: the ore sits inside granite in a copper vein and
        // inside tuff in an iron vein, so those are the variants that make it seamless.
        patch(OreVeinifier.VeinType.COPPER, HostStone.GRANITE, OreType.COPPER, Blocks.COPPER_ORE);
        patch(OreVeinifier.VeinType.IRON, HostStone.TUFF, OreType.IRON, Blocks.DEEPSLATE_IRON_ORE);
    }

    private static void patch(OreVeinifier.VeinType vein, HostStone host, OreType ore, Block expectedVanilla) {

        final Block ours = SeamlessOresContent.blocks().get(new OreVariant(host, ore));
        if (ours == null) {
            Constants.LOG.warn("No registered variant for {} {} - vein ore left vanilla", host.name(), ore.name());
            return;
        }

        final Block current = vein.ore.getBlock();
        if (current == ours) {
            return;   // already patched this session
        }
        if (current != expectedVanilla) {
            // Something else got here first. Leave it alone rather than stomping another mod.
            Constants.LOG.warn("{} vein ore is {}, expected {} - leaving it alone",
                    vein, current, expectedVanilla);
            return;
        }

        vein.ore = ours.defaultBlockState();
        Constants.LOG.info("Worldgen: {} vein ore -> {}", vein, ours.defaultBlockState().getBlock());
    }
}
