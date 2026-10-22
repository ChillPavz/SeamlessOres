package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.Constants;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.DropExperienceBlock;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Reports, once per game, every variant whose hardness, blast resistance or experience differs from the
 * ore it stands in for.
 *
 * <p>Those values are fixed when our blocks are built (from the game's ore, or from the ore mod's jar
 * when the generator ran), because a modded source block may not be registered before ours. So a mod
 * update or a modpack script that changes an ore leaves our variant on the old values, and nothing else
 * would say so. This only looks and logs: it changes nothing, and a variant whose source is absent is
 * skipped.
 *
 * <p>Experience is read from {@link DropExperienceBlock}'s range by its TYPE, not its name: the field is
 * private and named differently under each loader's mappings.
 */
public final class SourceDrift {

    private static final int SHOWN = 12;
    private static boolean checked;

    private SourceDrift() {
    }

    public static void check() {
        if (checked) {
            return;
        }
        checked = true;
        final Field xp = xpField();
        final List<String> drifted = new ArrayList<>();
        int compared = 0;
        for (Map.Entry<OreVariant, Block> entry : SeamlessOresContent.blocks().entrySet()) {
            final Block ours = entry.getValue();
            final Block source = BuiltInRegistries.BLOCK.getOptional(entry.getKey().source()).orElse(null);
            if (source == null) {
                continue;
            }
            compared++;
            final List<String> differences = new ArrayList<>();
            if (ours.defaultDestroyTime() != source.defaultDestroyTime()) {
                differences.add("hardness " + ours.defaultDestroyTime() + " vs " + source.defaultDestroyTime());
            }
            if (ours.getExplosionResistance() != source.getExplosionResistance()) {
                differences.add("blast resistance " + ours.getExplosionResistance() + " vs " + source.getExplosionResistance());
            }
            final String ourXp = experience(ours, xp);
            final String sourceXp = experience(source, xp);
            if (xp != null && !ourXp.equals(sourceXp)) {
                differences.add("experience " + ourXp + " vs " + sourceXp);
            }
            if (!differences.isEmpty()) {
                drifted.add(BuiltInRegistries.BLOCK.getKey(ours).getPath() + " (" + String.join(", ", differences)
                        + " in " + BuiltInRegistries.BLOCK.getKey(source) + ")");
            }
        }
        if (drifted.isEmpty()) {
            Constants.LOG.info("All {} ore variants match the hardness, blast resistance and experience of their source ore",
                    compared);
            return;
        }
        Constants.LOG.warn("{} of {} ore variants differ from their source ore, ours first: {}{}",
                drifted.size(), compared, String.join("; ", drifted.subList(0, Math.min(SHOWN, drifted.size()))),
                drifted.size() > SHOWN ? "; and " + (drifted.size() - SHOWN) + " more" : "");
    }

    /**
     * The experience range as the game prints it ("[3-7]", "2"), "none" for a block that drops none this
     * way. By toString, which UniformInt and ConstantInt override on every band: the accessors were renamed
     * at 26.1 (getMinValue to minInclusive), and Forge 1.20.1 runs on obfuscated names besides.
     */
    private static String experience(Block block, Field xp) {
        if (xp == null || !(block instanceof DropExperienceBlock)) {
            return "none";
        }
        try {
            final String range = String.valueOf(xp.get(block));
            return range.equals("0") || range.equals("[0-0]") ? "none" : range;
        } catch (ReflectiveOperationException | RuntimeException e) {
            return "unreadable";
        }
    }

    private static Field xpField() {
        try {
            for (Field field : DropExperienceBlock.class.getDeclaredFields()) {
                if (field.getType() == IntProvider.class) {
                    field.setAccessible(true);
                    return field;
                }
            }
        } catch (RuntimeException e) {
            Constants.LOG.info("Experience is not compared with the source ores: {}", e.toString());
        }
        return null;
    }
}
