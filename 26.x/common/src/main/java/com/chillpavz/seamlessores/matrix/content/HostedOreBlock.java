package com.chillpavz.seamlessores.matrix.content;

import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.DropExperienceBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockState;

/**
 * An ore in a modded stone. Sounds like the stone rather than like the vanilla ore.
 *
 * <p>The sound cannot be baked into the block properties the way Seamless Ores does it: the stone
 * belongs to another mod, which may not have registered yet when we do. So it is looked up from the
 * stone on first use instead, and falls back to the vanilla ore's own sound if the stone is absent.
 */
public class HostedOreBlock extends DropExperienceBlock {

    private final HostStone host;

    public HostedOreBlock(HostStone host, IntProvider xp, Properties properties) {
        super(xp, properties);
        this.host = host;
    }

    @Override
    protected SoundType getSoundType(BlockState state) {
        return hostSound(host, super.getSoundType(state));
    }

    static SoundType hostSound(HostStone host, SoundType fallback) {
        final Block stone = host.block();
        return stone == null ? fallback : stone.defaultBlockState().getSoundType();
    }
}
