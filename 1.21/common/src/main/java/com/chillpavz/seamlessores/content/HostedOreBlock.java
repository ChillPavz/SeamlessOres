package com.chillpavz.seamlessores.content;

import com.chillpavz.seamlessores.Constants;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.DropExperienceBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockState;

/**
 * An ore in a host stone. Sounds like the stone rather than like the ore it stands in for, as vanilla's
 * deepslate ores sound like deepslate.
 *
 * <p>The sound cannot be baked into the block properties: a host may belong to another mod, which may
 * not have registered yet when we do. So it is read from the stone on use, and falls back to the
 * ore's own sound if the stone does not resolve.
 *
 * <p>An ore that does something of its own while it sits in the world or is mined
 * ({@link OreType#keepsBehaviour()}) hands those calls to the block it stands in for. Mythic Metals'
 * banglum ore can blow up as it is mined, more often in the Nether, with the odds moved by the tool's
 * enchantments and a Mythril Drill's upgrades, and smokes now and then as a warning. Calling that
 * block's own methods keeps every one of those details exactly as the installed version of the mod
 * has them, with no compile-time dependency on it. Those methods only work on the world and position
 * they are given, so they treat this block as their own. The source is resolved on first use, long
 * after every mod has registered; if it cannot be found, or a call into it fails, the variant logs
 * once and carries on as a plain ore.
 */
public class HostedOreBlock extends DropExperienceBlock {

    private final OreVariant variant;
    private volatile Block source;
    private volatile boolean disabled;

    public HostedOreBlock(OreVariant variant, IntProvider xp, Properties properties) {
        super(xp, properties);
        this.variant = variant;
        this.disabled = !variant.ore().keepsBehaviour();
    }

    @Override
    protected SoundType getSoundType(BlockState state) {
        return hostSound(variant.host(), super.getSoundType(state));
    }

    static SoundType hostSound(HostStone host, SoundType fallback) {
        final Block stone = host.block();
        return stone == null ? fallback : stone.defaultBlockState().getSoundType();
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

    /** The block whose behaviour this variant keeps, or null for a plain ore. */
    private Block source() {
        if (disabled) {
            return null;
        }
        Block found = source;
        if (found == null) {
            found = variant.sourceBlock();
            // Never delegate to another variant: that would loop between the two.
            if (found == null || found instanceof HostedOreBlock) {
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
            Constants.LOG.warn("{} does not resolve, so {} behaves as a plain ore", variant.source(), this);
        } else {
            Constants.LOG.error("{} failed when called for {}, which behaves as a plain ore from now on",
                    variant.source(), this, cause);
        }
    }
}
