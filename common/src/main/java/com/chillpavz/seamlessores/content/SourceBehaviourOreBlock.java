package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.Constants;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.RandomSource;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.DropExperienceBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;

/**
 * A variant that hands what its source ore does when mined, and while it sits in the world, to the
 * source block itself.
 *
 * <p>Mythic Metals' banglum ore can blow up as it is mined: more often in the Nether, with the odds
 * moved by the tool's enchantments and a Mythril Drill's upgrades, and it smokes now and then as a
 * warning. Calling that block's own methods keeps every one of those details exactly as the
 * installed version of the mod has them, with no compile-time dependency on it. Those methods only
 * work on the world and position they are given, so they treat this block as their own.
 *
 * <p>The source is resolved on first use, long after every mod has registered. If it cannot be
 * found, or a call into it fails, the variant logs once and carries on as a plain ore.
 */
public class SourceBehaviourOreBlock extends DropExperienceBlock {

    private final ResourceLocation sourceId;
    private volatile Block source;
    private volatile boolean disabled;

    public SourceBehaviourOreBlock(IntProvider xp, BlockBehaviour.Properties properties, ResourceLocation sourceId) {
        super(xp, properties);
        this.sourceId = sourceId;
    }

    @Override
    public BlockState playerWillDestroy(Level level, BlockPos pos, BlockState state, Player player) {
        final Block delegate = source();
        if (delegate != null) {
            try {
                return delegate.playerWillDestroy(level, pos, state, player);
            } catch (RuntimeException | LinkageError e) {
                disable(e);
            }
        }
        return super.playerWillDestroy(level, pos, state, player);
    }

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        final Block delegate = source();
        if (delegate != null) {
            try {
                delegate.animateTick(state, level, pos, random);
                return;
            } catch (RuntimeException | LinkageError e) {
                disable(e);
            }
        }
        super.animateTick(state, level, pos, random);
    }

    private Block source() {
        if (disabled) {
            return null;
        }
        Block found = source;
        if (found == null) {
            found = BuiltInRegistries.BLOCK.getOptional(sourceId).orElse(null);
            // Never delegate to another variant: that would loop between the two.
            if (found == null || found instanceof SourceBehaviourOreBlock) {
                disable(null);
                return null;
            }
            source = found;
        }
        return found;
    }

    private void disable(Throwable cause) {
        if (disabled) {
            return;
        }
        disabled = true;
        if (cause == null) {
            Constants.LOG.warn("{} does not resolve, so {} behaves as a plain ore", sourceId, this);
        } else {
            Constants.LOG.error("{} failed when called for {}, which behaves as a plain ore from now on",
                    sourceId, this, cause);
        }
    }
}
